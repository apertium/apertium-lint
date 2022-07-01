#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
from .tree_sitter_langs import RTX_LANGUAGE
from collections import defaultdict

class RTXLinter(TreeSitterLinter):
    language = RTX_LANGUAGE
    stat_labels = {
        'out_rules': 'Output rules',
        'retag_rules': 'Rewrite rules',
        'macros': 'Macros',
        'attrs': 'Attribute categories',
        'reduce_rules': 'Reduction rules',
    }
    def stat_rules(self):
        self.count_node('out_rules', 'output_rule')
        self.count_node('attrs', 'attr_rule')
        for node in self.iter_children(self.tree.root_node, 'output_rule'):
            if any(ch.type == 'lu_cond' for ch in node.children):
                self.record_stat('macros', inc=1)
        self.count_node('reduce_rules', 'reduce_rule')
        self.count_node('retag_rules', 'retag_rule')

FileLinter.register(RTXLinter, ext='rtx')
