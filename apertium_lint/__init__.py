#!/usr/bin/env python3

from .file_linter import lint

try:
    from .xml import dix, lrx, modes, transfer
except ImportError:
    print('WARNING: lxml is required to run XML linters')

try:
    from .tree_sitter import cg, lexc, lexd, rtx, twolc
except ImportError:
    print('WARNING: tree-sitter is required to run some linters')

import os
import json
import sys
from collections import defaultdict
import subprocess

def disp_dict(dct, indent=0):
    prefix = '  '*indent
    for k in sorted(dct.keys()):
        blob = dct[k]
        if isinstance(blob['value'], dict):
            print(f'{prefix}{blob["long_name"]}:')
            disp_dict(blob['value'], indent+1)
        else:
            print(f'{prefix}{blob["long_name"]}:\t{blob["value"]}')

def display_results(pth, args, blob):
    if args.json:
        print(json.dumps(pth) + ':' + json.dumps(blob) + ',')
        return
    if ((len(blob['stats']) == 0 or not args.stats) and
        (len(blob['checks']) == 0 or not args.check)):
        return
    print_pth = pth.replace(os.getcwd(), '.')
    if args.linewise:
        if print_pth.count('/') == 1:
            # just use the filename if it's in the top directory
            print_pth = print_pth[2:]
    else:
        print(print_pth)
    if args.check:
        verb_labs = {
            1: 'Error',
            2: 'Warning',
            3: 'Suggestion',
            4: 'Nitpick',
        }
        for msg in blob['checks']:
            typ = verb_labs.get(msg['level'], 'Message')
            if args.linewise:
                print(f'{print_pth}:{msg["line"]}: {typ.lower()}: ({msg["name"]}) {msg["desc"]}')
            else:
                print(f'{typ} ({msg["name"]}) on line {msg["line"]}: {msg["desc"]}')
    if args.stats:
        disp_dict(blob['stats'])

def lint_file(pth, args, totals=None):
    linter = lint(pth, check=args.check, stats=args.stats)
    res = linter.get_results()
    display_results(pth, args, res)
    if totals is not None:
        for ch in res.get('checks', []):
            totals[ch['level']] += 1

def lint_path(pth, args, totals=None):
    if os.path.isfile(pth):
        lint_file(pth, args, totals)
    elif os.path.isdir(pth):
        skip = set()
        if args.ignore:
            # There's probably a safer way to write this call...
            proc = subprocess.run('git check-ignore *',
                                  shell=True, capture_output=True, cwd=pth)
            if proc.returncode == 0:
                skip = set(proc.stdout.decode('utf-8').splitlines())
        for ent in os.scandir(pth):
            if ent.name.startswith('.') or ent.name in skip:
                continue
            if ent.is_file():
                lint_file(ent.path, args, totals)
            elif ent.is_dir():
                lint_path(ent.path, args, totals)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Lint Apertium source files.')
    parser.add_argument('filename', action='store', nargs='*')
    parser.add_argument('--stats', '-s', action='store_true')
    parser.add_argument('--no-check', '-C', action='store_false', dest='check')
    parser.add_argument('--include-ignored', '-I', action='store_false',
                        dest='ignore', help='Also lint files in .gitignore')
    # these should probably be mutually exclusive and go to a format variable
    parser.add_argument('--json', '-j', action='store_true')
    parser.add_argument('--linewise', '--linewize', '-l', action='store_true')
    parser.add_argument('--max-error', action='store', type=int, default=-1,
                        metavar='N', help='Exit with non-zero status if more than N errors found')
    parser.add_argument('--max-warn', action='store', type=int, default=-1,
                        metavar='N', help='Exit with non-zero status if more than N warnings or errors found')
    args = parser.parse_args()
    if args.json:
        print('{')
    count = defaultdict(lambda: 0)
    for fname in args.filename or [os.getcwd()]:
        lint_path(fname, args, count)
    if args.json:
        print('"":{}\n}')
    else:
        print(f'Errors: {count[1]} Warnings: {count[2]} Suggestions: {count[3]} Nitpicks: {count[4]}')
    if args.max_error >= 0 and count[1] > args.max_error:
        sys.exit(1)
    if args.max_warn >= 0 and count[1] + count[2] > args.max_warn:
        sys.exit(1)

if __name__ == '__main__':
    main()
