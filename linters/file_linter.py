#!/usr/bin/env python3

from collections import defaultdict
import os.path
import re
from unicodedata import normalize

class Verbosity:
    Error = 1
    Warn = 2
    Suggestion = 3
    Nitpick = 4

class FileLinter:
    Extensions = {} # str:class
    Identifiers = [] # (regex, class)
    def __init__(self, path):
        self.path = path
        self.reports = [] # (line, level, text)
        self.statistics = defaultdict(lambda: 0)
        self.stat_labels = {}
    def record(self, line, level, text):
        self.reports.append((line, level, text))
    def get_stat(self, key):
        if isinstance(key, str):
            return self.statistics[key]
        else:
            dct = self.statistics
            for k in key:
                if k in dct:
                    dct = dct[k]
                else:
                    return 0
            return dct
    def set_stat(self, key, val):
        if isinstance(key, str):
            self.statistics[key] = val
        else:
            dct = self.statistics
            for i, k in enumerate(key):
                if i == len(key) - 1:
                    dct[k] = val
                elif k in dct:
                    dct = dct[k]
                else:
                    dct[k] = defaultdict(lambda: 0)
                    dct = dct[k]
    def record_stat(self, key, val=None, inc=None):
        cur = self.get_stat(key)
        if val != None:
            cur = val
        elif inc != None:
            cur += inc
        self.set_stat(key, cur)
    def report(self, verbosity=Verbosity.Warn, color=False):
        for line, level, text in self.reports:
            if level <= verbosity:
                print(f'{self.path} Line {line}')
                print(text)
    def report_stats(self, color=False):
        def disp_dict(dct, prefix):
            ind = '  '*len(prefix)
            for k in sorted(dct.keys()):
                name = k
                sk = tuple(prefix + [k]) if prefix else k
                if sk in self.__class__.stat_labels:
                    name = self.__class__.stat_labels[sk]
                if isinstance(dct[k], int):
                    print(f'{ind}{name}:\t{dct[k]}')
                else:
                    print(f'{ind}{name}:')
                    disp_dict(dct[k], prefix + [k])
        disp_dict(self.statistics, [])
    def check_encoding(self):
        with open(self.path, 'rb') as fin:
            try:
                txt = fin.read().decode('utf-8')
            except UnicodeDecodeError:
                return
            for num, line in enumerate(txt.splitlines(), 1):
                if normalize('NFC', line) != line:
                    self.record(num, Verbosity.Warn, 'Line contains non-normalized characters.')
                if ' ' in line:
                    self.record(num, Verbosity.Warn, 'Line contains non-breaking space.')
    def load(self):
        pass
    def lint(path, extension='', check=True, stats=False):
        cls = FileLinter
        if extension in FileLinter.Extensions:
            cls = FileLinter.Extensions[extension]
        else:
            filename = os.path.basename(path)
            ext = os.path.splitext(filename)[1].lstrip('.')
            if ext in FileLinter.Extensions:
                cls = FileLinter.Extensions[ext]
            else:
                for r, c in FileLinter.Identifiers:
                    if r.match(filename):
                        cls = c
                        break
        ret = cls(path)
        ret.load()
        prefixes = []
        if check:
            prefixes += ['check_', 'statcheck_']
        if stats:
            prefixes += ['stat_', 'statcheck_']
        prefixes = sorted(set(prefixes))
        for attr in dir(ret):
            if any(attr.startswith(p) for p in prefixes):
                if callable(getattr(ret, attr)):
                    getattr(ret, attr).__call__()
        return ret
    def register(cls, ext='', regexs=[]):
        if ext:
            FileLinter.Extensions[ext] = cls
        if regexs:
            for r in regexs:
                FileLinter.Identifiers.append((re.compile(r), cls))
