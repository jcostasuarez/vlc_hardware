#!/usr/bin/env python3
"""Sync PCB footprint fields and value to the schematic (netlist) so that the
KiCad "schematic parity" DRC test is clean.

The schematic/netlist is the source of truth: for every footprint property whose
name appears in the netlist component's fields (and for Value), the board value
is replaced by the exact netlist value.  Only the targeted field strings change;
the rest of the board file is untouched.

Usage:
    sync_schematic_parity.py --board <b.kicad_pcb> --netlist <n.net> [--write]
                             [--dnp-ref JP1 --set-dnp <sch.kicad_sch>]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_netlists import parse, children, value  # noqa: E402

SKIP = {'Reference', 'Footprint'}


def toks(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '(':
            yield ('open', i, i + 1, None)
            i += 1
        elif c == ')':
            yield ('close', i, i + 1, None)
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            start = i
            i += 1
            buf = ''
            while i < n:
                ch = text[i]
                if ch == '\\':
                    buf += text[i:i + 2]
                    i += 2
                elif ch == '"':
                    i += 1
                    break
                else:
                    buf += ch
                    i += 1
            yield ('str', start, i, buf)
        else:
            start = i
            while i < n and not text[i].isspace() and text[i] not in '()"':
                i += 1
            yield ('atom', start, i, text[start:i])


def build(text):
    root = []
    stack = [(None, root)]
    for kind, start, end, val in toks(text):
        if kind == 'open':
            node = ['list', start, None, []]
            stack[-1][1].append(node)
            stack.append((node, node[3]))
        elif kind == 'close':
            node, _ = stack.pop()
            if node is not None:
                node[2] = end
        else:
            stack[-1][1].append((kind, start, end, val))
    return root


def head(node):
    if isinstance(node, list) and node[3] and isinstance(node[3][0], tuple):
        return node[3][0][3]
    return None


def unescape(raw):
    out, i = '', 0
    while i < len(raw):
        if raw[i] == '\\' and i + 1 < len(raw):
            nxt = raw[i + 1]
            out += nxt if nxt in ('"', '\\') else '\\' + nxt
            i += 2
        else:
            out += raw[i]
            i += 1
    return out


def quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def netlist_components(path):
    root = parse(Path(path).read_text())[0]
    comps = {}
    for section in children(root, 'components'):
        for comp in children(section, 'comp'):
            ref = value(children(comp, 'ref')[0])
            val = value(children(comp, 'value')[0]) if children(comp, 'value') else ''
            fields = {}
            fsection = children(comp, 'fields')
            if fsection:
                for fld in children(fsection[0], 'field'):
                    names = children(fld, 'name')
                    if not names:
                        continue
                    idx = fld.index(names[0])
                    fv = ''
                    if idx + 1 < len(fld) and isinstance(fld[idx + 1], tuple):
                        fv = fld[idx + 1][1]
                    fields[value(names[0])] = fv
            comps[ref] = {'value': val, 'fields': fields}
    return comps


def top_children(text, root_head, child_head):
    out = []
    for root in build(text):
        if head(root) == root_head:
            out += [c for c in root[3] if head(c) == child_head]
    return out


def sync_board(board_path, netlist_path, write):
    text = Path(board_path).read_text()
    comps = netlist_components(netlist_path)
    edits = []
    checked = 0
    for node in top_children(text, 'kicad_pcb', 'footprint'):
        ref = None
        props = []
        for child in node[3]:
            if head(child) == 'property':
                name = child[3][1][3]
                if name == 'Reference':
                    ref = child[3][2][3]
                props.append((name, child[3][2]))
        comp = comps.get(ref)
        if not comp:
            continue
        for name, vleaf in props:
            if name in SKIP:
                continue
            new = comp['value'] if name == 'Value' else comp['fields'].get(name)
            if new is None:
                continue
            checked += 1
            cur = unescape(vleaf[3])
            if cur != new:
                edits.append((vleaf[1], vleaf[2], quote(new), ref, name, cur, new))
    edits.sort(key=lambda e: e[0], reverse=True)
    for start, end, q, ref, name, old, new in edits:
        text = text[:start] + q + text[end:]
    print(f'{Path(board_path).name}: {len(edits)} field(s) updated ({checked} compared)')
    for _, _, _, ref, name, old, new in reversed(edits):
        print(f'  {ref:5} {name:28} {old!r} -> {new!r}')
    if write and edits:
        Path(board_path).write_text(text)
    return len(edits)


def set_dnp(sch_path, ref, write):
    text = Path(sch_path).read_text()
    edits = []
    for node in top_children(text, 'kicad_sch', 'symbol'):
        is_target = False
        dnp = None
        for child in node[3]:
            if head(child) == 'property':
                if child[3][1][3] == 'Reference':
                    is_target = unescape(child[3][2][3]) == ref
            elif head(child) == 'dnp':
                dnp = child
        if is_target and dnp:
            vleaf = dnp[3][1]
            cur = unescape(vleaf[3])
            if cur != 'yes':
                edits.append((vleaf[1], vleaf[2], 'yes', cur))
    edits.sort(key=lambda e: e[0], reverse=True)
    for start, end, new, old in edits:
        text = text[:start] + new + text[end:]
    print(f'{Path(sch_path).name}: set dnp {ref} {old!r} -> yes' if edits
          else f'{Path(sch_path).name}: {ref} already dnp yes')
    if write and edits:
        Path(sch_path).write_text(text)
    return len(edits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board')
    ap.add_argument('--netlist')
    ap.add_argument('--dnp-ref')
    ap.add_argument('--set-dnp')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    if args.board and args.netlist:
        sync_board(args.board, args.netlist, args.write)
    if args.dnp_ref and args.set_dnp:
        set_dnp(args.set_dnp, args.dnp_ref, args.write)


if __name__ == '__main__':
    main()
