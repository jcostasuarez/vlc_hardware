#!/usr/bin/env python3
"""Parse kicadsexpr netlists and print per-board connector/power summaries."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NETS = ROOT / 'build/review/netlists'

POWER = re.compile(
    r'^(GND|GNDA?|AGND|VCC|VDD|V\+|V-|3V3|3\.3V|5V|5\.0V|Vdc|Vout|Vin|VBUS|VCC_.*|\+.*V|-.*V)$',
    re.I,
)
CONN = re.compile(r'^(J|JP|P|TP|U?J)\d')


def tokenize(text):
    token = ''
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                token += ch if ch in ('"', '\\') else '\\' + ch
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                yield ('str', token)
                token, in_string = '', False
            else:
                token += ch
        elif ch == '"':
            in_string = True
            token = ''
            escaped = False
        elif ch in '()':
            if token:
                yield ('atom', token)
                token = ''
            yield (ch, ch)
        elif ch.isspace():
            if token:
                yield ('atom', token)
                token = ''
        else:
            token += ch
    if token:
        yield ('atom', token)


def parse(text):
    stack = [[]]
    for kind, value in tokenize(text):
        if kind == '(':
            stack.append([])
        elif kind == ')':
            node = stack.pop()
            stack[-1].append(node)
        elif kind == 'str':
            stack[-1].append(('str', value))
        elif kind == 'atom':
            stack[-1].append(value)
    return stack[0]


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def value(node):
    return node[1][1] if len(node) > 1 and isinstance(node[1], tuple) else ''


def parse_netlist(text):
    root = parse(text)[0]
    comps = {}
    for section in children(root, 'components'):
        for comp in children(section, 'comp'):
            ref = value(children(comp, 'ref')[0])
            val = value(children(comp, 'value')[0])
            fp = value(children(comp, 'footprint')[0])
            comps[ref] = {'value': val, 'footprint': fp}

    nets = {}
    net_root = children(root, 'nets')
    if net_root:
        for net in children(net_root[0], 'net'):
            name = value(children(net, 'name')[0])
            nodes = []
            for node in children(net, 'node'):
                ref = value(children(node, 'ref')[0])
                pin = value(children(node, 'pin')[0])
                pf = children(node, 'pinfunction')
                nodes.append((ref, pin, value(pf[0]) if pf else ''))
            nets[name] = nodes
    return comps, nets


def main():
    for path in sorted(NETS.glob('*.net')):
        comps, nets = parse_netlist(path.read_text())
        print(f'\n### {path.stem} ({len(comps)} comps, {len(nets)} nets)')
        print('Connectors:')
        for ref in sorted(k for k in comps if CONN.match(k)):
            print(f'  {ref:6} {comps[ref]["value"][:40]:40} {comps[ref]["footprint"]}')
        print('Power nets:')
        for name, nodes in sorted(nets.items()):
            if POWER.match(name) or name.startswith('Net-(J'):
                refs = sorted({r for r, _, _ in nodes})
                print(f'  {name:20} -> {", ".join(refs)}')


if __name__ == '__main__':
    main()
