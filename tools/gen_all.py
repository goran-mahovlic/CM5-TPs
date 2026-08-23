# -*- coding: utf-8 -*-
"""Izgradi cijeli projekt iz izvornog repozitorija cm5-reveng.

Redoslijed je bitan: knjiznica -> ploca -> shema (cita plocu) -> README (cita plocu).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_symbols, gen_pcb, gen_sch, gen_readme
from gen_common import SRCPCB

if not os.path.exists(SRCPCB):
    raise SystemExit("nema izvorne ploce: %s\n"
                     "git clone --depth 1 https://github.com/schlae/cm5-reveng.git ~/.tmp/cm5-reveng" % SRCPCB)

for step, mod in (("simboli", gen_symbols), ("ploca", gen_pcb), ("shema", gen_sch), ("README", gen_readme)):
    print("\n== %s ==" % step)
    mod.main()
print("\ngotovo.")
