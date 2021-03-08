#!/usr/bin/env python3

from tree_sitter import Language, Parser
from collections import defaultdict

def text(node, contents, offset=0):
    return contents[node.start_byte-offset:node.end_byte-offset].decode('utf-8')

def get_side(node, count):
    parts = ''
    for c in node.children:
        if c.type == 'colon':
            parts += ':'
        elif c.type == count:
            parts += 's'
    if parts == ':s':
        return 'right'
    elif parts == 's:':
        return 'left'
    else:
        return 'both'

def examine_pattern_line(line, line_string): # Node, bytes
    toks = [] # (name, side)
    line_number = line.start_point[0]+1
    offset = line.start_byte
    for tok in line.children:
        if tok.type == '\n' or tok.type == 'comment':
            continue
        if tok.type != 'pattern_token':
            toks.append(('?', 'both'))
            continue
        for ch in tok.children:
            if ch.type in ['left_sieve', 'right_sieve']:
                toks.append(('<>', 'both'))
                break
            elif ch.type == 'anonymous_lexicon':
                toks.append(('[]', get_side(ch.children[1], 'lexicon_string')))
                break
            elif ch.type == 'anonymous_pattern':
                toks.append(('()', 'both'))
                break
            else:
                name = ''
                for n in tok.children:
                    if n.type == 'lexicon_reference':
                        name = text(n.children[0], line_string, offset)
                        break
                toks.append((name, get_side(tok, 'lexicon_reference')))
                break
    has_matched = False
    matched = defaultdict(list)
    special = ['<>', '()', '[]', '?']
    matched_names = set()
    for i, t in enumerate(toks):
        matched[t[0]].append(i)
        if t[0] not in special and len(matched[t[0]]) > 1:
            has_matched = True
            matched_names.add(t[0])
    if has_matched:
        handled = []
        for name in matched_names:
            if len(matched[name]) == 2:
                l1, l2 = matched[name]
                if (toks[l1][1] == 'left' and toks[l2][1] == 'right') or \
                   (toks[l1][1] == 'right' and toks[l2][1] == 'left'):
                    if l2 == l1 + 1:
                        print('Line %s: References to %s can be merged, decreasing the number of paired tokens.' % (line_number, name))
                        handled.append(name)
                        continue
                    for i in range(l1+1,l2):
                        if toks[i][1] == 'both':
                            break
                    else:
                        print('Line %s: Line can be rearranged so as to merge references to %s, decreasing the number of paired tokens.' % (line_number, name))
                        handled.append(name)
                        continue
        todo = [n for n in matched_names if n not in handled]
        for i in range(len(toks)):
            left = []
            right = []
            failed = False
            for tk in todo:
                if all(n <= i for n in matched[tk]):
                    left.append(tk)
                elif all(n > i for n in matched[tk]):
                    right.append(tk)
                else:
                    failed = True
                    break
            if failed:
                continue
            if len(left) > 0 and len(right) > 0:
                print('Line %s: Line can be partitioned into sub-patterns to decrease the number of overlapping sets of paired tokens.' % line_number)
                print(line_string.decode('utf-8'), end='')
                indent = line.children[i].end_byte - offset
                # TODO: this doesn't properly account for diacritics etc
                print(' '*indent + '^')
                print('  Possible partition point')
                return

def check_tags(tree, contents):
    tag_set = defaultdict(list)
    tag_use = defaultdict(list)
    def search(node):
        nonlocal tag_set, tag_use, contents
        for n in node.children:
            search(n)
        if node.type == 'tag_setting':
            for n in node.children:
                if n.type == 'tag':
                    tag_set[text(n,contents)].append(n.start_point[0]+1)
        elif node.type in ['tag_filter', 'tag_distribution']:
            for n in node.children:
                if n.type == 'tag':
                    tag_use[text(n,contents)].append(n.start_point[0]+1)
    search(tree)
    for n in tag_set:
        if n not in tag_use:
            s = 'line'
            if len(tag_set[n]) > 1:
                s += 's'
            s += ' ' + ', '.join(str(x) for x in tag_set[n])
            print("Tag '%s' set but never filtered by on %s." % (n, s))
    for n in tag_use:
        if n not in tag_set:
            s = 'line'
            if len(tag_set[n]) > 1:
                s += 's'
            s += ' ' + ', '.join(str(x) for x in tag_set[n])
            print("Tag '%s' filtered by but never set on %s." % (n, s))

def stats(tree, contents):
    cur_name = ''
    lex_counts = defaultdict(lambda: 0)
    pat_counts = defaultdict(lambda: 0)
    def count_anon(node):
        if node.type == 'anonymous_lexicon':
            return 1
        else:
            return sum(count_anon(x) for x in node.children)
    for node in tree.children:
        if node.type == 'pattern_block':
            cur_name = ''
            for ch in node.children:
                if ch.type == 'identifier':
                    cur_name = text(ch,contents)
                elif ch.type == 'pattern_line':
                    pat_counts[cur_name] += 1
                    lex_counts[''] += count_anon(ch)
        elif node.type == 'lexicon_block':
            for ch in node.children:
                if ch.type == 'identifier':
                    cur_name = text(ch,contents)
                elif ch.type == 'lexicon_line':
                    lex_counts[cur_name] += 1
    return lex_counts, pat_counts
    
def lint(filename, lang):
    print('Linting %s' % filename)
    p = Parser()
    p.set_language(lang)
    with open(filename, 'rb') as f:
        contents = f.read()
        tree = p.parse(contents)
        for block in tree.root_node.children:
            if block.type == 'pattern_block':
                for line in block.children:
                    if line.type == 'pattern_line':
                        s = contents[line.start_byte:line.end_byte]
                        examine_pattern_line(line, s)

        check_tags(tree.root_node, contents)

        lstats, pstats = stats(tree.root_node, contents)

        total = 0
        for l in sorted(lstats.keys()):
            if not l: continue
            print('%s: %s' % (l, lstats[l]))
            total += lstats[l]
        print('All anonymous lexicons: %s' % (lstats['']))
        total += lstats['']
        print('=====')
        print('Number of lexicons: %s' % len(lstats))
        print('Total number of lexicon entries: %s\n' % total)

        total = 0
        for p in sorted(pstats.keys()):
            if not p: continue
            print('%s: %s' % (p, pstats[p]))
            total += pstats[p]
        print('Toplevel pattern: %s' % (pstats['']))
        total += pstats['']
        print('=====')
        print('Number of patterns: %s' % len(pstats))
        print('Total number of pattern lines: %s' % total)
    print('Done linting')
