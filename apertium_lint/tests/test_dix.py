#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class MonodixTest(unittest.TestCase, LintTestBase):
    file_name = 'test.dix'
    file_contents = '''
<dictionary>
  <alphabet>ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÄÅÆÇÈÉÊËÍÑÒÓÔÕÖØÙÚÜČĐŊŠŦŽabcdefghijklmnopqrstuvwxyzàáâäåæçèéêëíñòóôõöøùúüčđŋšŧž­-</alphabet>
  <sdefs>
    <sdef n="n"/>
    <sdef n="vblex"/>
    <sdef n="m"/>
    <sdef n="pr"/>
    <sdef n="def"/>
    <sdef n="ind"/>
  </sdefs>
  <pardefs></pardefs>
  <section id="main" type="standard">
    <e lm="abc"><p><l>ab c</l><r>ab<s n="n"/><s n="def"/></r></p></e>
    <e lm="ab"><p><l>a	b</l><r>ab<s n="n"/><s n="ind"/></r></p></e>
    <e><p><l>y</l><r>y<s n="n"/> <s n="ind"/></r></p></e>
    <e><p><l>n</l><r>n<s n="n"/>	<s n="ind"/></r></p></e>
  </section>
  <section id="j" type="standard">
    <e><p><l>j<a/>g</l><r>j<s n="pr"/><j/>g<s n="n"/></r></p></e>
    <e><p><l>j<b/>h</l><r>j<s n="pr"/><j/>h<s n="n"/></r></p></e>
    <e><p><l>k<m/>g</l><r>k<s n="pr"/><j/>g<s n="n"/></r></p></e>
  </section>
</dictionary>
'''
    expected_class = 'MonoDixLinter'
    expected_checks = [
        (14, 'LitSpace'),
        (15, 'OtherSpace'),
        (16, 'LitSpace'),
        (17, 'OtherSpace'),
    ]
    stats = True
    expected_stats = {
        'section_entries': {
            'name': 'section_entries',
            'long_name': 'Entries in each section',
            'value': {
                'main@standard': {
                    'name': 'main@standard',
                    'long_name': 'main@standard',
                    'value': 4,
                },
                'j@standard': {
                    'name': 'j@standard',
                    'long_name': 'j@standard',
                    'value': 3,
                },
            },
        },
        'stems': {
            'name': 'stems',
            'long_name': 'stems',
            'value': 2,
        },
    }

class Pardefs(unittest.TestCase, LintTestBase):
    file_name = 'test.dix'
    file_contents = '''
<dictionary>
  <alphabet>ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÄÅÆÇÈÉÊËÍÑÒÓÔÕÖØÙÚÜČĐŊŠŦŽabcdefghijklmnopqrstuvwxyzàáâäåæçèéêëíñòóôõöøùúüčđŋšŧž­-</alphabet>
  <sdefs>
    <sdef n="n"/>
    <sdef n="vblex"/>
    <sdef n="m"/>
    <sdef n="pr"/>
    <sdef n="def"/>
    <sdef n="ind"/>
  </sdefs>
  <pardefs>
    <pardef n="har/gle__n">
      <e><p><l></l><r>hi</r></p></e>
    </pardef>
  </pardefs>
  <section id="main" type="standard">
    <e lm="hargle"><i>hargle</i><par n="har/gle__n"/></e>
    <e lm="hargle"><i>har</i><par n="har/gle__n"/></e>
    <e lm="hargle"><i>ha</i><par n="har/gle__n"/></e>
  </section>
</dictionary>
'''
    expected_class = 'MonoDixLinter'
    expected_checks = [
        (18, 'lemma-is-stem'),
        (20, 'wrong-stem'),
    ]
