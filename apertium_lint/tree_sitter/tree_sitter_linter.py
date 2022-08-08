#!/usr/bin/env python3

from ..file_linter import FileLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class TreeSitterLinter(FileLinter):
    language = None
    def text(self, node, offset=0):
        return TSA.text(self.content, node, offset)
    def load(self):
        self.content, self.tree = TSA.parse_file(self.path, self.language)
        return True
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
                         sum(1 for _ in self.iter_children(self.tree,
                                                           tags, nest)))
    def query(self, qr, node=None):
        q = self.language.query(qr)
        yield from q.captures(node or self.tree)
    def iter_type(self, name, node=None):
        for n, _ in self.query(f'({name}) @thing', node):
            yield n
    def all_labels(self, name, node=None):
        for node in self.iter_type(name, node):
            yield self.text(node)
    def record(self, key, line, *args):
        l = line if isinstance(line, int) else TSA.line(line)
        FileLinter.record(self, key, l, *args)
    def gather_lines(self, qr, redef=None):
        dct = defaultdict(list)
        for node, _ in self.query(qr):
            t = self.text(node)
            l = TSA.line(node)
            if redef and t in dct:
                self.record(redef, l, t)
            dct[t].append(l)
        return dct
