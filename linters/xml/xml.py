#!/usr/bin/env python3

from ..file_linter import FileLinter, Verbosity
from lxml import etree

class XmlLinter(FileLinter):
    stat_labels = {}
    def load(self):
        self.tree = etree.parse(self.path).getroot()
    def get_child_count(self, element, child_type):
        return len(list(element.iter(child_type)))
    def record_child_count(self, name, element, child_type):
        self.record_stat(name, self.get_child_count(element, child_type))
