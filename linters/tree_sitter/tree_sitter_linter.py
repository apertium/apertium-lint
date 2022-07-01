#!/usr/bin/env python3

from ..file_linter import FileLinter
from .tree_sitter_langs import Parser

class TreeSitterLinter(FileLinter):
    stat_labels = {}
    language = None
    def text(self, node, offset=0):
        return self.content[node.start_byte-offset:node.end_byte-offset].decode('utf-8')
    def load(self):
        self.parser = Parser()
        self.parser.set_language(self.language)
        with open(self.path, 'rb') as fin:
            self.content = fin.read()
        self.tree = self.parser.parse(self.content)
    def iter_children(self, node, tags=None, nest=True):
        keep = []
        if isinstance(tags, str):
            keep.append(tags)
        elif isinstance(tags, list):
            keep = tags
        def node_iter(node):
            if not keep or node.type in keep:
                yield node
                if not nest:
                    return
            for ch in node.children:
                yield from node_iter(ch)
        yield from node_iter(node)
    def count_node(self, name, tags, nest=False):
        self.record_stat(name,
                         sum(1 for _ in self.iter_children(self.tree.root_node,
                                                           tags, nest)))
