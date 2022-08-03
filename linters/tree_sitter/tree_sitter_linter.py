#!/usr/bin/env python3

from ..file_linter import FileLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class TreeSitterLinter(FileLinter):
    stat_labels = {}
    language = None
    def text(self, node, offset=0):
        return TSA.text(self.content, node, offset)
    def load(self):
        self.content, self.tree = TSA.parse_file(self.path, self.language)
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
    def statcheck_do_per(self):
        dct = defaultdict(lambda: defaultdict(list))
        for attr in dir(self):
            if '__' in attr.strip('_') and callable(getattr(self, attr)):
                pos, ntype = attr.split('__')[0].split('_', 1)
                dct[ntype][pos].append(attr)
        for k in dct:
            for a in dct[k]['pre']:
                getattr(self, a).__call__()
            for n, _ in self.query(f'({k}) @thing'):
                for a in dct[k]['per']:
                    getattr(self, a).__call__(n)
            for a in dct[k]['post']:
                getattr(self, a).__call__()
