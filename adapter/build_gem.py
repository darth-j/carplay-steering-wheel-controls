#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
"""Generate a target-specific GEM tree using the operator's local OEM dependencies."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, tempfile, zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def strict_patch(original, patch):
    """Apply exact unified hunks; never guess offsets or accept fuzzy context."""
    old = original.splitlines(keepends=True)
    lines = patch.splitlines(keepends=True)
    if len(lines) < 3 or not lines[0].startswith('--- ') or not lines[1].startswith('+++ '):
        raise ValueError('Invalid patch header')
    result, cursor, i = [], 0, 2
    while i < len(lines):
        match = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n?', lines[i])
        if not match:
            raise ValueError('Invalid hunk header')
        start = max(0, int(match.group(1)) - 1)
        old_count = int(match.group(2) or 1)
        new_count = int(match.group(4) or 1)
        if start < cursor or start > len(old):
            raise ValueError('Hunk outside source')
        result.extend(old[cursor:start]); cursor = start
        consumed = emitted = 0; i += 1
        while i < len(lines) and not lines[i].startswith('@@ '):
            line = lines[i]; prefix, text = line[:1], line[1:]
            if prefix in (' ', '-'):
                if cursor >= len(old) or old[cursor] != text:
                    raise ValueError('Source does not match patch exactly')
                cursor += 1; consumed += 1
            if prefix in (' ', '+'):
                result.append(text); emitted += 1
            if prefix not in (' ', '-', '+'):
                raise ValueError('Unsupported patch line')
            i += 1
        if consumed != old_count or emitted != new_count:
            raise ValueError('Hunk count mismatch')
    result.extend(old[cursor:])
    return ''.join(result)

def safe_relative(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe profile path')
    return path

def check_hash(path, expected, label):
    if digest(path.read_bytes()) != expected:
        raise ValueError(label + ' checksum mismatch; refusing unsupported input')

def build(args):
    profile = json.loads((HERE / 'profile.json').read_text())
    for key in ['lsd_jar', 'jxe_file', 'cfr_jar', 'ecj_jar', 'boot_jar']:
        path = Path(getattr(args, key)).expanduser().resolve()
        if not path.is_file():
            raise ValueError(key + ' must be an existing local file')
        setattr(args, key, path)
    check_hash(args.cfr_jar, profile['cfr_sha256'], 'CFR')
    check_hash(args.ecj_jar, profile['ecj_sha256'], 'ECJ')
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise ValueError('Output already exists; choose a new output directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.controls-build-', dir=output.parent) as tmp:
        work = Path(tmp); raw = work / 'raw'; stock = work / 'stock'; src = work / 'src'; classes = work / 'classes'
        with zipfile.ZipFile(args.lsd_jar) as original_jar:
            for entry in profile['patched_sources']:
                rel = safe_relative(entry['path']); class_name = str(rel.with_suffix('.class'))
                data = original_jar.read(class_name)
                if digest(data) != entry['original_class_sha256']:
                    raise ValueError('OEM class fingerprint mismatch: ' + class_name)
                class_file = raw / class_name; class_file.parent.mkdir(parents=True, exist_ok=True); class_file.write_bytes(data)
                subprocess.run([args.java, '-jar', str(args.cfr_jar), str(class_file), '--extraclasspath', str(args.lsd_jar), '--outputdir', str(stock), '--silent', 'true'], check=True)
                generated = stock / rel
                check_hash(generated, entry['canonical_source_sha256'], 'Canonical decompilation')
                patched = strict_patch(generated.read_text(), (HERE / 'patches' / safe_relative(entry['patch'])).read_text())
                if digest(patched.encode()) != entry['patched_source_sha256']:
                    raise ValueError('Patched source fingerprint mismatch')
                dest = src / rel; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(patched)
        for helper in profile['helpers']:
            rel = safe_relative(helper['path']); text = (HERE / 'src' / rel).read_text()
            marker = '// TARGET-SOURCE-BEGIN\n'
            if text.count(marker) != 1:
                raise ValueError('Helper provenance marker missing')
            text = text.split(marker, 1)[1]
            if digest(text.encode()) != helper['target_source_sha256']:
                raise ValueError('Helper source mismatch')
            dest = src / rel; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(text)
        subprocess.run([args.java, '-jar', str(args.ecj_jar), '-1.4', '-bootclasspath', str(args.boot_jar), '-cp', str(args.lsd_jar), '-d', str(classes)] + [str(p) for p in sorted(src.rglob('*.java'))], check=True)
        actual = {str(p.relative_to(classes)): digest(p.read_bytes()) for p in classes.rglob('*.class')}
        if actual != profile['expected_class_sha256']:
            raise ValueError('Compiled classes differ from reference; no installable package generated')
        for path in classes.rglob('*.class'):
            data = path.read_bytes()
            if data[:4] != b'\xca\xfe\xba\xbe' or int.from_bytes(data[6:8], 'big') > 48:
                raise ValueError('Unsupported target bytecode')
            if any(s in data for s in [b'myAudi.VIN', b'myAudi.IMSI', b'PRIVATE KEY-----']) or re.search(rb'/(?:Users|home)/[A-Za-z0-9_-]+', data):
                raise ValueError('Potential private material in target payload')
        gem = work / 'gem'; shutil.copytree(HERE / 'gem', gem)
        target = gem / 'mod' / 'steering-controls'; jar = target / 'SteeringWheelCarPlayControls.jar'
        with zipfile.ZipFile(jar, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(classes.rglob('*.class')):
                info = zipfile.ZipInfo(str(path.relative_to(classes)), (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
            for name, data in [('META-INF/PROJECT-LICENSE', (ROOT / 'LICENSE').read_bytes()), ('META-INF/ADAPTER-NOTICE.md', (HERE / 'ADAPTER-NOTICE.md').read_bytes())]:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data)
        (target / 'payload.sha1').write_text(hashlib.sha1(jar.read_bytes()).hexdigest() + '\n')
        (target / 'rom.sha1').write_text(hashlib.sha1(args.jxe_file.read_bytes()).hexdigest() + '\n')
        (target / 'action.txt').write_text('install-once\n')
        (gem / 'BUILD.json').write_text(json.dumps({'profile': profile['id'], 'train': profile['train'], 'mu': profile['mu'], 'class_count': len(actual), 'class_payload_matches_reference': True, 'jar_sha256': digest(jar.read_bytes()), 'default_action': 'install-once', 'installer_live_tested': False}, indent=2) + '\n')
        shutil.copyfile(HERE / 'ADAPTER-NOTICE.md', gem / 'ADAPTER-NOTICE.md')
        shutil.copyfile(HERE / 'GEM-INSTALL.md', gem / 'GEM-INSTALL.md')
        shutil.copyfile(ROOT / 'LICENSE', gem / 'PROJECT-LICENSE')
        gem.rename(output)
    print('GEM tree generated: ' + str(output))
    print('Reference classes match. Default: ONE-BOOT TEST; new installer requires hardware validation.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['lsd-jar', 'jxe-file', 'cfr-jar', 'ecj-jar', 'boot-jar']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--java', default='java')
    parser.add_argument('--output', default='dist/gem')
    try:
        build(parser.parse_args())
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as failure:
        raise SystemExit('STOP: ' + str(failure))
