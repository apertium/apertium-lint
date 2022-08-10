#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class ModesLinter(XmlLinter):
    Identifiers = [r'^modes\.xml$']
    ReportTypes = {
        'install-deps': (Verbosity.Error, 'Debug modes using files in .deps/ should not be installed.'),
        'redef-mode': (Verbosity.Error, 'Mode {0} defined more than once. First definition on line {1}.'),
        'required-mode': (Verbosity.Error, 'Mode {0} is defined, but corresponding mode {1} is missing.'),
        'suggested-mode': (Verbosity.Suggestion, 'Mode {0} is defined, but corresponding mode {1} is missing.'),
        'separate-biltrans': (Verbosity.Warn, 'Lexical transfer should be done in a separate step with lt-proc, not within apertium-transfer.'),
    }
    def check_deps(self):
        for node in self.tree.findall(".//mode[@install='yes']//file"):
            if node.attrib.get('name', '').startswith('.deps/'):
                self.record('install-deps', node)
    def check_mode_names(self):
        locs = {}
        morph = []
        for node in self.tree.findall('.//mode'):
            n = node.attrib.get('name', '')
            l = node.sourceline
            if n in locs:
                self.record('repeat-name', node, n, locs[n])
            else:
                locs[n] = l
            if n.endswith('-morph') and n.count('-') == 1:
                morph.append(n)
        sufs = [
            ('-gener', 'required-mode'),
            ('-tagger', 'required-mode'),
            ('-paradigm', 'suggested-mode'),
        ]
        for mode in morph:
            lang = mode.split('-')[0]
            for suf, msg in sufs:
                nm = lang + suf
                if nm not in locs:
                    self.record(msg, locs[mode], mode, nm)
    def arg_list(self, prog_node):
        def uni_arg(s):
            if len(s) > 2 and s.startswith('-') and not s.startswith('--'):
                return ['-'+c for c in s[1:]]
            else:
                return [s]
        def sargs(s):
            ret = []
            for a in s.split():
                ret += uni_arg(a)
            return ret
        ret = sargs(prog_node.attrib.get('name', ''))
        for ch in prog_node:
            if ch.tag == 'file':
                ret.append(ch.attrib.get('name', ''))
            elif ch.tag == 'arg':
                ret += sargs(ch.attrib.get('name', ''))
        return ret
    def check_programs(self):
        for prog_node in self.tree.findall('.//program'):
            args = self.arg_list(prog_node)
            if not args:
                continue
            prog_name = args[0]
            if prog_name == 'apertium-transfer':
                if '-b' not in args and '-n' not in args:
                    self.record('separate-biltrans', prog_node)
