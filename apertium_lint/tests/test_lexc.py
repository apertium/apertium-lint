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
a:x Z ; ! Use/MT
a:n Z ; ! Use/MT
b:q Z ;

LEXICON Z
:q # ;
a:b # ;
z # ;
'''
    expected_class = 'LexCLinter'
    expected_checks = [
        (1, 'left-empty'),
    ]
    stats = True
    expected_stats = {
        'entries': {
            'long_name': 'entries',
            'name': 'entries',
            'value': {
                'Q': {'long_name': 'Q', 'name': 'Q', 'value': 4},
                'Root': {'long_name': 'Root', 'name': 'Root', 'value': 1},
                'Z': {'long_name': 'Z', 'name': 'Z', 'value': 3},
            },
        },
        'stem_cont': {
            'long_name': 'stem_cont',
            'name': 'stem_cont',
            'value': 3,
        },
        'stem_cont_vanilla': {
            'long_name': 'stem_cont_vanilla',
            'name': 'stem_cont_vanilla',
            'value': 2,
        },
        'stem_gloss': {
            'long_name': 'stem_gloss',
            'name': 'stem_gloss',
            'value': 3,
        },
        'stem_gloss_vanilla': {
            'long_name': 'stem_gloss_vanilla',
            'name': 'stem_gloss_vanilla',
            'value': 2,
        },
        'total_entries': {
            'long_name': 'total_entries',
            'name': 'total_entries',
            'value': 8,
        },
    }

class Multichar(unittest.TestCase, LintTestBase):
    file_name = 'test.lexc'
    file_contents = '''
Multichar_Symbols
%{a%}
%{b%}
%<c%>
%{a%}

LEXICON Root
%<c%>%<d%>:a% %{d%} # ;
'''
    expected_class = 'LexCLinter'
    expected_checks = [
        (6, 'multichar-redef'),
        (9, 'undef-archi'),
        (9, 'undef-tag'),
    ]
