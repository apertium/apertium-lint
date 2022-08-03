#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium
from collections import defaultdict

class CGLinter(TreeSitterLinter):
    language = tree_sitter_apertium.CG
    stat_labels = {
        'rules': 'Rules',
    }
    def stat_rules(self):
        self.record_stat('rules',
                         sum(1 for n in self.tree.children
                             if n.type.startswith('rule')))

FileLinter.register(CGLinter, ext='rlx')
