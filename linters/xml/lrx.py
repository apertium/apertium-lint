#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class LRXLinter(XmlLinter):
    Extensions = ['lrx']
    ReportTypes = {
        'p-non-mac': (Verbosity.Error, 'Parameterized attribute {0} cannot be used outside of <def-macro>.'),
        'p-non-p': (Verbosity.Error, '<{0}> cannot have both parameterized {1} and non-parameterized {2}.'),
        'param-non-mac': (Verbosity.Error, 'Cannot inject parameter outside of <def-macro>.'),
        'non-param-mac': (Verbosity.Warn, 'Rule does not use any parameters so there is no need for it to be inside <def-macro>.'),
        'long-or': (Verbosity.Suggestion, 'Sequence has more than 5 elements - did you forget an <or>?'),
        'redef-seq': (Verbosity.Error, 'Redefinition of sequence {0} (initial definition on line {1}.')
    }
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
                        self.record('p-non-mac', node, attr)
                    if attr[1:] in node.keys():
                        self.record('p-non-p', node, node.tag, attr, attr[1:])
            if node.tag == 'param':
                any_mac = True
                if not in_mac:
                    self.record('param-non-mac', node)
            for ch in node:
                any_mac = self.check_macro_params(ch, in_mac) or any_mac
            if node.tag == 'rule' and in_mac and not any_mac:
                self.record('non-param-mac', node)
            return any_mac
    def check_repeat(self):
        for node in self.tree.findall('.//repeat'):
            att = node.keys()
            if 'from' not in att and 'pfrom' not in att:
                self.record_missing_attr(node, 'from')
            if 'upto' not in att and 'pupto' not in att:
                self.record_missing_attr(node, 'upto')
    def check_seqs(self):
        seq_def = {}
        for node in self.tree.findall('.//def-seq'):
            if len(node) > 5:
                self.record('long-or', node)
            name = node.get('n', '')
            if name in seq_def:
                self.record('redef-seq', node, name, seq_def[name])
            else:
                seq_def[name] = node.sourceline
        seq_use = defaultdict(list)
        for node in self.tree.findall('.//seq'):
            seq_use[node.get('n', '')].append(node.sourceline)
        for name, line in seq_def.items():
            if name not in seq_use:
                self.record('unuse', line, 'Sequence', name)
        for name, lines in seq_use.items():
            if name not in seq_def:
                for line in lines:
                    self.record('undef', line, 'Sequence', name)
    def stat_rules(self):
        self.record_stat('rules', len(self.tree.findall('.//rules/rule')))
        self.record_stat('macros', len(self.tree.findall('.//def-macro')))
