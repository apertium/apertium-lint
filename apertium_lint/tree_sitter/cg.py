#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class CGLinter(TreeSitterLinter):
    language = TSA.CG
    Extensions = ['rlx']
    StatLabels = {
        'rules': 'Rules',
    }
    ReportTypes = {
        'redef-set': (Verbosity.Error, 'Redefinition of set {0}.'),
        'undef-set': (Verbosity.Error, 'Set {0} used but not defined.'),
        'unuse-set': (Verbosity.Warn, 'Set {0} defined but not used.'),
    }
    def stat_rules(self):
        self.record_stat('rules',
                         sum(1 for n in self.tree.children
                             if n.type.startswith('rule')))
    def check_setnames(self):
        qr = '[(set name: (setname) @n) (list name: (setname) @n)]'
        sdef = self.gather_lines(qr, 'redef-set')
        qr = '[(inlineset_single (setname) @n) (setname_t) @n]'
        suse = self.gather_lines(qr)
        magic_sets = ['_S_DELIMITERS_', '_S_SOFT_DELIMITERS_']
        for k in magic_sets:
            if k in suse:
                del suse[k]
        self.warn_def_use(sdef, suse, 'unuse-set')
        self.warn_def_use(suse, sdef, 'undef-set')
