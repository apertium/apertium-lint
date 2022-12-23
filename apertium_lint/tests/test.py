#!/usr/bin/env python3

import unittest
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

class LintTest(unittest.TestCase):
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
                self.assertEqual(len(self.expected_checks),
                                 len(blob['checks']),
                                 'wrong number of checks reported')
                for exp, out in zip(self.expected_checks, blob['checks']):
                    self.assertEqual(exp[0], out['line'])
                    self.assertEqual(exp[1], out['name'])

class CGUndefSet(LintTest):
    file_name = 'test.rlx'
    file_contents = '''
SELECT X ;
'''
    expected_class = 'CGLinter'
    expected_checks = [
        (2, 'undef-set'),
    ]

class ModesInstallDeps(LintTest):
    file_name = 'modes.xml'
    file_contents = '''
<modes>
  <mode name="blah" install="yes">
    <pipeline>
      <program name="lt-proc">
        <file name=".deps/eng.automorf.bin"/>
      </program>
    </pipeline>
  </mode>
</modes>
'''
    expected_class = 'ModesLinter'
    expected_checks = [
        (6, 'install-deps')
    ]

class RTXInconsistentOperators(LintTest):
    file_name = 'test.rtx'
    file_contents = '''
number = sg pl;
NP: _ ;
num: _ ;
NP -> num [$number=(if (1.lem equal-cl one) sg else pl)]
      { 1[number=(if ($lem equal_CASE_LESS one) sg else pl)] } ;
'''
    expected_class = 'RTXLinter'
    expected_checks = [
        (6, 'inconsistent-operator')
    ]
