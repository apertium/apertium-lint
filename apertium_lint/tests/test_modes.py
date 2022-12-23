#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class InstallDeps(unittest.TestCase, LintTestBase):
    file_name = 'modes.xml'
    file_contents = '''
<modes>
  <mode name="blah" install="yes">
    <pipeline>
      <program name="lt-proc">
        <file name=".deps/eng.automorf.bin"/>
      </program>
    </pipeline>
  </mode>
</modes>
'''
    expected_class = 'ModesLinter'
    expected_checks = [
        (6, 'install-deps')
    ]
