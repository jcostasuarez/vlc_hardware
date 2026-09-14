#!/usr/bin/env python3
"""Make a KiCad schematic project self-contained by vendoring embedded symbols.

For every symbol referenced by a project whose library nickname is not the
project-local library, this tool:

  1. extracts the exact symbol definition embedded in the schematic's
     ``lib_symbols`` cache,
  2. appends it (renamed, without library prefix) to the project-local
     ``.kicad_sym`` symbol library,
  3. repoints the embedded symbol name and every ``lib_id`` reference to the
     project-local library.

Symbol geometry, pins, units and properties are copied verbatim, so the
schematic is unchanged visually and electrically.  ERC symbol-library parity
warnings disappear because the project now ships the exact copy the schematic
was drawn with.

Usage:
    vendor_symbols.py <project-dir> --library-nick <nick> --library-file <path.kicad_sym> [--write]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_netlists import parse, children, value  # noqa: E402


def _scalar(node):
    if isinstance(node, tuple):
        return '"' + node[1].replace('\\', '\\\\').replace('"', '\\"') + '"'
    return node


def sexpr(node, indent=0):
    """Serialize keeping the head and leading scalars on one line (KiCad style)."""
    if isinstance(node, (tuple, str)):
        return _scalar(node)
    if not node:
        return '()'
    parts = [_scalar(node[0])]
    i = 1
    while i < len(node) and isinstance(node[i], (str, tuple)):
        parts.append(_scalar(node[i]))
        i += 1
    line = '(' + ' '.join(parts)
    if i == len(node):
        return line + ')'
    lines = [line]
    lines += ['\t' * (indent + 1) + sexpr(c, indent + 1) for c in node[i:]]
    lines.append('\t' * indent + ')')
    return '\n'.join(lines)


def top_level_symbols(sch_text):
    root = parse(sch_text)[0]
    libs = children(root, 'lib_symbols')
    return children(libs[0], 'symbol') if libs else []


def used_lib_ids(sch_text):
    root = parse(sch_text)[0]
    ids = []
    for sym in children(root, 'symbol'):
        lid = children(sym, 'lib_id')
        if lid:
            ids.append(value(lid[0]))
    return ids


def rename(node, name):
    out = list(node)
    out[1] = ('str', name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project_dir')
    ap.add_argument('--library-nick', required=True)
    ap.add_argument('--library-file', required=True)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    proj = Path(args.project_dir)
    nick = args.library_nick
    lib_file = Path(args.library_file)
    schematics = sorted(proj.rglob('*.kicad_sch'))
    if not schematics:
        raise SystemExit(f'no .kicad_sch under {proj}')

    # Collect symbols to vendor across all sheets, keyed by the target lib_id.
    to_vendor = {}   # new_full -> (old_full, node)
    renames = {}     # old_full -> new_full
    for sch in schematics:
        text = sch.read_text()
        embedded = {value(n): n for n in top_level_symbols(text)}
        for old_full in sorted(set(used_lib_ids(text))):
            lib, _, name = old_full.partition(':')
            if not lib or lib == nick:
                continue
            if old_full not in embedded:
                raise SystemExit(f'{sch}: {old_full} used but not in lib_symbols')
            new_full = f'{nick}:{name}'
            if new_full in to_vendor and to_vendor[new_full][0] != old_full:
                raise SystemExit(f'collision: {new_full} from '
                                 f'{to_vendor[new_full][0]} and {old_full}')
            to_vendor[new_full] = (old_full, embedded[old_full])
            renames[old_full] = new_full

    if not to_vendor:
        print(f'{proj}: already fully vendored into {nick}')
        return

    print(f'{proj}: {len(to_vendor)} symbol type(s) to vendor -> {nick}')
    for new_full, (old_full, _) in sorted(to_vendor.items()):
        print(f'  {old_full}  ->  {new_full}')

    if not args.write:
        return

    lib_text = lib_file.read_text() if lib_file.exists() else (
        '(kicad_symbol_lib\n\t(version 20231120)\n\t(generator "kicad_symbol_editor")\n'
        '\t(generator_version "8.0")\n)\n')
    for new_full, (_, node) in sorted(to_vendor.items()):
        name = new_full.split(':', 1)[1]
        if f'(symbol "{name}"' in lib_text:
            raise SystemExit(f'refusing to duplicate symbol "{name}" in {lib_file}')
        out = sexpr(rename(node, name))
        body = '\n'.join('\t' + line for line in out.splitlines())
        lib_text = lib_text.rstrip()
        if not lib_text.endswith(')'):
            raise SystemExit(f'unexpected end of {lib_file}')
        lib_text = lib_text[:-1].rstrip() + '\n' + body + '\n)\n'
    lib_file.parent.mkdir(parents=True, exist_ok=True)
    lib_file.write_text(lib_text)
    print(f'  wrote {lib_file}')

    for sch in schematics:
        text = sch.read_text()
        changed = 0
        for old_full, new_full in renames.items():
            if f'"{old_full}"' in text:
                text = text.replace(f'"{old_full}"', f'"{new_full}"')
                changed += 1
        if changed:
            sch.write_text(text)
            print(f'  repointed {changed} symbol reference(s) in {sch}')


if __name__ == '__main__':
    main()
