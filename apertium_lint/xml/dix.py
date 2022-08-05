#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class DixLinter(XmlLinter):
    nodes_with_text = ['i', 'l', 'r', 'g', 'ig']
    nodes_in_text = ['a', 'b', 'm', 'g', 'j', 's']
    ReportTypes = {
        'LitSpace': (Verbosity.Warn, 'Spaces in entries should be written with <b/>.')
    }
    def collect_child_strings(self, node, nonempty=False):
        ret = []
        l = ''
        r = ''
        if node.text and node.tag in self.nodes_with_text:
            l = node.text
            r = node.text
        for ch in node:
            l2, r2, p = self.collect_strings(ch)
            if p:
                if l or r:
                    ret.append((l, r, ''))
                    l = ''
                    r = ''
                ret.append(('', '', p))
            else:
                l += l2
                r += r2
            if node.tag in self.nodes_with_text:
                l += ch.tail or ''
                r += ch.tail or ''
        if l or r:
            ret.append((l, r, ''))
        if nonempty and not ret:
            ret.append(('', '', ''))
        return ret
    def collect_strings(self, node): # -> (L, R, par)
        if node.tag in self.nodes_with_text:
            if node.text and ' ' in node.text:
                self.record('LitSpace', node)
        elif node.tag in self.nodes_in_text:
            if node.tail and ' ' in node.tail:
                self.record('LitSpace', node)
        if node.tag == 'a':
            return ('~', '~', '')
        elif node.tag == 'b':
            return (' ', ' ', '')
        elif node.tag == 'm':
            return ('>', '>', '')
        elif node.tag == 'j':
            return ('+', '+', '')
        elif node.tag == 's':
            n = '<' + node.get('n') + '>'
            return (n, n, '')
        elif node.tag == 'par':
            return ('', '', node.get('n'))
        elif node.tag == 're':
            return ('{REGEX}', '{REGEX}', '')
        elif node.tag in ['p', 'i']:
            return self.collect_child_strings(node, True)[0]
        elif node.tag == 'l':
            l, r, _ = self.collect_child_strings(node, True)[0]
            return (l, '', '')
        elif node.tag == 'r':
            l, r, _ = self.collect_child_strings(node, True)[0]
            return ('', r, '')
        elif node.tag in ['g', 'ig']:
            l, r, _ = self.collect_child_strings(node, True)[0]
            return ('#'+l, '#'+r, '')
        return ('???', '???', '')
    def statcheck_par_refs(self):
        pref = defaultdict(list)
        for pr in self.tree.iter('par'):
            pref[pr.get('n')].append(pr.sourceline)
        pdef = {}
        for pd in self.tree.iter('pardef'):
            self.record_child_count(('pardef_entries', pd.get('n')), pd, 'e')
            pdef[pd.get('n')] = pd.sourceline
        for sec in self.tree.iter('section'):
            name = sec.get('id') + '@' + sec.get('type')
            self.record_child_count(('section_entries', name), sec, 'e')
        for p in sorted(pref.keys()):
            if p not in pdef:
                for ln in pref[p]:
                    self.record('undef', ln, 'Pardef', p)
        for p in sorted(pdef.keys()):
            if p not in pref:
                self.record('unuse', pdef[p], 'Pardef', p)

class BiDixLinter(DixLinter):
    Identifiers = [r'^apertium-\w+-\w+.\w+-\w+.dix$']
    def stat_stems(self):
        self.record_stat('stems', len(self.tree.findall("*[@id='main']/e//l")))

class MonoDixLinter(DixLinter):
    Identifiers = [r'.*\.dix$']
    ReportTypes = {
        'maybeempty': (Verbosity.Error, 'Entry can be empty on {0} side.'),
        'initspace': (Verbosity.Error, 'Entry can begin with a space on the {0} side.'),
    }
    def space_blank_entry(self, ent):
        strs = self.collect_child_strings(ent)
        parname = ''
        if ent.getparent().tag == 'pardef':
            parname = ent.getparent().get('n')
        line = ent.sourceline
        if not strs:
            self.blank_left[parname].append((line, []))
            self.blank_right[parname].append((line, []))
        else:
            emptyl = []
            emptyr = []
            if ent.get('r') == 'LR':
                emptyr = None
            elif ent.get('r') == 'RL':
                emptyl = None
            emptylstr = True
            emptyrstr = True
            for l, r, p in strs:
                if p:
                    if emptyl != None:
                        emptyl.append(p)
                        self.space_left[parname].append((line, emptyl, False))
                    if emptyr != None:
                        emptyr.append(p)
                        self.space_right[parname].append((line, emptyr, False))
                if l:
                    if l[0].isspace() and emptyl != None:
                        self.space_left[parname].append((line, emptyl, True))
                    emptylstr = False
                    emptyl = None
                if r:
                    if r[0].isspace() and emptyr != None:
                        self.space_right[parname].append((line, emptyr, True))
                    emptyrstr = False
                    emptyr = None
            if emptylstr and emptyl != None:
                self.blank_left[parname].append((line, emptyl))
            if emptyrstr and emptyr != None:
                self.blank_right[parname].append((line, emptyr))
    def all_blank(self, ls, side):
        return all([self.can_be_empty(p)[0 if side=='left' else 1] for p in ls])
    def can_be_empty(self, par):
        if par in self.really_blank:
            return tuple(self.really_blank[par])
        left = [i for i, (line, reqs) in enumerate(self.blank_left[par])
                if self.all_blank(reqs, 'left')]
        right = [i for i, (line, reqs) in enumerate(self.blank_right[par])
                 if self.all_blank(reqs, 'right')]
        self.really_blank[par] = [left, right]
        return (left, right)
    def can_be_space(self, par):
        if par in self.really_space:
            return tuple(self.really_space[par])
        left = []
        right = []
        if par in self.space_left:
            for i, (line, reqs, final) in enumerate(self.space_left[par]):
                sp = [self.can_be_space(r)[0] for r in reqs]
                for j in range(len(reqs)):
                    if self.all_blank(reqs[:j], 'left') and sp[j]:
                        left.append((i, j))
                if final and self.all_blank(reqs, 'left'):
                    left.append((i, -1))
        if par in self.space_right:
            for i, (line, reqs, final) in enumerate(self.space_right[par]):
                sp = [self.can_be_space(r)[1] for r in reqs]
                for j in range(len(reqs)):
                    if self.all_blank(reqs[:j], 'right') and sp[j]:
                        right.append((i, j))
                if final and self.all_blank(reqs, 'right'):
                    right.append((i, -1))
        self.really_space[par] = [left, right]
        return (left, right)
    def check_space_blank(self):
        self.space_left = defaultdict(list)
        self.space_right = defaultdict(list)
        self.blank_left = defaultdict(list)
        self.blank_right = defaultdict(list)
        for ent in self.tree.iter('e'):
            self.space_blank_entry(ent)

        # TODO: It could be useful to recursively enumerate the pardefs
        # involved in these errors
        self.really_blank = defaultdict(list)
        le, re = self.can_be_empty('')
        for idx in le:
            self.record('maybeempty', self.blank_left[''][idx][0], 'left')
        for idx in re:
            self.record('maybeempty', self.blank_right[''][idx][0], 'right')

        self.really_space = defaultdict(list)
        ls, rs = self.can_be_space('')
        for idx, ct in ls:
            self.record('initspace', self.space_left[''][idx][0], 'left')
        for idx, ct in rs:
            self.record('initspace', self.space_right[''][idx][0], 'right')
    def stat_stems(self):
        self.record_stat('stems', len(self.tree.findall("section/*[@lm]")))
