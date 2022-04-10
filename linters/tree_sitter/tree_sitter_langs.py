#!/usr/bin/env python3

import os.path
from tree_sitter import Language, Parser

PATH = os.path.dirname(__file__) + '/'

Language.build_library(
    PATH+'build/langs.so',
    [
        PATH+'tree-sitter-apertium/tree-sitter-lexd',
        PATH+'tree-sitter-apertium/tree-sitter-cg',
        PATH+'tree-sitter-apertium/tree-sitter-twolc',
        PATH+'tree-sitter-apertium/tree-sitter-rtx',
        PATH+'tree-sitter-apertium/tree-sitter-lexc'
    ]
)

LEXD_LANGUAGE = Language(PATH+'build/langs.so', 'lexd')
CG_LANGUAGE = Language(PATH+'build/langs.so', 'cg')
TWOLC_LANGUAGE = Language(PATH+'build/langs.so', 'twolc')
RTX_LANGUAGE = Language(PATH+'build/langs.so', 'rtx')
LEXC_LANGUAGE = Language(PATH+'build/langs.so', 'lexc')
