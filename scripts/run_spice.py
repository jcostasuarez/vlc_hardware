#!/usr/bin/env python3
"""Headless ngspice runner using the libngspice shipped with KiCad.

Runs one or more SPICE decks and writes an ngspice log plus optional ASCII
data files (via ``wrdata``).  No GUI and no external ngspice binary needed:
the KiCad runtime provides ``libngspice.so`` and this script drives it through
ctypes.

Usage:
    run_spice.py <deck.cir> [<deck2.cir> ...] [--outdir DIR]
                 [--vec v(out) ...] [--print expr ...]

Each deck is sourced with its own directory as the working directory, so
relative ``.include`` paths resolve against the deck location.  Results go to
``<outdir>/<deck>.log`` and ``<outdir>/<deck>.dat``.
"""
import argparse
import ctypes
import os
import sys
from pathlib import Path

CANDIDATES = [
    os.environ.get('NGSPICE_LIB'),
    '/tmp/.mount_backpl5CoXpo/resources/kicad/lib/libngspice.so.0',
    '/tmp/.mount_backpl5CoXpo/resources/kicad/lib/libngspice.so',
]


def load_library():
    tried = []
    for path in CANDIDATES:
        if not path:
            continue
        tried.append(path)
        try:
            return ctypes.CDLL(path), path
        except OSError:
            continue
    raise SystemExit('could not load libngspice; tried: ' + ', '.join(tried))


class NgSpice:
    SENDCHAR = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
    SENDSTAT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
    EXIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool,
                            ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
    SENDDATA = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
                                ctypes.c_int, ctypes.c_void_p)
    SENDINIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
    BG = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)

    def __init__(self):
        self.lib, self.path = load_library()
        self.out = []
        self.exited = False
        self.lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_Command.restype = ctypes.c_int
        self.lib.ngSpice_Init.argtypes = [self.SENDCHAR, self.SENDSTAT, self.EXIT,
                                          self.SENDDATA, self.SENDINIT, self.BG, ctypes.c_void_p]
        self.lib.ngSpice_Init.restype = ctypes.c_int
        self._cb = self.SENDCHAR(self._sendchar)
        self._cbs = self.SENDSTAT(self._sendstat)
        self._cbe = self.EXIT(self._exit)
        self._cbd = self.SENDDATA(lambda *a: 0)
        self._cbi = self.SENDINIT(lambda *a: 0)
        self._cbg = self.BG(lambda *a: 0)
        self.lib.ngSpice_Init(self._cb, self._cbs, self._cbe, self._cbd,
                              self._cbi, self._cbg, None)

    def _sendchar(self, text, ident, user):
        if text:
            self.out.append(text.decode('utf-8', errors='replace'))
        return 0

    def _sendstat(self, text, ident, user):
        if text:
            self.out.append(text.decode('utf-8', errors='replace'))
        return 0

    def _exit(self, status, immediate, quit, ident, user):
        self.exited = True
        return 0

    def command(self, cmd):
        rc = self.lib.ngSpice_Command(cmd.encode())
        return rc

    def text(self):
        return ''.join(self.out)


def run_deck(deck, outdir, vectors, noise=False):
    deck = Path(deck).resolve()
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    ng = NgSpice()
    try:
        os.chdir(deck.parent)
        ng.command('source ' + str(deck))
        ng.command('run')
        ng.command('set wr_singlescale')
        ng.command('set wr_vecnames')
        tag = f'{deck.parent.name}__{deck.stem}'
        if vectors:
            dat = outdir / (tag + '.dat')
            ng.command(f"wrdata {dat} {' '.join(vectors)}")
        if noise:
            spec = outdir / (tag + '.spectrum.dat')
            ng.command('setplot noise1')
            ng.command(f'wrdata {spec} onoise_spectrum inoise_spectrum')
            total = outdir / (tag + '.total.dat')
            ng.command('setplot noise2')
            ng.command(f'wrdata {total} onoise_total inoise_total')
    finally:
        os.chdir(cwd)
    log = outdir / (tag + '.log')
    log.write_text(ng.text())
    print(f'[{deck.name}] rc ok, log: {log}')
    return ng.text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('decks', nargs='+')
    ap.add_argument('--outdir', default='build/sim')
    ap.add_argument('--vec', action='append', default=[])
    ap.add_argument('--noise', action='store_true')
    args = ap.parse_args()
    failed = []
    for deck in args.decks:
        try:
            run_deck(deck, args.outdir, args.vec, noise=args.noise)
        except Exception as exc:  # noqa: BLE001
            failed.append((deck, exc))
            print(f'[{deck}] FAILED: {exc}', file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
