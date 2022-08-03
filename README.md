# apertium-lint
linter for Apertium source files

# Implemented Features

- lexd
  - checks for optimizable patterns
  - checks for unused or unset tag filters
  - counts lexicon and pattern entries
- monodix
  - checks for unused or undefined pardefs
  - checks for empty entries
  - checks for entries beginning with a space
  - counts pardef and section entries

# Dependencies

```bash
pip3 install tree_sitter lxml tree-sitter-apertium
```

# Example usage

## Lexd
blah.lexd
```
PATTERNS
X: Z :X Y: A :Y

LEXICON X
x
LEXICON Y
y
LEXICON Z
z
LEXICON A
a
```

```
$ ./apertium-lint.py blah.lexd
blah.lexd Line 2
Line can be partitioned into sub-patterns to decrease the number of overlapping sets of paired tokens.
X: Z :X Y: A :Y
       ^
  Possible partition point
```

## Monodix

blah.dix
```xml
<?xml version="1.0" encoding="UTF-8"?>
<dictionary>
  <alphabet>ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÄÅÆÇÈÉÊËÍÑÒÓÔÕÖØÙÚÜČĐŊŠŦŽabcdefghijklmnopqrstuvwxyzàáâäåæçèéêëíñòóôõöøùúüčđŋšŧž­-</alphabet>
  <sdefs>
    <sdef n="n" 	c="Noun"/>
  </sdefs>
  <pardefs>
  </pardefs>
  <section id="main" type="standard">
    <e><p><l><b/>a</l><r>a<s n="n"/></r></p></e>
  </section>
</dictionary>
```

```
$ ./apertium-lint.py blah.dix
blah.dix Line 10
Entry can begin with a space on the left side.
```
