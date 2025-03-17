#!/usr/bin/env python3

from collections import defaultdict
import inspect
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

    # short label : (level, format str)
    ReportTypes = {
        'noNL': (Verbosity.Error, 'Missing trailing newline.'),
        'unnorm': (Verbosity.Warn, 'Line contains non-normalized characters.'),
        'NBSP': (Verbosity.Warn, 'Line contains non-breaking space.'),
        'undef': (Verbosity.Error, '{0} {1} used but not defined.'),
        'unuse': (Verbosity.Warn, '{0} {1} defined but not used.'),
    }
    StatLabels = {} # short label : full label

    RunStat = []
    RunCheck = []
    RunStatCheck = []
    RunPer = {}

    def __init__(self, path):
        self.path = path
        self.reports = [] # (line, level, key, text)
        self.statistics = defaultdict(lambda: 0)
    def __init_subclass__(cls, *args, **kwargs):
        super.__init_subclass__(*args, **kwargs)
        stat_methods = []
        check_methods = []
        per_methods = defaultdict(lambda: [[], [], []])
        for name, fn in inspect.getmembers(cls):
            if not callable(fn):
                continue
            if name.startswith('stat_'):
                stat_methods.append(name)
            elif name.startswith('check_'):
                check_methods.append(name)
            elif name.startswith('statcheck_'):
                stat_methods.append(name)
                check_methods.append(name)
            elif name.startswith('pre_'):
                method_name = name.split('__')[0].split('_', 1)[1]
                per_methods[method_name][0].append(name)
            elif name.startswith('per_'):
                method_name = name.split('__')[0].split('_', 1)[1]
                per_methods[method_name][1].append(name)
            elif name.startswith('post_'):
                method_name = name.split('__')[0].split('_', 1)[1]
                per_methods[method_name][2].append(name)
        if per_methods:
            stat_methods.append('run_per')
            check_methods.append('run_per')
        def nsort(ls):
            return sorted(set(ls), key=lambda x: x.split('_', 1)[1])
        cls.RunStat = nsort(stat_methods)
        cls.RunCheck = nsort(check_methods)
        cls.RunStatCheck = nsort(check_methods + stat_methods)
        cls.RunPer = {k:list(map(sorted, v))
                      for k, v in per_methods.items()}
        if isinstance(cls.Extensions, list):
            for e in cls.Extensions:
                FileLinter.Extensions[e] = cls
        for i in cls.Identifiers:
            if isinstance(i, str):
                FileLinter.Identifiers.append((re.compile(i), cls))
        for pi in cls.PathIdentifiers:
            if isinstance(pi, str):
                FileLinter.PathIdentifiers.append((re.compile(pi), cls))
    def load(self):
        return True
    def _get_report_label(self, label):
        for cls in self.__class__.__mro__:
            if label in cls.ReportTypes:
                return cls.ReportTypes[label]
        raise KeyError(f'Report type "{label}" is not defined.')
    def record(self, key, line, *args):
        level, fs = self._get_report_label(key)
        self.reports.append((line, level, key, fs.format(*args)))
    def _get_stat_label(self, label, default):
        for cls in self.__class__.__mro__:
            if not hasattr(cls, 'StatLabels'):
                continue
            if label in cls.StatLabels:
                return cls.StatLabels[label]
            elif len(label) == 1 and label[0] in cls.StatLabels:
                return cls.StatLabels[label[0]]
        return default
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
    def __process_stats(self, dct, pth=None):
        ret = {}
        for k, v in dct.items():
            key = tuple((pth or []) + [k])
            val = v
            if isinstance(v, dict):
                val = self.__process_stats(v, list(key))
            sd = {
                'name': k,
                'long_name': self._get_stat_label(key, k),
                'value': val
            }
            ret[k] = sd
        return ret
    def get_results(self):
        rep = []
        for line, level, key, desc in sorted(self.reports):
            rep.append({
                'line': line,
                'level': level,
                'name': key,
                'desc': desc,
            })
        return {'stats': self.__process_stats(self.statistics), 'checks': rep}

    def __call_all(self, ls, *args):
        for a in ls:
            getattr(self, a).__call__(*args)
    def iter_type(self, name):
        pass
    def run_per(self):
        for k in sorted(self.RunPer.keys()):
            pre, per, post = self.RunPer[k]
            self.__call_all(pre)
            for node in self.iter_type(k):
                self.__call_all(per, node)
            self.__call_all(post)
    def run_stat(self):
        self.__call_all(self.RunStat)
    def run_check(self):
        self.__call_all(self.RunCheck)
    def run_statcheck(self):
        self.__call_all(self.RunStatCheck)
    def check_encoding(self):
        with open(self.path, 'rb') as fin:
            try:
                txt = fin.read().decode('utf-8')
            except UnicodeDecodeError:
                return
            lines = txt.splitlines()
            if txt and not txt.endswith('\n'):
                self.record('noNL', len(lines))
            for num, line in enumerate(lines, 1):
                if normalize('NFC', line) != line:
                    self.record('unnorm', num)
                if ' ' in line:
                    self.record('NBSP', num)
    def warn_def_use(self, check_dict, ref_dict, err):
        '''
        Given check_dict of the form {label:line} or {label:[line1, line2]}
        and ref_dict of the same form, call
        self.record(err, line, label) for every label not in ref_dict
        '''
        for lab, lines in check_dict.items():
            if lab not in ref_dict:
                ls = lines
                if not isinstance(ls, list):
                    ls = [ls]
                for ln in ls:
                    self.record(err, ln, lab)

class SkipLinting(FileLinter):
    Extensions = [
        'bin', 'prob', 'zhfst', 'hfst', 'gz', 'mode', # compiled files
        'pc', 'cache', 'm4', # build system
        'py', 'sh', # scripts
    ]
    Identifiers = [
        # build system
        r'Makefile(\.in)?$',
        r'INSTALL',
        r'ap_include\.am',
        r'config(\.log|\.status)?',
        r'configure',
        r'install-sh',
        # editor save files
        r'.*~', r'\.DS_Store',
    ]
    PathIdentifiers = [
        r'(/|^)modes/',
        r'(/|^)autom4te\.cache/',
        # generated test files
        r'(/|^)test/(expected|output|gold)/',
        r'(/|^)test/.*-(expected|output|gold)\.txt$',
        r'(/|^)test/error\.log$',
        # non-standardized subdirs
        r'(/|^)(corpus|texts|dev)/',
    ]
    def load(self):
        return False

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
    cls = identify(path, extension)
    ret = cls(path)
    loaded = ret.load()
    if not loaded:
        return ret
    if check and stats:
        ret.run_statcheck()
    elif check:
        ret.run_check()
    elif stats:
        ret.run_stat()
    return ret
