# -*- coding: utf-8 -*-
"""Zajednicki dio generatora projekta cm5_tp_breakout."""
import os, re, uuid

SRC   = "/home/klaudio/.tmp/cm5-reveng"
OUT   = "/home/klaudio/app/cm5_tp_breakout"
PROJ  = "cm5_tp_breakout"
SRCPCB = os.path.join(SRC, "CM5RevEng.kicad_pcb")

# Deterministicki UUID-ovi: isti ulaz -> isti projekt (bez slucajnosti).
_NS = uuid.UUID("6f1c0a3e-0d5b-5f77-9a41-2b6e5c7d8e90")
def U(key):
    return str(uuid.uuid5(_NS, PROJ + ":" + key))

# Mreze bez smislenog imena u izvorniku -> citljivo ime u novom projektu.
NET_RENAME = {
    "Net-(TP22-Pad1)":  "PMIC_U5_PIN48",
    "Net-(U10A-ON1)":   "PWRSW_U10_ON",
    "Net-(U4-VREG)":    "ETHPHY_U4_VREG",
}

def short_net(n):
    """Skini hijerarhijsku putanju i primijeni preimenovanja."""
    if not n:
        return n
    s = n.rsplit("/", 1)[-1] if n.startswith("/") else n
    return NET_RENAME.get(s, s)

def find_block(text, header, start=0):
    """(pocetak, kraj) uravnotezenog bloka koji pocinje s 'header'; svjestan navodnika."""
    i = text.find(header, start)
    if i < 0:
        return None
    depth, j, instr, esc = 0, i, False, False
    while j < len(text):
        c = text[j]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return (i, j + 1)
        j += 1
    raise ValueError("neuravnotezene zagrade za " + header)

def extract(text, header):
    r = find_block(text, header)
    return text[r[0]:r[1]] if r else None

def dedent_block(s, tabs=2):
    """Blok izvucen iz .kicad_sch ima uvlaku izvorne datoteke; poravnaj na zadanu razinu."""
    lines = s.split("\n")
    out = [lines[0]]
    for ln in lines[1:]:
        out.append(("\t" * tabs) + ln.lstrip("\t"))
    return "\n".join(out)

# --- raspored po listovima sheme (dijele ga i generator sheme i generator ploce) ---
SHEETS = [
    ("testpoints",      "Test Points",     "testpoints.kicad_sch",      "A2"),
    ("cm5_connectors",  "CM5 Connectors",  "cm5_connectors.kicad_sch",  "A3"),
    ("mechanical",      "Mechanical",      "mechanical.kicad_sch",      "A4"),
]

def sheet_of(ref):
    u = ref.upper()
    if u.startswith("TP"): return "testpoints"
    if u in ("J3", "J4"):  return "cm5_connectors"
    if u.startswith("H"):  return "mechanical"
    raise KeyError(ref)

def sheet_meta(key):
    for k, name, fname, paper in SHEETS:
        if k == key:
            return name, fname, paper
    raise KeyError(key)

def pcb_path(ref):
    """Putanja koju footprint u .kicad_pcb mora nositi: /<uuid lista>/<uuid simbola>."""
    return "/%s/%s" % (U("sheet:" + sheet_of(ref)), U("sym:" + ref))

# Footprinti se sele u knjiznicu ovog projekta (izvorne knjiznice nema u repou).
FP_REMAP = {
    "TestPoint:TestPoint_Pad_D1.0mm": "cm5_tp_breakout:TestPoint_Pad_D1.0mm",
    "Conn:10164228-1001A1RLF":        "cm5_tp_breakout:10164228-1001A1RLF",
    "Conn:CM5_MH":                    "cm5_tp_breakout:CM5_MH",
}
