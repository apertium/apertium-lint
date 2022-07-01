#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
from .tree_sitter_langs import CG_LANGUAGE
from collections import defaultdict

class CGLinter(TreeSitterLinter):
    language = CG_LANGUAGE
    stat_labels = {
        'rules': 'Rules',
    }
    def stat_rules(self):
        self.record_stat('rules',
                         sum(1 for n in self.tree.root_node.children
                             if n.type.startswith('rule')))

FileLinter.register(CGLinter, ext='rlx')
