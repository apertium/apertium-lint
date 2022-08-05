#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from lxml import etree

class XmlLinter(FileLinter):
    ReportTypes = {
        'missing-attr': (Verbosity.Error, '<{0}> must have value for attribute {1}.'),
        'invalid-xml': (Verbosity.Error, 'Invalid XML: {0}.'),
    }
    def load(self):
        try:
            self.tree = etree.parse(self.path).getroot()
            return True
        except etree.XMLSyntaxError as e:
            self.record('invalid-xml', e.lineno, e.msg)
            return False
    def get_child_count(self, element, child_type):
        return len(list(element.iter(child_type)))
    def record_child_count(self, name, element, child_type):
        self.record_stat(name, self.get_child_count(element, child_type))
    def record_missing_attr(self, node, attr):
        self.record('missing-attr', node.sourceline, node.tag, attr)
    def record(self, key, node, *args):
        l = node if isinstance(node, int) else node.sourceline
        FileLinter.record(self, key, l, *args)
