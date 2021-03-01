#!/usr/bin/env python3

from tree_sitter import Language, Parser
import argparse
import lexd_lint
import sys, os.path

PATH = os.path.dirname(__file__) + '/'

Language.build_library(
    PATH+'build/langs.so',
    [
        PATH+'tree-sitter-apertium/tree-sitter-lexd',
        PATH+'tree-sitter-apertium/tree-sitter-cg',
        PATH+'tree-sitter-apertium/tree-sitter-twolc',
        PATH+'tree-sitter-apertium/tree-sitter-rtx'
    ]
)

LEXD_LANGUAGE = Language(PATH+'build/langs.so', 'lexd')
#CG_LANGUAGE = Language(PATH+'build/langs.so', 'cg')
#TWOLC_LANGUAGE = Language(PATH+'build/langs.so', 'twolc')
#RTX_LANGUAGE = Language(PATH+'build/langs.so', 'rtx')

def lint(filename, extension=''):
    ext = extension
    if len(ext) == 0:
        ext = os.path.splitext(filename)[1]
    elif ext[0] != '.':
        ext = '.' + ext
    if ext == '.lexd':
        lexd_lint.lint(filename, LEXD_LANGUAGE)
    else:
        print('Unable to identify filetype.')
        print('Please specify an extension.')
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store')
    parser.add_argument('--extension', '-e', choices=['lexd'])
    args = parser.parse_args()
    lint(args.filename, args.extension or '')
