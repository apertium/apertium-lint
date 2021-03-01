# apertium-lint
linter for Apertium source files

# Dependencies
```bash
pip3 install tree_sitter
```

# Example usage
```
$ ./apertium-lint.py blah.lexd
Linting blah.lexd
Line 2: References to Z can be merged, decreasing the number of paired tokens.
Line 3: Line can be partitioned into sub-patterns to decrease the number of overlapping sets of paired tokens.
X: Z :X Y: A :Y
       ^
  Possible partition point
Line 4: Line can be rearranged so as to merge references to Z, decreasing the number of paired tokens.
Done linting
```