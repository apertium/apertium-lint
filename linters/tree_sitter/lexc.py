#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class LexCLinter(TreeSitterLinter):
    language = TSA.LEXC
    Extensions = ['lexc']
    ReportTypes = {
        'wrong-paren': (Verbosity.Warn, '() means optional in XFST, did you mean []+ ?'),
        'multichar-redef': (Verbosity.Warn, 'Multichar symbol {0} defined multiple times.'),
        'undef-tag': (Verbosity.Error, 'Undefined tag {0}.'),
        'undef-archi': (Verbosity.Error, 'Undefined archiphoneme {0}'),
    }
    def process_lexicon_line(self, lex, line):
        l = ''
        r = ''
        com = TSA.end_comment(line)
        gloss = self.text(com).strip('!').strip() if com else ''
        cont = None
        for ch in line.children:
            if ch.type == 'lexicon_name':
                cont = self.text(ch)
        if line.children[0].type == 'lexicon_string':
            l = self.text(line.children[0])
            r = l
        elif line.children[0].type == 'lexicon_pair':
            for i, ch in enumerate(line.children[0].children):
                if ch.type == 'lexicon_string':
                    if i == 0:
                        l = self.text(ch)
                    else:
                        r = self.text(ch)
        if cont and (l or r):
            self.entries[lex].add((l, r, gloss, cont))
        elif cont:
            self.plain_continue[lex].add(cont)
    def process_lexicon(self, lex):
        name = ''
        for i, line in enumerate(lex.children):
            if line.type == 'lexicon_name':
                name = self.text(line)
            elif line.type == 'empty_lexicon_line':
                self.plain_continue[name].add(self.text(line.children[0]))
            elif line.type == 'lexicon_line':
                self.process_lexicon_line(name, line)
    def collect_stems(self):
        self.plain_continue = defaultdict(set)
        self.entries = defaultdict(set)
        nodes = self.tree.children
        for i, lex in enumerate(nodes):
            if lex.type == 'lexicon':
                self.process_lexicon(lex, com)
    def stat_stems(self):
        self.collect_stems()
        initial_lex = {'Root'}
        while True:
            l = len(initial_lex)
            for lx in list(initial_lex):
                initial_lex.update(self.plain_continue[lx])
            if len(initial_lex) == l:
                break
        lemma_gloss = set()
        lemma_gloss_no_mt = set()
        lemma_cont = set()
        lemma_cont_no_mt = set()
        for lex in initial_lex:
            for l, r, cont, com in self.entries[lex]:
                lemma_gloss.add((l, com))
                lemma_cont.add((l, cont))
                if 'Use/MT' not in com:
                    lemma_gloss_no_mt.add((l, com))
                    lemma_cont_no_mt.add((l, cont))
        self.record_stat('stem_gloss', len(lemma_gloss))
        self.record_stat('stem_gloss_vanilla', len(lemma_gloss_no_mt))
        self.record_stat('stem_cont', len(lemma_cont))
        self.record_stat('stem_cont_vanilla', len(lemma_cont_no_mt))
    def stat_entries(self):
        total = 0
        for lex in self.tree.children:
            n = 0
            name = ''
            for ln in lex.children:
                if ln.type == 'lexicon_name':
                    name = self.text(ln)
                elif ln.type == 'lexicon_line':
                    n += 1
            total += n
            self.record_stat(('entries', name), n)
        self.record_stat('total_entries', total)
    def check_regex(self):
        q = '(expression (expression (optional)) (plus)) @exp'
        for node, _ in self.query(q):
            self.record('wrong-paren', node)
    def read_alphabet(self):
        if hasattr(self, 'symbols'):
            return
        self.symbols = {}
        for node, _ in self.query('(multichar_symbols (alphabet_symbol) @a)'):
            s = self.text(node)
            if s in self.symbols:
                self.record('multichar-redef', node, s)
            else:
                self.symbols[s] = TSA.line(node)
    def pre_lexicon_string__symbols(self):
        self.read_alphabet()
    def per_lexicon_string__symbols(self, lexstr):
        txt = self.text(lexstr)
        t = txt
        while t:
            for s in self.symbols:
                if t.startswith(s):
                    t = t[len(s):]
                    break
            else:
                if t[0] == '%':
                    if t.startswith('%<') and '>' in t:
                        s, t = t.split('>', 1)
                        s += '>'
                        self.record('undef-tag', lexstr, s)
                    elif t.startswith('%{') and '}' in t:
                        s, t = t.split('}', 1)
                        s += '}'
                        self.record('undef-archi', lexstr, s)
                    else:
                        t = t[2:]
                else:
                    t = t[1:]
