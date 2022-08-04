#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class TwolCLinter(TreeSitterLinter):
    language = TSA.TWOLC
    Extensions = ['twol', 'twoc', 'twolc']
    StatLabels = {
        'rules': 'Rules',
        'sets': 'Sets',
        'symbols': 'Alphabet symbol pairs',
        'in_symbols': 'Input alphabet symbols',
        'out_symbols': 'Output alphabet symbols',
    }
    ReportTypes = {
        'alpha-implicit': (Verbosity.Error, 'Alphabet should not contain implicit pairs.'),
        'alpha-repeat': (Verbosity.Warn, 'Symbol {0}:{1} listed multiple times.'),
        'stray-semi': (Verbosity.Warn, 'Stray semicolon.'),
        'explicit-target': (Verbosity.Suggestion, 'Explicit pairs like {0}:{0} are more readable than bare symbols like {0}.'),
        'undef-pair': (Verbosity.Warn, 'Symbol pair {0}:{1} not listed in alphabet.'),
        'unconstrained': (Verbosity.Warn, 'Symbol {0} has multiple unconstrained realizations ({1}).'),
        'over-constrained': (Verbosity.Suggestion, 'Symbol {0} has only 1 realization ({1}), so constraining it witha rule is unnecessary.'),
    }
    def read_alphabet(self):
        if hasattr(self, 'symbols'):
            return
        self.symbols = defaultdict(dict)
        q = TSA.TWOLC.query('(alphabet [(symbol) @sym (symbol_pair) @pair])')
        captures = q.captures(self.tree)
        for node, kind in captures:
            if kind == 'sym':
                sym = self.text(node)
                self.symbols[sym][sym] = TSA.line(node)
            elif kind == 'pair':
                l = node.child_by_field_name('left')
                r = node.child_by_field_name('right')
                if not l or not r:
                    self.record('alpha-implicit', node)
                sl = self.text(l) if l else '0'
                sr = self.text(r) if r else '0'
                if sr in self.symbols[sl]:
                    self.record('alpha-repeat', node, sl, sr)
                else:
                    self.symbols[sl][sr] = TSA.line(node)
    def read_sets(self):
        if hasattr(self, 'sets'):
            return
        self.sets = {}
        for node, _ in self.query('(sets (set name: (symbol) @n))'):
            n = self.text(node)
            self.sets[n] = [self.text(c)
                            for c in self.iter_type('symbol') if not c.is_named]
    def stat_rules(self):
        self.count_node('rules', 'rule')
        self.count_node('sets', 'set')
        self.read_alphabet()
        sin = len(self.symbols)
        if '0' in self.symbols:
            sin -= 1
        out_syms = set()
        spair = 0
        for l in self.symbols.values():
            out_syms.update(l.keys())
            spair += len(l)
        sout = len(out_syms)
        if '0' in out_syms:
            sout -= 1
        self.record_stat('symbols', spair)
        self.record_stat('in_symbols', sin)
        self.record_stat('out_symbols', sout)
    def per_context__semicolon(self, ctx):
        semi = False
        for ch in ctx.children:
            if ch.type == 'semicolon':
                if not semi:
                    semi = True
                else:
                    self.record('stray-semi', ch)
    def per_rule__plain_symbol(self, rl):
        node = rl.child_by_field_name('target')
        if node and node.type == 'symbol':
            t = self.text(node)
            self.record('explicit-target', node, t)
    def symbol_to_pair(self, node):
        if not node:
            return ('0', '0')
        if node.type == 'symbol':
            t = self.text(node)
            return (t, t)
        ln = node.child_by_field_name('left')
        rn = node.child_by_field_name('right')
        l = self.text(ln) if ln else '0'
        r = self.text(rn) if rn else '0'
        return (l, r)
    def pre_rule(self):
        self.read_alphabet()
        self.read_sets()
        self.used_symbols = defaultdict(dict)
    def per_rule__undefined_symbols(self, rule):
        # TODO: regex targets
        target = rule.child_by_field_name('target')
        l, r = self.symbol_to_pair(target)
        var = rule.child_by_field_name('variables')
        pairs = []
        ls = self.sets.get(l, [l])
        rs = self.sets.get(r, [r])
        if var:
            varl = False
            varr = False
            for node in self.iter_type('in_keyword', var):
                name = self.text(node.prev_named_sibling)
                nxt = node.next_named_sibling
                syms = []
                if nxt.type == 'loptional':
                    nxt = nxt.next_named_sibling
                    syms = [self.text(c) for c in self.iter_type('symbol', nxt)]
                else:
                    syms = self.sets.get(self.text(nxt), [])
                if l == name:
                    varl = True
                    ls = syms
                if r == name:
                    varr = True
                    rs = syms
            typ = var.child_by_field_name('type')
            if typ and varl and varr:
                t = self.text(typ)
                if t == 'matched':
                    pairs = list(zip(ls, rs))
                elif t == 'mixed':
                    for i, si in enumerate(ls):
                        for j, sj in enumerate(rs):
                            if i != j:
                                pairs.append((si, sj))
                ls = []
                rs = []
        for l in ls:
            for r in rs:
                pairs.append((l, r))
        for l, r in sorted(set(pairs)):
            if r not in self.symbols[l]:
                self.record('undef-pair', target, l, r)
            self.used_symbols[l][r] = TSA.line(rule)
    def post_rule__uncontrolled_symbols(self):
        for k in self.symbols:
            sdef = set(self.symbols[k].keys())
            suse = set(self.used_symbols[k].keys())
            uncon = list(sorted(sdef - suse))
            if len(uncon) > 1:
                s = ' '.join(uncon)
                self.record('unconstrained', self.symbols[k][uncon[0]], k, s)
            if len(sdef) == 1 and sdef == suse:
                s = list(sdef)[0]
                self.record('over-constrained', self.used_symbols[k][s], k, s)
