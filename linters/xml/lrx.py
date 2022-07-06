#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class LRXLinter(XmlLinter):
    stat_labels = {}
    def check_macro_params(self, node=None, in_mac=False):
        if node == None:
            node = self.tree
        if node.tag == 'def-macro':
            any_mac = False
            for ch in node:
                any_mac = self.check_macro_params(ch, True) or any_mac
            return any_mac
        else:
            any_mac = False
            for attr in node.keys():
                if attr.startswith('p'):
                    any_mac = True
                    if not in_mac:
                        self.record(node.sourceline, Verbosity.Error, f'Parameterized attribute {attr} cannot be used outside of <def-macro>.')
                    if attr[1:] in node.keys():
                        self.record(node.sourceline, Verbosity.Error, f'<{node.tag} cannot have both parameterized {attr} and non-parameterized {attr[1:]}.')
            if node.tag == 'param':
                any_mac = True
                if not in_mac:
                    self.record(node.sourceline, Verbosity.Error, f'Cannot inject parameter outside of <def-macro>.')
            for ch in node:
                any_mac = self.check_macro_params(ch, in_mac) or any_mac
            if node.tag == 'rule' and in_mac and not any_mac:
                self.record(node.sourceline, Verbosity.Warn, 'Rule does not use any parameters so there is no need for it to be inside <def-macro>.')
            return any_mac
    def check_repeat(self):
        for node in self.tree.findall('.//repeat'):
            att = node.keys()
            if 'from' not in att and 'pfrom' not in att:
                self.record(node.sourceline, Verbosity.Error, '<repeat> must have value for attribute from.')
            if 'upto' not in att and 'pupto' not in att:
                self.record(node.sourceline, Verbosity.Error, '<repeat> must have value for attribute upto.')
    def check_seqs(self):
        seq_def = {}
        for node in self.tree.findall('.//def-seq'):
            if len(node) > 5:
                self.record(node.sourceline, Verbosity.Suggestion, 'Sequence has more than 5 elements - did you forget an <or>?')
            name = node.get('n', '')
            if name in seq_def:
                self.record(node.sourceline, Verbosity.Error, 'Redefinition of sequence {name} (initial definition on line {seq_def[name]}.')
            else:
                seq_def[name] = node.sourceline
        seq_use = defaultdict(list)
        for node in self.tree.findall('.//seq'):
            seq_use[node.get('n', '')].append(node.sourceline)
        for name, line in seq_def.items():
            if name not in seq_use:
                self.record(line, Verbosity.Warn, 'Sequence {name} defined but not used.')
        for name, lines in seq_use.items():
            if name not in seq_def:
                for line in lines:
                    self.record(line, Verbosity.Error, 'Sequence {name} used but not defined.')
    def stat_rules(self):
        self.record_stat('rules', len(self.tree.findall('.//rules/rule')))
        self.record_stat('macros', len(self.tree.findall('.//def-macro')))

FileLinter.register(LRXLinter, ext='lrx')
