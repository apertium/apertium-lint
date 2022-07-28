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
    def check_semicolons(self):
        for ctx in self.iter_children(self.tree.root_node, 'context', False):
            semi = False
            for ch in ctx.children:
                if ch.type == 'semicolon':
                    if not semi:
                        semi = True
                    else:
                        self.record(ch.start_point[0]+1, Verbosity.Warn,
                                    'Stray semicolon')
    def check_rule_pairs(self):
        for rl in self.iter_children(self.tree.root_node, 'rule', False):
            for ch in rl.children:
                if ch.type == 'symbol':
                    t = self.text(ch)
                    self.record(ch.start_point[0]+1, Verbosity.Suggestion,
                                f'Explicit pairs like {t}:{t} are more readable than bare symbols like {t}.')

FileLinter.register(TwolCLinter, ext='twol')
FileLinter.register(TwolCLinter, ext='twoc')
FileLinter.register(TwolCLinter, ext='twolc')
