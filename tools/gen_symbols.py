# -*- coding: utf-8 -*-
"""Sastavi cm5_tp_breakout.kicad_sym iz simbola ugradenih u izvorne sheme."""
import os, re
from gen_common import SRC, OUT, PROJ, extract

WANT = [
    ("CM5RevEng.kicad_sch",  '(symbol "Connector:TestPoint"',              "TestPoint"),
    ("CM5RevEng.kicad_sch",  '(symbol "Mechanical:MountingHole"',          "MountingHole"),
    ("Connectors.kicad_sch", '(symbol "connectors:Conn_2Rows-100Pins"',    "CM5_Conn_100P"),
]

def reindent(block, base=1):
    lines = block.split("\n")
    out = [("\t" * base) + lines[0].lstrip("\t")]
    for ln in lines[1:]:
        stripped = ln.lstrip("\t")
        depth = len(ln) - len(stripped)
        out.append(("\t" * max(base, depth - 2 + base)) + stripped)
    return "\n".join(out)

def main():
    parts = []
    for fname, header, newname in WANT:
        txt = open(os.path.join(SRC, fname), encoding="utf-8").read()
        blk = extract(txt, header)
        if blk is None:
            raise SystemExit("nema simbola: " + header)
        # preimenuj glavu i sve interne jedinice (npr. TestPoint_1_1 -> NewName_1_1)
        oldfull = re.match(r'\(symbol "([^"]+)"', blk).group(1)
        oldbase = oldfull.split(":")[-1]
        blk = blk.replace('(symbol "%s"' % oldfull, '(symbol "%s"' % newname, 1)
        blk = re.sub(r'\(symbol "%s_(\d+_\d+)"' % re.escape(oldbase),
                     lambda m: '(symbol "%s_%s"' % (newname, m.group(1)), blk)
        blk = blk.replace('(property "Value" "%s"' % oldbase,
                          '(property "Value" "%s"' % newname, 1)
        parts.append(reindent(blk))
        print("  simbol:", oldfull, "->", newname, "(%d znakova)" % len(blk))

    out = ('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "cm5_tp_breakout")\n'
           '\t(generator_version "9.0")\n' + "\n".join(parts) + "\n)\n")
    path = os.path.join(OUT, PROJ + ".kicad_sym")
    open(path, "w", encoding="utf-8").write(out)
    print("zapisano:", path, os.path.getsize(path), "B")

if __name__ == "__main__":
    main()
