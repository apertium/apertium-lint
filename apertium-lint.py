#!/usr/bin/env python3

from linters import file_linter

try:
    import linters.xml.dix
    import linters.xml.lrx
    import linters.xml.transfer
except ImportError:
    print('WARNING: lxml is required to run XML linters')

try:
    import linters.tree_sitter.cg
    import linters.tree_sitter.lexc
    import linters.tree_sitter.lexd
    import linters.tree_sitter.rtx
    import linters.tree_sitter.twolc
except ImportError:
    print('WARNING: tree-sitter is required to run some linters')

import os

def lint_file(pth, args, out_json):
    linter = file_linter.FileLinter.lint(pth, check=args.check, stats=args.stats)
    if args.check:
        linter.report()
    if args.stats:
        linter.report_stats()

def lint_path(pth, args, out_json):
    if os.path.isfile(pth):
        lint_file(pth, args, out_json)
    elif os.path.isdir(pth):
        for ent in os.scandir(pth):
            if ent.name.startswith('.'):
                continue
            if ent.is_file():
                lint_file(ent.path, args, out_json)
            elif ent.is_dir():
                lint_path(ent.path, args, out_json)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store', nargs='*')
    parser.add_argument('--stats', '-s', action='store_true')
    parser.add_argument('--no-check', '-C', action='store_false', dest='check')
    args = parser.parse_args()
    out_json = {}
    for fname in args.filename or [os.getcwd()]:
        lint_path(fname, args, out_json)
