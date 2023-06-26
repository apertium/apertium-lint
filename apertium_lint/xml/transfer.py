#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class TransferLinter(XmlLinter):
    Extensions = ['t1x', 't2x', 't3x', 't4x']
    ReportTypes = {
        'wrong-arg-count': (Verbosity.Error, 'Macro {0} called with {1} arguments but defined with {2}.'),
        'blank-manipulation': (Verbosity.Warn, '<let> copies a blank to a variable, which can corrupt formatting.'),
        'overlapping-paths': (Verbosity.Warn, 'The sequence [{0}] matches both this rule and the rule on line {1}.'),
    }
    def stat_rules(self):
        self.record_child_count(('rules'), self.tree, 'rule')
        self.record_child_count(('macros'), self.tree, 'def-macro')
    def check_macros(self):
        macdef = {}
        macarg = {}
        for mac in self.tree.iter('def-macro'):
            macdef[mac.get('n')] = mac.sourceline
            macarg[mac.get('n')] = int(mac.get('npar'))
        macref = defaultdict(list)
        for mac in self.tree.iter('call-macro'):
            n = mac.get('n')
            if n in macdef:
                macref[n].append(mac.sourceline)
                carg = self.get_child_count(mac, 'with-param')
                if carg != macarg[n]:
                    self.record('wrong-arg-count', mac, n, carg, macarg[n])
            else:
                self.record('undef', mac, 'Macro', n)
        for mac in macdef:
            if mac not in macref or not macref[mac]:
                self.record('unuse', macdef[mac], 'Macro', mac)
    def check_blank_manipulation(self):
        '''See https://github.com/apertium/apertium/issues/117'''
        for let in self.tree.iter('let'):
            if len(let) != 2:
                continue
            if let[0].tag == 'var':
                for b in let[1].iter('b'):
                    self.record('blank-manipulation', let.sourceline)
                    break
    def check_blocking_rules(self):
        cats = defaultdict(set)
        cat_overlap = defaultdict(set)
        for cat in self.tree.iter('def-cat'):
            name = cat.get('n')
            cat_overlap[name].add(name)
            for ci in cat.iter('cat-item'):
                l = ci.get('lemma', '')
                t = ci.get('tags', '')
                cats[name].add(l+'@'+t if l else t)
            for k, v in cats.items():
                if k == name: continue
                if not v.isdisjoint(cats[name]):
                    cat_overlap[k].add(name)
                    cat_overlap[name].add(k)
        pat2rule = defaultdict(list)
        for rule in self.tree.iter('rule'):
            pat = []
            for pi in rule.iter('pattern-item'):
                pat.append(pi.get('n'))
            for line, opat in pat2rule[len(pat)]:
                if all(b in cat_overlap[a] for a, b in zip(pat, opat)):
                    ls = []
                    for a, b in zip(pat, opat):
                        s = cats[a].intersection(cats[b])
                        ls.append((sorted(s) + ['*'])[0])
                    ex = ' '.join(ls)
                    self.record('overlapping-paths', rule.sourceline, ex, line)
                    break
            pat2rule[len(pat)].append((rule.sourceline, pat))
