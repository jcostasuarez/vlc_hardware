#!/usr/bin/env python3
"""Summarise ngspice results in a directory into docs/sim/RESULTS.md."""
import glob
import math
import os
import sys
from datetime import date
from pathlib import Path


def read_cols(path, n):
    rows = []
    for line in Path(path).read_text().splitlines():
        p = line.split()
        if len(p) >= n:
            try:
                rows.append([float(x) for x in p[:n]])
            except ValueError:
                continue
    rows.sort(key=lambda r: r[0])
    return rows


def fmt(x):
    return f'{x:.3g}'


def tag_of(path):
    base = os.path.basename(path)[:-4]  # drop .dat
    for end in ('__ac', '_ac', '__tran', '_tran'):
        if base.endswith(end):
            return base[:-len(end)]
    return base


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/sim')
    lines = ['# Resultados de simulación (ngspice)', '',
             f'Generado por `scripts/summarize_sims.py` ({date.today().isoformat()}).',
             'Los supuestos de cada modelo están en `sim/README.md`.', '',
             '## Respuesta en frecuencia (AC)', '',
             '| Deck | Banda simulada | Pico | Frecuencia del pico | Ancho de banda a -3 dB |',
             '|---|---|---:|---:|---:|']
    for path in sorted(glob.glob(str(outdir / '*ac.dat'))):
        rows = read_cols(path, 3)
        if not rows:
            continue
        mags = [(f, math.hypot(re, im)) for f, re, im in rows]
        peak = max(mags, key=lambda r: r[1])
        bw = next((f for f, m in mags if f > peak[0] and m < peak[1] / math.sqrt(2)), None)
        band = f'{fmt(mags[0][0])}..{fmt(mags[-1][0])} Hz'
        lines.append(f'| `{tag_of(path)}` | {band} | {fmt(peak[1])} | '
                     f'{fmt(peak[0])} Hz | {fmt(bw) + " Hz" if bw else "> banda"} |')

    lines += ['', '## Transitorio', '', '| Deck | pico-pico |', '|---|---:|']
    for path in sorted(glob.glob(str(outdir / '*tran.dat'))):
        rows = read_cols(path, 2)
        if not rows:
            continue
        vals = [v for _, v in rows]
        lines.append(f'| `{tag_of(path)}` | {fmt(max(vals) - min(vals))} V |')

    lines += ['', '## Ruido', '',
              '| Deck | en salida @1 kHz | en salida @1 MHz | in referida @1 kHz | '
              'en salida rms (1k-500M) | in referida rms |',
              '|---|---:|---:|---:|---:|---:|']
    for spec in sorted(glob.glob(str(outdir / '*.spectrum.dat'))):
        rows = read_cols(spec, 3)
        if not rows:
            continue
        tag = os.path.basename(spec)[:-len('.spectrum.dat')]

        def at(freq):
            return min(rows, key=lambda r: abs(math.log10(r[0]) - math.log10(freq)))

        on_tot = in_tot = None
        total = outdir / (tag + '.total.dat')
        if total.exists():
            for v in read_cols(total, 3):
                on_tot, in_tot = v[0], v[2]
        label = tag.replace('__noise', '').replace('_noise', '')
        lines.append(f'| `{label}` | {fmt(at(1e3)[1])} V/√Hz | {fmt(at(1e6)[1])} V/√Hz | '
                     f'{fmt(at(1e3)[2])} A/√Hz | '
                     f'{fmt(on_tot) + " V" if on_tot else "—"} | '
                     f'{fmt(in_tot) + " A" if in_tot else "—"} |')

    Path('docs/sim').mkdir(parents=True, exist_ok=True)
    Path('docs/sim/RESULTS.md').write_text('\n'.join(lines) + '\n')
    print('wrote docs/sim/RESULTS.md')


if __name__ == '__main__':
    main()
