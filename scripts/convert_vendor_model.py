#!/usr/bin/env python3
"""Convert a PSpice/LTspice vendor macro-model into ngspice-compatible syntax.

Handles the constructs that appear in the TI (Green-Williams-Lis) macro-models
shipped with this repository:

  * ``.MODEL <n> VSWITCH ROFF/RON/VOFF/VON``  -> ``SW(Roff/Ron/Vt/Vh)``
  * ``.MODEL <n> ISWITCH ROFF/RON/IOFF/ION``  -> ``CSW(Roff/Ron/Ith/Ih)``
  * PSpice ``PWR(x,y)``                        -> ``((x)**(y))``
  * ``noiseless`` and ``T_ABS`` tokens         -> dropped/neutralised

Usage:
    convert_vendor_model.py <input.lib> <output.lib>
"""
import re
import sys
from pathlib import Path


def convert(text):
    def vswitch(m):
        n = m.group(1)
        ro, rn, vo, vn = (float(m.group(i)) for i in range(2, 6))
        return f'.MODEL {n} SW(Roff={ro:g} Ron={rn:g} Vt={(vo + vn) / 2:g} Vh={vn - vo:g})'

    def iswitch(m):
        n = m.group(1)
        ro, rn, io, ion = (float(m.group(i)) for i in range(2, 6))
        return f'.MODEL {n} CSW(Roff={ro:g} Ron={rn:g} It={(io + ion) / 2:g} Ih={ion - io:g})'

    text = re.sub(
        r'\.MODEL\s+(\S+)\s+VSWITCH\s+ROFF=(\S+)\s+RON=(\S+)\s+VOFF=(\S+)\s+VON=(\S+)',
        vswitch, text, flags=re.I)
    text = re.sub(
        r'\.MODEL\s+(\S+)\s+ISWITCH\s+ROFF=(\S+)\s+RON=(\S+)\s+IOFF=(\S+)\s+ION=(\S+)',
        iswitch, text, flags=re.I)
    text = re.sub(r'PWR\(([^,()]+),([^(),]+)\)', r'((\1)**(\2))', text, flags=re.I)
    text = re.sub(r'\bnoiseless\b', '', text, flags=re.I)
    text = re.sub(r'\bT_ABS=\S+', '', text, flags=re.I)
    return text


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    header = (f'* Converted to ngspice syntax by scripts/convert_vendor_model.py\n'
              f'* Source: {src}\n')
    dst.write_text(header + convert(src.read_text()))
    print(f'wrote {dst}')


if __name__ == '__main__':
    main()
