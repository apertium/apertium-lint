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
    PathIdentifiers = [] # same, but full path
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
            lines = txt.splitlines()
            if txt and not txt.endswith('\n'):
                self.record(len(lines), Verbosity.Error, 'Missing trailing newline.')
            for num, line in enumerate(lines, 1):
                if normalize('NFC', line) != line:
                    self.record(num, Verbosity.Warn, 'Line contains non-normalized characters.')
                if ' ' in line:
                    self.record(num, Verbosity.Warn, 'Line contains non-breaking space.')
    def load(self):
        pass
    def identify(path, extension):
        if extension in FileLinter.Extensions:
            return FileLinter.Extensions[extension]
        filename = os.path.basename(path)
        ext = os.path.splitext(filename)[1].lstrip('.')
        if ext in FileLinter.Extensions:
            return FileLinter.Extensions[ext]
        for r, c in FileLinter.PathIdentifiers:
            if r.search(path):
                return c
        for r, c in FileLinter.Identifiers:
            if r.match(filename):
                return c
        return FileLinter
    def lint(path, extension='', check=True, stats=False):
        cls = FileLinter.identify(path, extension)
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
    def register(cls, ext='', regexs=None, path_regexs=None):
        if ext:
            if isinstance(ext, str):
                FileLinter.Extensions[ext] = cls
            else:
                for e in ext:
                    FileLinter.Extensions[e] = cls
        if regexs:
            for r in regexs:
                FileLinter.Identifiers.append((re.compile(r), cls))
        if path_regexs:
            for r in path_regexs:
                FileLinter.PathIdentifiers.append((re.compile(r), cls))

class SkipLinting(FileLinter):
    def check_encoding(self):
        # override default check
        pass

# skip compiled files
FileLinter.register(SkipLinting,
                    ext=[
                        'bin',
                        'prob',
                        'zhfst',
                        'hfst',
                        'gz',
                        'mode',
                    ],
                    path_regexs=[r'/modes/'])
# skip generated test files
FileLinter.register(SkipLinting,
                    path_regexs=[
                        r'/test/.*-expected\.txt',
                        r'/test/expected/',
                        r'/test/.*-output\.txt',
                        r'/test/output/',
                        r'/test/.*-gold\.txt',
                        r'/test/gold/',
                        r'/test/error\.log$',
                    ])
# skip files generated by the build system
FileLinter.register(SkipLinting,
                    ext=['pc', 'cache', 'm4'],
                    regexs=[
                        r'Makefile$',
                        r'Makefile\.in$',
                        r'INSTALL',
                        r'ap_include\.am',
                        r'config(\.log|\.status)?',
                        r'configure',
                        r'install-sh',
                    ],
                    path_regexs=[
                        r'/autom4te\.cache/'
                    ])
# skip editor save files
FileLinter.register(SkipLinting, regexs=[r'.*~', r'\.DS_Store'])
# skip corpus and dev dirs since there's no standards about what goes in there
FileLinter.register(SkipLinting,
                    path_regexs=[
                        r'/corpus/',
                        r'/texts/',
                        r'/dev/',
                    ])
# let's not try to process scripts
FileLinter.register(SkipLinting, ext=['py', 'sh'])
