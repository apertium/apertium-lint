# apertium-lint
linter for Apertium source files

This package provides the command-line tool `apertium-lint` which statically analyzes Apertium source files for potential issues.

The linter can be run on a single file, giving output like

```
$ apertium-lint modes.xml
modes.xml
Error (install-deps) on line 8: Debug modes using files in .deps/ should not be installed.
Error (install-deps) on line 25: Debug modes using files in .deps/ should not be installed.
Error (install-deps) on line 91: Debug modes using files in .deps/ should not be installed.
Errors: 3 Warnings: 0 Suggestions: 0 Nitpicks: 0
```

or it can be run without arguments, which will apply it to the entire current directory

```
$ apertium-lint
./modes.xml
Error (install-deps) on line 8: Debug modes using files in .deps/ should not be installed.
Error (install-deps) on line 25: Debug modes using files in .deps/ should not be installed.
Error (install-deps) on line 91: Debug modes using files in .deps/ should not be installed.
./paper/paper.tex
Warning (unnorm) on line 113: Line contains non-normalized characters.
Errors: 3 Warnings: 1 Suggestions: 0 Nitpicks: 0
```

With option `-s`, statistics about the files will also be gathered.

```
$ apertium-lint -s apertium-kir.kir.twol
apertium-kir.kir.twol
Input alphabet symbols:	169
Output alphabet symbols:	139
Rules:	61
Sets:	35
Alphabet symbol pairs:	169
Errors: 0 Warnings: 0 Suggestions: 0 Nitpicks: 0
```
