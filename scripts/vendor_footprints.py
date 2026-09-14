#!/usr/bin/env python3
"""Make a KiCad board project self-contained by vendoring its embedded footprints.

For every footprint instance on the board whose library nickname is not already
the project-local library, this tool:

  1. extracts the footprint block embedded in the .kicad_pcb,
  2. canonicalizes it (position 0,0, instance rotation removed) and writes it as
     a library footprint into the project-local .pretty library,
  3. repoints the board footprint's FPID to the project-local library.

Geometry, pads, nets, zones and text are copied verbatim (the comparison used by
KiCad DRC ignores nets/teardrops and instance transforms), so the board is
electrically and mechanically unchanged.  Library version-drift and
"footprint not found" DRC warnings disappear because the project now ships the
exact copy the board was validated with.

Usage:
    vendor_footprints.py <board.kicad_pcb> --library-nick <nick> --library-dir <dir> [--write]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_netlists import parse  # noqa: E402

ROOT_DROP = {'path', 'sheetname', 'sheetfile', 'tstamp', 'uuid', 'locked', 'placed'}
PROP_KEEP = {'Reference', 'Value', 'Footprint', 'Datasheet', 'Description'}
PROP_DROP = {'uuid', 'unlocked'}
PAD_DROP = {'net', 'pintype', 'pinfunction', 'teardrops', 'uuid'}


def sexpr(node, indent=0):
    if isinstance(node, tuple):
        return '"' + node[1].replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(node, str):
        return node
    if not node:
        return '()'
    head = node[0] if isinstance(node[0], str) else sexpr(node[0])
    rest = node[1:]
    if all(isinstance(c, str) or isinstance(c, tuple) for c in rest):
        inline = ' '.join(sexpr(c) for c in rest)
        return '(' + head + ((' ' + inline) if inline else '') + ')'
    lines = ['(' + head]
    lines += ['\t' * (indent + 1) + sexpr(c, indent + 1) for c in rest]
    lines.append('\t' * indent + ')')
    return '\n'.join(lines)


def fmt_angle(a):
    a %= 360
    if abs(a - round(a)) < 1e-9:
        return str(int(round(a)))
    return f'{a:g}'


def derotate(node, ang):
    if isinstance(node, list):
        if node and node[0] == 'at' and len(node) > 3:
            return node[:3] + [fmt_angle(float(node[3]) - ang)]
        return [derotate(c, ang) for c in node]
    return node


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def set_property_value(node, name, value):
    for prop in children(node, 'property'):
        if len(prop) > 1 and isinstance(prop[1], tuple) and prop[1][1] == name:
            prop[2] = ('str', value)


def fp_blocks(text):
    root = parse(text)[0]
    out = []
    for node in root:
        if isinstance(node, list) and node and node[0] == 'footprint':
            fpid = node[1][1] if len(node) > 1 and isinstance(node[1], tuple) else None
            out.append((fpid, node))
    return out


def instance_angle(node):
    at = children(node, 'at')
    if at and len(at[0]) > 3:
        return float(at[0][3])
    return 0.0


def to_library(node, name):
    ang = instance_angle(node)
    out = ['footprint', ('str', name),
           ['version', '20240108'],
           ['generator', ('str', 'pcbnew')],
           ['generator_version', ('str', '8.0')]]
    for child in node[1:]:
        if not isinstance(child, list) or not child:
            continue
        head = child[0]
        if head in ROOT_DROP or head in ('at',):
            continue
        if head == 'property':
            pname = child[1][1] if len(child) > 1 and isinstance(child[1], tuple) else child[1]
            if pname not in PROP_KEEP and not pname.startswith('ki_'):
                continue
            child = [c for c in child
                     if not (isinstance(c, list) and c and c[0] in PROP_DROP)]
        elif head == 'pad':
            child = [c for c in child
                     if not (isinstance(c, list) and c and c[0] in PAD_DROP)]
        out.append(derotate(child, ang))
    set_property_value(out, 'Reference', 'REF**')
    set_property_value(out, 'Value', name)
    set_property_value(out, 'Footprint', name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board')
    ap.add_argument('--library-nick', required=True)
    ap.add_argument('--library-dir', required=True)
    ap.add_argument('--project-dir',
                    help='Project directory; all *.kicad_sch under it are kept in sync')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    board_path = Path(args.board)
    text = board_path.read_text()
    lib_dir = Path(args.library_dir)
    nick = args.library_nick

    plans = {}
    seen_name = {}
    for fpid, node in fp_blocks(text):
        if fpid is None:
            continue
        lib, _, name = fpid.partition(':')
        if lib == nick:
            continue
        if name in seen_name and seen_name[name] != fpid:
            raise SystemExit(f'name collision in {board_path.name}: {name} used by '
                             f'{seen_name[name]} and {fpid}')
        seen_name[name] = fpid
        plans.setdefault(fpid, (name, node))
    plans = [(fpid, name, node) for fpid, (name, node) in plans.items()]

    if not plans:
        print(f'{board_path.name}: already fully vendored into {nick}')
        return

    print(f'{board_path.name}: {len(plans)} footprint type(s) to vendor -> {nick}')
    for fpid, name, _ in plans:
        print(f'  {fpid}  ->  {nick}:{name}')

    if not args.write:
        return

    lib_dir.mkdir(parents=True, exist_ok=True)
    for fpid, name, node in plans:
        dest = lib_dir / f'{name}.kicad_mod'
        if dest.exists():
            raise SystemExit(f'refusing to overwrite existing {dest}')
        dest.write_text(sexpr(to_library(node, name)) + '\n')
        print(f'  wrote {dest}')

    new_text = text
    for fpid, name, _ in plans:
        new_text = new_text.replace(f'"{fpid}"', f'"{nick}:{name}"')
    board_path.write_text(new_text)
    print(f'  repointed FPIDs in {board_path}')

    if args.project_dir:
        for sch in sorted(Path(args.project_dir).rglob('*.kicad_sch')):
            sch_text = sch.read_text()
            changed = 0
            for fpid, name, _ in plans:
                if f'"{fpid}"' in sch_text:
                    sch_text = sch_text.replace(f'"{fpid}"', f'"{nick}:{name}"')
                    changed += 1
            if changed:
                sch.write_text(sch_text)
                print(f'  synced {changed} footprint field(s) in {sch}')


if __name__ == '__main__':
    main()
