#!/usr/bin/env python3

from tree_sitter import Language, Parser
import argparse
import lexd_lint
import sys, os.path

Language.build_library(
    'build/langs.so',
    [
        'tree-sitter-apertium/tree-sitter-lexd',
        'tree-sitter-apertium/tree-sitter-cg',
        'tree-sitter-apertium/tree-sitter-twolc',
        'tree-sitter-apertium/tree-sitter-rtx'
    ]
)

LEXD_LANGUAGE = Language('build/langs.so', 'lexd')
#CG_LANGUAGE = Language('build/langs.so', 'cg')
#TWOLC_LANGUAGE = Language('build/langs.so', 'twolc')
#RTX_LANGUAGE = Language('build/langs.so', 'rtx')

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
