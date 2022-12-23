#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class MergeableTokens(unittest.TestCase, LintTestBase):
    file_name = 'test.lexd'
    file_contents = '''
PATTERNS
X: :X
'''
    expected_class = 'LexdLinter'
    expected_checks = [
        (3, 'adj-tok-merge'),
    ]
