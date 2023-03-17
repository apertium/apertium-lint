#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class NewMatchedPairs(unittest.TestCase, LintTestBase):
    file_name = 'test.twol'
    file_contents = '''
Alphabet
a b c
;

Rules
"blah"
X:Y <=> _ ;
  where X in ( a b )
        Y in ( b c )
  matched ;
'''
    expected_class = 'TwolCLinter'
    expected_checks = [
        (8, 'undef-pair'), (8, 'undef-pair'),
    ]
