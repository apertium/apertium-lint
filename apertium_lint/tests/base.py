#!/usr/bin/env python3

import shutil
import tempfile
import os
from .. import lint

class TempDir:
    def __enter__(self):
        self.tmpd = tempfile.mkdtemp()
        return self.tmpd
    def __exit__(self, *args):
        shutil.rmtree(self.tmpd)

class LintTestBase:
    file_name = 'test.lexd'
    file_contents = '''
PATTERNS
X: :X
'''
    expected_class = 'LexdLinter'
    expected_checks = [
        (3, 'adj-tok-merge'),
    ]
    expected_stats = {
    }
    stats = False
    check = True

    def runTest(self):
        with TempDir() as tmpd:
            pth = os.path.join(tmpd, self.file_name)
            with open(pth, 'w') as fout:
                fout.write(self.file_contents)
            linter = lint(pth, check=self.check, stats=self.stats)
            blob = linter.get_results()
            self.assertEqual(self.expected_class, linter.__class__.__name__)
            if self.stats or self.expected_stats:
                self.assertEqual(self.expected_stats, blob['stats'])
            if self.check or self.expected_checks:
                output = [(out['line'], out['name']) for out in blob['checks']]
                for exp in self.expected_checks:
                    self.assertIn(
                        exp, output,
                        'Check on line %s of type %s not returned' % exp
                    )
                for out in output:
                    self.assertIn(
                        out, self.expected_checks,
                        'Unexpected check returned on line %s of type %s' % out
                    )
