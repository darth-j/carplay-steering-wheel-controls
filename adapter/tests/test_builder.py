# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Skywalker (darth-j)
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_gem import strict_patch, safe_relative

class BuilderTest(unittest.TestCase):
    def test_exact_patch(self):
        original = 'alpha\nbeta\ngamma\n'
        patch = '--- a/test\n+++ b/test\n@@ -1,3 +1,3 @@\n alpha\n-beta\n+replacement\n gamma\n'
        self.assertEqual(strict_patch(original, patch), 'alpha\nreplacement\ngamma\n')
        with self.assertRaises(ValueError):
            strict_patch('changed\nbeta\ngamma\n', patch)

    def test_no_fuzzy_or_path_escape(self):
        with self.assertRaises(ValueError):
            strict_patch('hello\n', '--- a/x\n+++ b/x\n@@ -1,2 +1,1 @@\n hello\n')
        for path in ['../dependency.jar', '/private-input.jar']:
            with self.assertRaises(ValueError):
                safe_relative(path)

if __name__ == '__main__':
    unittest.main()
