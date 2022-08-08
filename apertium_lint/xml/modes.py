#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from .xml import XmlLinter
from collections import defaultdict

class ModesLinter(XmlLinter):
    Identifiers = [r'^modes\.xml$']
    ReportTypes = {
        'install-deps': (Verbosity.Error, 'Debug modes using files in .deps/ should not be installed.'),
    }
    def check_deps(self):
        for node in self.tree.findall(".//mode[@install='yes']//file"):
            if node.attrib.get('name', '').startswith('.deps/'):
                self.record('install-deps', node)
