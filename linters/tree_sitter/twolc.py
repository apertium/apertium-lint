#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class TwolCLinter(TreeSitterLinter):
    language = TSA.TWOLC
    stat_labels = {
        'rules': 'Rules',
        'sets': 'Sets',
        'symbols': 'Alphabet symbol pairs',
        'in_symbols': 'Input alphabet symbols',
        'out_symbols': 'Output alphabet symbols',
    }
    def read_alphabet(self):
        if hasattr(self, 'symbols'):
            return
        self.symbols = defaultdict(list)
        q = TSA.TWOLC.query('(alphabet [(symbol) @sym (symbol_pair) @pair])')
        captures = q.captures(self.tree)
        for node, kind in captures:
            if kind == 'sym':
                sym = self.text(node)
                self.symbols[sym].append(sym)
            elif kind == 'pair':
                l = node.child_by_field_name('left')
                r = node.child_by_field_name('right')
                if not l or not r:
                    self.record(TSA.line(node), Verbosity.Error,
                                'Alphabet should not contain implicit pairs')
                sl = self.text(l) if l else '0'
                sr = self.text(r) if r else '0'
                if sr in self.symbols[sl]:
                    self.record(TSA.line(node), Verbosity.Warn,
                                f'Symbol {sl}:{sr} listed multiple times')
                else:
                    self.symbols[sl].append(sr)
    def read_sets(self):
        if hasattr(self, 'sets'):
            return
        self.sets = {}
        for node, _ in self.query('(sets (set name: (symbol) @n))'):
            n = self.text(node)
            ls = []
            for ch, _ in self.query('(symbol)'):
                if not ch.is_named:
                    ls.append(self.text(ch))
            self.sets[n] = ls
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
            out_syms.update(l)
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
                    self.record(TSA.line(ch), Verbosity.Warn, 'Stray semicolon')
    def per_rule__plain_symbol(self, rl):
        node = rl.child_by_field_name('target')
        if node and node.type == 'symbol':
            t = self.text(node)
            self.record(TSA.line(node), Verbosity.Suggestion,
                        f'Explicit pairs like {t}:{t} are more readable than bare symbols like {t}.')
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
    def pre_rule__gather_symbols(self):
        self.read_alphabet()
        self.read_sets()
        self.used_symbols = defaultdict(set)
    def per_rule__undefined_symbols(self, rule):
        target = rule.child_by_field_name('target')
        l, r = self.symbol_to_pair(target)
        var = rule.child_by_field_name('variables')
        pairs = []
        ls = self.sets.get(l, [l])
        rs = self.sets.get(r, [r])
        if var:
            varl = False
            varr = False
            for node, _ in self.query('(in_keyword) @kwd', var):
                name = self.text(node.prev_named_sibling)
                nxt = node.next_named_sibling
                syms = []
                if nxt.type == 'loptional':
                    nxt = nxt.next_named_sibling
                    for ch, _ in self.query('(symbol) @s', nxt):
                        syms.append(self.text(ch))
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
                msg = f'Symbol pair {l}:{r} not listed in alphabet'
                self.record(TSA.line(target), Verbosity.Warn, msg)
            self.used_symbols[l].add(r)
    def post_rule__uncontrolled_symbols(self):
        for k in self.symbols:
            sdef = set(self.symbols[k])
            suse = self.used_symbols[k]
            uncon = sdef - suse
            if len(uncon) > 1:
                s = ' '.join(sorted(uncon))
                # TODO: is there a better loc for this?
                self.record(1, Verbosity.Warn,
                            f'Symbol {k} has multiple unconstrained realizations ({s})')
            if len(sdef) == 1 and sdef == suse:
                s = list(sdef)[0]
                # TODO: this definitely has a right location
                self.record(1, Verbosity.Suggestion,
                            f'Symbol {k} has only 1 realization ({s}), so constraining it with a rule is unnecesary')

FileLinter.register(TwolCLinter, ext=['twol', 'twoc', 'twolc'])
