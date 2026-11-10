# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
import hashlib, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
STOCK = b'''#!/bin/sh
# Synthetic startup fixture, not an OEM file.
VMOPTIONS=-Dsynthetic=true
BOOTCLASSPATH=/ifs/synthetic.jxe
on -p 12 /ifs/jre/bin/j9 $VMOPTIONS -Xbootclasspath:$BOOTCLASSPATH -jxe:$LSD_DIR/lsd.jxe &
'''

def sha(data):
    return hashlib.sha1(data).hexdigest()

class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.sd = self.root / 'sd'; self.app = self.root / 'app'; self.ram = self.root / 'ram'; self.bin = self.root / 'bin'
        self.ram.mkdir(); self.bin.mkdir(); self.trace = self.root / 'java-args'
        shutil.copytree(ADAPTER / 'gem/mod', self.sd / 'mod')
        self.pkg = self.sd / 'mod/steering-controls'
        (self.sd / 'apps/sbin').mkdir(parents=True)
        (self.sd / 'apps/sbin/sed').symlink_to(shutil.which('sed'))
        self.executable(self.sd / 'apps/sbin/pc', '#!/bin/sh\nexit 0\n')
        self.base = self.app / 'eso/hmi/lsd'; (self.base / 'jars').mkdir(parents=True)
        self.lsd = self.base / 'lsd.sh'; self.lsd.write_bytes(STOCK)
        self.jar = self.base / 'jars/SteeringWheelCarPlayControls.jar'
        self.payload = b'SYNTHETIC PAYLOAD ONLY; NEVER INSTALL THIS TEST FIXTURE'
        (self.pkg / 'SteeringWheelCarPlayControls.jar').write_bytes(self.payload)
        (self.pkg / 'payload.sha1').write_text(sha(self.payload) + '\n')
        self.action('install-once')
        self.rom = self.root / 'rom/lsd.jxe'; self.rom.parent.mkdir(); self.rom.write_bytes(b'SYNTHETIC ROM FIXTURE')
        (self.pkg / 'rom.sha1').write_text(sha(self.rom.read_bytes()) + '\n')
        self.marker = self.root / 'rcc-marker'; self.executable(self.marker, '#!/bin/sh\nexit 0\n')
        self.executable(self.bin / 'sha1sum', '#!' + sys.executable + '\nimport hashlib,os,sys\nif os.environ.get("FAIL_DIGEST")=="1":sys.exit(1)\nprint(hashlib.sha1(open(sys.argv[1],"rb").read()).hexdigest()+"  "+sys.argv[1])\n')
        self.executable(self.bin / 'mount', '#!/bin/sh\nexit 0\n')
        self.executable(self.bin / 'sync', '#!/bin/sh\nexit 0\n')
        self.executable(self.bin / 'on', '''#!/bin/sh
if [ "$2" = rcc ]; then shift 2; exec "$@"; fi
case "$4" in
s:30:1966084) echo "${TEST_TRAIN:-MHI2_CN_AU57x_K1006_2}";;
s:30:1966083) echo 1005;;
*) exit 1;;
esac
''')
        self.executable(self.bin / 'cp', '''#!/bin/sh
case "$*" in *SteeringWheelCarPlayControls.jar.sww-new-*) [ "$FAIL_JAR_COPY" = 1 ] && exit 1;; esac
exec REAL_CP "$@"
'''.replace('REAL_CP', shutil.which('cp')))
        self.executable(self.bin / 'mv', '''#!/bin/sh
case "$*" in
*lsd.sh.sww-new-*)
 if [ "$FAIL_STARTUP_COMMIT" = 1 ] && [ ! -f "$TEST_ROOT/mv-failed-once" ]; then
  : > "$TEST_ROOT/mv-failed-once"; exit 1
 fi;;
esac
exec REAL_MV "$@"
'''.replace('REAL_MV', shutil.which('mv')))
        self.script = self.pkg / 'manage.sh'
        self.script.write_text(self.translate(self.script.read_text()).replace('export PATH=', 'export PATH=' + str(self.bin) + ':', 1))

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def executable(path, text):
        path.write_text(text); path.chmod(0o755)

    def translate(self, text):
        return text.replace('/net/mmx/fs/sda0', str(self.sd)).replace('/net/mmx/fs/sdb0', str(self.root / 'sd2')).replace('/net/mmx/mnt/app', str(self.app)).replace('/net/rcc/dev/shmem', str(self.ram)).replace('/net/rcc/usr/bin/sha1sum', str(self.bin / 'sha1sum')).replace('/usr/apps/mib2_ioc_flash', str(self.marker)).replace('/net/mmx/ifs/lsd.jxe', str(self.rom))

    def action(self, value):
        (self.pkg / 'action.txt').write_text(value + '\n')

    def run_manager(self, **extra):
        env = dict(os.environ, TEST_ROOT=str(self.root), **extra)
        return subprocess.run(['/bin/sh', str(self.script), str(self.sd)], env=env, capture_output=True, text=True)

    def install(self, mode='install-once'):
        self.action(mode); result = self.run_manager()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('INSTALL VERIFIED', result.stdout)

    def run_boot(self, block, fail_digest=False):
        code = self.translate(block).replace('/mnt/app', str(self.app)).replace('/eso/hmi/lsd/jars', str(self.base / 'jars')).replace('/dev/shmem', str(self.ram))
        pre = '''mount() { return 0; }
sync() { return 0; }
on() {
 if [ "$2" = rcc ]; then shift 2; "$@"; else echo "$*" > "$TRACE_FILE"; fi
}
'''
        script = self.root / 'boot.sh'; script.write_text(pre + code + '\nwait\n')
        result = subprocess.run(['/bin/sh', str(script)], env=dict(os.environ, TRACE_FILE=str(self.trace), FAIL_DIGEST='1' if fail_digest else '0'), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.trace.read_text()

    def test_one_boot_restores_then_loads_and_second_boot_is_stock(self):
        self.install(); self.assertEqual(self.jar.read_bytes(), self.payload)
        self.assertEqual((self.base / 'lsd.sh.sww-original').read_bytes(), STOCK)
        args = self.run_boot((self.pkg / 'once.block').read_text())
        self.assertIn('-Xbootclasspath/p:', args); self.assertEqual(self.lsd.read_bytes(), STOCK)
        args = self.run_boot(STOCK.decode()); self.assertNotIn('-Xbootclasspath/p:', args)

    def test_permanent_after_trial_and_uninstall(self):
        self.install(); self.run_boot((self.pkg / 'once.block').read_text())
        self.install('install-permanent'); permanent = self.lsd.read_bytes()
        for unused in range(2):
            self.assertIn('-Xbootclasspath/p:', self.run_boot((self.pkg / 'permanent.block').read_text()))
            self.assertEqual(self.lsd.read_bytes(), permanent)
        (self.base / 'sww-controls.disabled').touch()
        self.assertNotIn('-Xbootclasspath/p:', self.run_boot((self.pkg / 'permanent.block').read_text()))
        self.action('uninstall'); result = self.run_manager(); self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('UNINSTALL VERIFIED', result.stdout); self.assertEqual(self.lsd.read_bytes(), STOCK)
        self.assertFalse(self.jar.exists()); self.assertTrue((self.base / 'lsd.sh.sww-original').exists())

    def test_unsupported_firmware_does_not_write(self):
        result = self.run_manager(TEST_TRAIN='UNSUPPORTED_TEST_TRAIN')
        self.assertNotEqual(result.returncode, 0); self.assertEqual(self.lsd.read_bytes(), STOCK)
        self.assertFalse((self.base / 'lsd.sh.sww-original').exists())

    def test_wrong_rom_does_not_write(self):
        self.rom.write_bytes(b'DIFFERENT SYNTHETIC ROM')
        result = self.run_manager(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), STOCK); self.assertFalse(self.jar.exists())

    def test_foreign_loader_refused(self):
        data = STOCK + b'# foreign -Xbootclasspath/p:other.jar\n'; self.lsd.write_bytes(data)
        result = self.run_manager(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), data); self.assertFalse(self.jar.exists())

    def test_payload_corruption_refused(self):
        (self.pkg / 'SteeringWheelCarPlayControls.jar').write_bytes(b'corrupt')
        result = self.run_manager(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), STOCK); self.assertFalse(self.jar.exists())

    def test_failed_jar_staging_leaves_startup_unchanged(self):
        result = self.run_manager(FAIL_JAR_COPY='1'); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), STOCK); self.assertFalse(self.jar.exists())
        self.assertFalse(list(self.ram.iterdir()))

    def test_failed_startup_publish_rolls_back(self):
        result = self.run_manager(FAIL_STARTUP_COMMIT='1'); self.assertNotEqual(result.returncode, 0)
        self.assertIn('RESTORE VERIFIED', result.stdout); self.assertEqual(self.lsd.read_bytes(), STOCK)
        self.assertFalse(self.jar.exists())

    def test_corrupted_original_backup_blocks_uninstall(self):
        self.install(); current = self.lsd.read_bytes()
        (self.base / 'lsd.sh.sww-original').write_bytes(b'corrupt'); self.action('uninstall')
        result = self.run_manager(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), current)

    def test_unmanaged_edit_blocks_mode_change(self):
        self.install(); current = self.lsd.read_bytes() + b'# unrelated change\n'; self.lsd.write_bytes(current)
        self.action('install-permanent'); result = self.run_manager(); self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.lsd.read_bytes(), current)

    def test_duplicate_install_preserves_backup(self):
        self.install(); current = self.lsd.read_bytes()
        result = self.run_manager(); self.assertEqual(result.returncode, 0); self.assertIn('ALREADY INSTALLED', result.stdout)
        self.assertEqual(self.lsd.read_bytes(), current); self.assertEqual((self.base / 'lsd.sh.sww-original').read_bytes(), STOCK)

    def test_boot_hash_failure_does_not_load_overlay(self):
        self.install(); args = self.run_boot((self.pkg / 'once.block').read_text(), fail_digest=True)
        self.assertNotIn('-Xbootclasspath/p:', args)

if __name__ == '__main__':
    unittest.main()
