#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class TransferLinter(XmlLinter):
    stat_labels = {}
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
                    self.record(mac.sourceline, Verbosity.Error, f'Macro {n} called with {carg} arguments but defined with {macarg[n]}.')
            else:
                self.record(mac.sourceline, Verbosity.Error, f'Macro {n} called but not defined.')
        for mac in macdef:
            if mac not in macref or not macref[mac]:
                self.record(macdef[mac], Verbosity.Warn, f'Macro {mac} defined but not used.')
