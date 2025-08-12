#!/usr/bin/env python3

import unittest
from .base import LintTestBase

class BlankManipulation(unittest.TestCase, LintTestBase):
    file_name = 'test.t1x'
    file_contents = '''
<transfer default="lu">
  <section-def-cats>
    <def-cat n="nom">
      <cat-item tags="n.*"/>
    </def-cat>
  </section-def-cats>

  <section-def-attrs>
  </section-def-attrs>

  <section-def-vars>
    <def-var n="macro_generated_lu"/>
  </section-def-vars>

  <section-def-macros>
    <def-macro n="test" npar="2">
      <let>
        <var n="macro_generated_lu"/>
        <concat>
          <lit v="^de"/>
          <lit-tag v="pr"/>
          <lit v="$"/>
          <b/>
          <lit v="^blarg"/>
          <lit-tag v="ij"/>
          <lit v="$"/>
        </concat>
      </let>
    </def-macro>
  </section-def-macros>

  <section-rules>
    <rule comment="REGLA: nom nom">
      <pattern>
        <pattern-item n="nom"/>
        <pattern-item n="nom"/>
      </pattern>
      <action>
        <call-macro n="test">
          <with-param pos="1"/>
          <with-param pos="2"/>
        </call-macro>
        <out>
          <lu>
            <clip pos="1" side="tl" part="whole"/>
          </lu>
          <b/>
          <var n="macro_generated_lu"/>
          <b/>
          <lu>
            <clip pos="2" side="tl" part="whole"/>
          </lu>
        </out>
      </action>
    </rule>
  </section-rules>
</transfer>
'''
    expected_class = 'TransferLinter'
    expected_checks = [
        (18, 'blank-manipulation'),
    ]

class UndefinedAndUnused(unittest.TestCase, LintTestBase):
    file_name = 'test.t1x'
    file_contents = '''
<transfer default="lu">
  <section-def-cats>
    <def-cat n="nom">
      <cat-item tags="n.*"/>
    </def-cat>
    <def-cat n="nom">
      <cat-item tags="n"/>
    </def-cat>
  </section-def-cats>

  <section-def-attrs>
    <def-attr n="a_case">
      <attr-item tags="nom"/>
      <attr-item tags="acc"/>
    </def-attr>
  </section-def-attrs>

  <section-def-vars>
  </section-def-vars>

  <section-def-macros>
  </section-def-macros>

  <section-rules>
    <rule comment="REGLA: nom nom">
      <pattern>
        <pattern-item n="nom"/>
        <pattern-item n="nom"/>
      </pattern>
      <action>
        <out>
          <lu>
            <clip pos="1" side="tl" part="whole"/>
          </lu>
          <b/>
          <var n="macro_generated_lu"/>
          <b/>
          <lu>
            <clip pos="2" side="tl" part="whole"/>
          </lu>
        </out>
      </action>
    </rule>
  </section-rules>
</transfer>
'''
    expected_class = 'TransferLinter'
    expected_checks = [
        (7, 'redef'),
        (13, 'unuse'),
        (37, 'undef'),
    ]

class OutOfRange(unittest.TestCase, LintTestBase):
    file_name = 'test.t1x'
    file_contents = '''
<transfer default="lu">
  <section-def-cats>
    <def-cat n="nom">
      <cat-item tags="n"/>
      <cat-item tags="n.*"/>
    </def-cat>
  </section-def-cats>

  <section-def-attrs>
    <def-attr n="nbr">
      <attr-item v="sg"/>
    </def-attr>
  </section-def-attrs>

  <section-def-vars>
  </section-def-vars>

  <section-def-macros>
    <def-macro n="foo" npar="2">
      <let><clip pos="3" side="tl" part="nbr"/><lit-tag v="pl"/></let>
    </def-macro>
  </section-def-macros>

  <section-rules>
    <rule comment="REGLA: nom nom">
      <pattern>
        <pattern-item n="nom"/>
        <pattern-item n="nom"/>
      </pattern>
      <action>
        <call-macro n="foo">
          <with-param pos="1"/>
          <with-param pos="2"/>
        </call-macro>
        <out>
          <lu>
            <clip pos="3" side="tl" part="whole"/>
          </lu>
          <b/>
          <lu>
            <clip pos="2" side="tl" part="whole"/>
          </lu>
        </out>
      </action>
    </rule>
  </section-rules>
</transfer>
'''
    expected_class = 'TransferLinter'
    expected_checks = [
        (21, 'out-of-range-macro'),
        (38, 'out-of-range-rule'),
    ]
