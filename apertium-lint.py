#!/usr/bin/env python3

import file_linter
import lexd_lint

import os.path
import re
import sys

EXTENSIONS = ['monodix', 'bidix', 'lexc', 'lexd',
              'lsx', 'lrx',
              'Makefile.am', 'modes.xml', 'configure.ac']

BIDIX_NAME = re.compile(r'^apertium-\w+-\w+.\w+-\w+.dix$')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store')
    parser.add_argument('--extension', '-e', choices=['lexd'])
    parser.add_argument('--stats', '-s', action='store_true')
    args = parser.parse_args()
    linter = file_linter.FileLinter.lint(args.filename)
    linter.report()
    if args.stats:
        linter.report_stats()
