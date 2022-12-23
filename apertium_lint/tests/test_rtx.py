#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class InconsistentOperators(unittest.TestCase, LintTestBase):
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
