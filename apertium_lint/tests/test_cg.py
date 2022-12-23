#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class UndefSet(unittest.TestCase, LintTestBase):
    file_name = 'test.rlx'
    file_contents = '''
SELECT X ;
'''
    expected_class = 'CGLinter'
    expected_checks = [
        (2, 'undef-set'),
    ]
