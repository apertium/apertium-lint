#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .tree_sitter_linter import TreeSitterLinter
import tree_sitter_apertium as TSA
from collections import defaultdict

class LexdLinter(TreeSitterLinter):
    language = TSA.LEXD
    Extensions = ['lexd']
    StatLabels = {
        'lex_entries': 'Lexicon entries',
        'pat_entries': 'Pattern lines',
        ('lex_entries', ''): 'All anonymous lexicons',
        ('pat_entries', ''): 'Toplevel pattern'
    }
    ReportTypes = {
        'adj-tok-merge': (Verbosity.Warn, 'References to {0} can be merged, decreasing the number of paired tokens.'),
        'tok-merge': (Verbosity.Warn, 'Line can be rearranged so as to merge references to {0}, decreasing the number of paired tokens.'),
        'partition': (Verbosity.Warn, 'Line can be partitioned into sub-patterns to decrease the number of overlapping sets of paired tokens.\n{0}\n  Possible partition point'),
        'tag-unuse': (Verbosity.Warn, 'Tag {0} set but never used in a filter.'),
        'tag-unset': (Verbosity.Warn, 'Tag {0} used in a filter but never set.'),
        'nonempty-anon-left': (Verbosity.Suggestion, 'Non-tag content is not normally expected on the left side of an anonymous lexicon. This is often a typo.'),
    }
    def get_side(self, node, count_type):
        parts = ''
        for c in node.children:
            if c.type == 'colon':
                parts += ':'
            elif c.type == count_type:
                parts += 's'
        if parts == ':s':
            return 'right'
        elif parts == 's:':
            return 'left'
        else:
            return 'both'
    def classify_pattern_token(self, tok):
        if tok.type == '\n' or tok.type == 'comment':
            return None
        elif tok.type != 'pattern_token':
            return ('?', 'both')
        for ch in tok.children:
            if ch.type in ['left_sieve', 'right_sieve']:
                return ('<>', 'both')
            elif ch.type == 'anonymous_lexicon':
                return ('[]', self.get_side(ch.children[1], 'lexicon_string'))
            elif ch.type == 'anonymous_pattern':
                return ('()', 'both')
            name = ''
            for n in tok.children:
                if n.type == 'lexicon_reference':
                    return (self.text(n.children[0]),
                            self.get_side(tok, 'lexicon_reference'))
    def examine_pattern_line(self, line):
        line_number = TSA.line(line)
        toks = [] # (name, side)
        for tok in line.children:
            c = self.classify_pattern_token(tok)
            if c:
                toks.append(c)
        has_matched = False
        matched = defaultdict(list)
        special = ['<>', '()', '[]', '?']
        matched_names = set()
        for i, t in enumerate(toks):
            matched[t[0]].append(i)
            if t[0] not in special and len(matched[t[0]]) > 1:
                has_matched = True
                matched_names.add(t[0])
        if not has_matched:
            return
        handled = []
        for name in matched_names:
            if len(matched[name]) == 2:
                l1, l2 = matched[name]
                if (toks[l1][1] == 'left' and toks[l2][1] == 'right') or \
                   (toks[l1][1] == 'right' and toks[l2][1] == 'left'):
                    if l2 == l1 + 1:
                        self.record('adj-tok-merge', line_number, name)
                        handled.append(name)
                        continue
                    for i in range(l1+1,l2):
                        if toks[i][1] == 'both':
                            break
                    else:
                        self.record('tok-merge', line_number, name)
                        handled.append(name)
                        continue
        todo = [n for n in matched_names if n not in handled]
        for i in range(len(toks)):
            left = []
            right = []
            failed = False
            for tk in todo:
                if all(n <= i for n in matched[tk]):
                    left.append(tk)
                elif all(n > i for n in matched[tk]):
                    right.append(tk)
                else:
                    failed = True
                    break
            if failed:
                continue
            if len(left) > 0 and len(right) > 0:
                msg = self.text(line).rstrip() + '\n'
                msg += ' ' * (line.children[i].end_byte - line.start_byte)
                # TODO: this doesn't properly account for diacritics etc
                msg += '^'
                self.record('partition', line_number, msg)
                return
    def check_tags(self):
        tag_set = defaultdict(list)
        tag_use = defaultdict(list)
        qr = '[(tag_setting) @set (tag_filter) @use (tag_distribution) @use]'
        for node, mode in self.query(qr):
            dct = tag_set if mode == 'set' else tag_use
            for tg in self.all_labels('tag', node):
                dct[tg].append(TSA.line(node))
        self.warn_def_use(tag_set, tag_use, 'tag-unuse')
        self.warn_def_use(tag_use, tag_set, 'tag-unset')
    def stat_all(self, node=None, name=''):
        if node == None:
            node = self.tree
        if node.type == 'lexicon_line':
            self.record_stat(('lex_entries', name), inc=1)
        elif node.type == 'pattern_line':
            self.record_stat(('pat_entries', name), inc=1)
        n = ''
        for ch in node.children:
            if node.type in ['pattern_block', 'lexicon_block'] and ch.type == 'identifier':
                n = self.text(ch)
            self.stat_all(ch, n)
    def check_patterns(self):
        for line in self.iter_type('pattern_line'):
            self.examine_pattern_line(line)
    def per_anonymous_lexicon(self, node):
        char = False
        for c in node.children[1].children:
            if c.type == 'colon':
                break
            elif c.type == 'tag_symbol':
                return
            else:
                char = True
        if char:
            self.record('nonempty-anon-left', node)
