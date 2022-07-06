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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store')
    parser.add_argument('--stats', '-s', action='store_true')
    parser.add_argument('--no-check', '-C', action='store_false', dest='check')
    args = parser.parse_args()
    linter = file_linter.FileLinter.lint(args.filename,
                                         check=args.check,
                                         stats=args.stats)
    if args.check:
        linter.report()
    if args.stats:
        linter.report_stats()
