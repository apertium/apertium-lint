#!/usr/bin/env python3

import file_linter

import lexd_lint
import dix_lint

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store')
    parser.add_argument('--stats', '-s', action='store_true')
    args = parser.parse_args()
    linter = file_linter.FileLinter.lint(args.filename)
    linter.report()
    if args.stats:
        linter.report_stats()
