#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class EmptyLeft(unittest.TestCase, LintTestBase):
    file_name = 'test.lexc'
    file_contents = '''
LEXICON Root
Q ;

LEXICON Q
:x Z ;

LEXICON Z
:q # ;
a:b # ;
z # ;
'''
    expected_class = 'LexCLinter'
    expected_checks = [
        (1, 'left-empty'),
    ]
