#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
from .tree_sitter_langs import TWOLC_LANGUAGE
from collections import defaultdict

class TwolCLinter(TreeSitterLinter):
    language = TWOLC_LANGUAGE
    stat_labels = {
        'rules': 'Rules',
        'sets': 'Sets',
        'symbols': 'Alphabet symbols'
    }
    def stat_rules(self):
        self.count_node('rules', 'rule')
        self.count_node('sets', 'set')
        for node in self.tree.root_node.children:
            if node.type == 'alphabet':
                self.record_stat('symbols',
                                 sum(1 for n in node.children
                                     if n.type.startswith('symbol')))

FileLinter.register(TwolCLinter, ext='twol')
FileLinter.register(TwolCLinter, ext='twoc')
