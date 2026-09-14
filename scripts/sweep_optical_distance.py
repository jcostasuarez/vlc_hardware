#!/usr/bin/env python3
"""Sweep the LED-photodiode distance in sim/system/link_channel.cir.

Writes the link magnitude at 50 MHz for several distances, showing the 1/D^2
behaviour of the line-of-sight optical channel.
"""
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_spice import NgSpice  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / 'sim/system/link_channel.cir'
TMP = ROOT / 'sim/system'  # keep relative model includes working
OUT = Path('/tmp/vlc_link_sweep')
DISTANCES = [0.1, 0.25, 0.5, 1.0, 2.0]
F = 50e6


def run(d):
    OUT.mkdir(parents=True, exist_ok=True)
    deck = TMP / '_link_sweep.cir'
    text = DECK.read_text()
    text = re.sub(r'\.param D=\S+', f'.param D={d}', text, count=1)
    deck.write_text(text)
    dat = OUT / 'link.dat'
    ng = NgSpice()
    ng.command('set ngbehavior=ltpsa')
    cwd = os.getcwd()
    try:
        os.chdir(TMP)
        ng.command('source ' + str(deck))
        ng.command('run')
        ng.command('set wr_singlescale')
        ng.command('set wr_vecnames')
        ng.command(f'wrdata {dat} v(out)')
    finally:
        os.chdir(cwd)
    rows = []
    for line in dat.read_text().splitlines():
        p = line.split()
        if len(p) >= 3:
            try:
                rows.append((float(p[0]), math.hypot(float(p[1]), float(p[2]))))
            except ValueError:
                continue
    rows.sort()
    return min(rows, key=lambda r: abs(math.log10(r[0]) - math.log10(F)))[1]


def main():
    print(f'{"D [m]":>6} {"|Vout/Vin| @50MHz":>18} {"rel. a D=0.5m":>14}')
    ref = None
    for d in DISTANCES:
        g = run(d)
        if abs(d - 0.5) < 1e-9:
            ref = g
        print(f'{d:>6g} {g:>18.4g} {"":>14}')
    # second pass for the relative column (ref known)
    print('\nRelative (ganancia / ganancia(D=0.5)):')
    for d in DISTANCES:
        g = run(d)
        print(f'{d:>6g} m: {g / ref:>8.3f}   (1/D^2 esperado {0.25 / (d * d):.3f})')


if __name__ == '__main__':
    try:
        main()
    finally:
        (ROOT / 'sim/system/_link_sweep.cir').unlink(missing_ok=True)
