#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class RTXLinter(TreeSitterLinter):
    language = TSA.RTX
    Extensions = ['rtx']
    StatLabels = {
        'out_rules': 'Output rules',
        'retag_rules': 'Rewrite rules',
        'macros': 'Macros',
        'attrs': 'Attribute categories',
        'reduce_rules': 'Reduction rules',
    }
    ReportTypes = {
        'redef-retag': (Verbosity.Error, 'Redefinition of tag-rewrite rule from {0} to {1}. First definition on line {2}.'),
        'undef-retag': (Verbosity.Error, 'No tag-rewrite rule from {0} to {1} is defined.'),
        'unuse-retag': (Verbosity.Warn, 'Tag-rewrite rule from {0} to {1} is defined but not used.'),
        'inconsistent-operator': (Verbosity.Warn, 'Inconsistent operator name {0}. Prior instance on line {1} has {2}.'),
    }
    def stat_rules(self):
        self.count_node('out_rules', 'output_rule')
        self.count_node('attrs', 'attr_rule')
        qr = '(output_rule (lu_cond) @lc)'
        self.record_stat('macros', sum(1 for n in self.query(qr)))
        self.count_node('reduce_rules', 'reduce_rule')
        self.count_node('retag_rules', 'retag_rule')
    def check_retag(self):
        rdef = {}
        for node in self.iter_type('retag_rule'):
            src = self.text(node.child_by_field_name('src_attr'))
            trg = self.text(node.child_by_field_name('trg_attr'))
            if (src, trg) in rdef:
                self.record('redef-retag', node, src, trg, rdef[(src, trg)])
            else:
                rdef[(src, trg)] = TSA.line(node)
        ruse = defaultdict(list)
        qr = '''[
                 (set_var value: (clip attr: (ident))) @sv
                 (clip convert: (ident)) @c
                ]'''
        for node, typ in self.query(qr):
            src, trg = '', ''
            if typ == 'sv':
                trg = self.text(node.child_by_field_name('name'))
                cl = node.child_by_field_name('value')
                nsrc = cl.child_by_field_name('convert')
                if not nsrc:
                    nsrc = cl.child_by_field_name('attr')
                src = self.text(nsrc)
            elif typ == 'c':
                src = self.text(node.child_by_field_name('attr'))
                trg = self.text(node.child_by_field_name('convert'))
            if src and trg and src != trg:
                ruse[(src, trg)].append(TSA.line(node))
        for src, trg in rdef.keys():
            if (src, trg) not in ruse and src != trg:
                self.record('unuse-retag', rdef[(src, trg)], src, trg)
        for src, trg in ruse.keys():
            if src and trg and (src, trg) not in rdef:
                if trg in ['lem', 'lemh', 'lemq']:
                    continue
                for ln in ruse[(src, trg)]:
                    self.record('undef-retag', ln, src, trg)
    def check_operators(self):
        def get_op(opstr):
            s = opstr.replace('_', '').replace('-', '').lower()
            caseless = False
            case = ['cl', 'caseless', 'fold', 'foldcase']
            for c in case:
                if s.endswith(c):
                    s = s[:-len(c)]
                    caseless = True
            synonyms = {
                '=': 'equal', '∈': 'in',
                '&': 'and', '|': 'or', '~': 'not', '⌐': 'not',
                'startswith': 'isprefix', 'beginswith': 'isprefix',
                'startswithlist': 'hasprefix', 'beginswithlist': 'hasprefix',
                'endwith': 'issuffix', 'endswithlist': 'hassuffix',
                'issubstring': 'contains'
            }
            s = synonyms.get(s, s)
            return s, caseless
        opuse = defaultdict(list)
        qr = '[(str_op) @op (and) @op (or) @op (not) @op]'
        for node, typ in self.query(qr):
            txt = self.text(node)
            opuse[get_op(txt)].append((txt, TSA.line(node)))
        for opls in opuse.values():
            first_op = opls[0][0]
            first_line = opls[0][1]
            for op, ln in opls[1:]:
                if op != first_op:
                    self.record('inconsistent-operator', ln, op, first_line, first_op)
