# -*- coding: utf-8 -*-
"""Generiraj shemu (root + 3 lista) koja je 1:1 sinkronizirana s generiranom plocom.

Podatci se citaju iz VEC generirane .kicad_pcb datoteke, pa se reference, vrijednosti,
footprinti i imena mreza ne mogu razici. Veza ide preko UUID putanja iz gen_common.U().
"""
import os, re, textwrap
from gen_common import OUT, PROJ, U, SHEETS, sheet_of, sheet_meta, find_block, extract
import tp_info

PCB = os.path.join(OUT, PROJ + ".kicad_pcb")
SYM = os.path.join(OUT, PROJ + ".kicad_sym")

GROUP_ORDER = ["PWR", "GND", "CTRL", "DBG", "I2C", "ETH", "USB", "LED", "MISC"]
GRID = 1.27  # raster sheme; svaka spojna tocka mora leziti na njemu
SYM_FOR_FP = {
    "cm5_tp_breakout:TestPoint_Pad_D1.0mm": "TestPoint",
    "cm5_tp_breakout:10164228-1001A1RLF":   "CM5_Conn_100P",
    "cm5_tp_breakout:CM5_MH":               "MountingHole",
}

# ---------------------------------------------------------------- ulazni podatci
def read_pcb():
    txt = open(PCB, encoding="utf-8").read()
    parts = []
    for m in re.finditer(r'^\s*\(footprint "', txt, re.M):
        start = txt.index("(footprint", m.start())
        r = find_block(txt, "(footprint ", start)
        blk = txt[r[0]:r[1]]
        fpid = re.search(r'\(footprint "([^"]+)"', blk).group(1)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        val = re.search(r'\(property "Value" "([^"]*)"', blk).group(1)
        pads = re.findall(r'\(pad "([^"]*)"[^\n]*\n(?:.*?\n)*?\s*\(net \d+ "([^"]*)"\)', blk)
        parts.append({"ref": ref, "val": val, "fpid": fpid, "pads": pads})
    return parts

def read_pins(symname):
    """Pinovi simbola iz knjiznice: [(broj, x, y, kut, duljina)] u lokalnim koordinatama."""
    txt = open(SYM, encoding="utf-8").read()
    blk = extract(txt, '(symbol "%s"' % symname)
    pins = []
    for m in re.finditer(r'\(pin \w+ \w+\s*\n\s*\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*\n\s*\(length ([\d.]+)\)'
                         r'(?:.*\n)*?\s*\(number "([^"]+)"', blk):
        x, y, rot, ln, num = m.groups()
        pins.append((num, float(x), float(y), int(rot), float(ln)))
    return pins

# ---------------------------------------------------------------- gradivni blokovi
def eff(size=1.27, justify=None, hide=False):
    j = "\n\t\t\t\t(justify %s)" % justify if justify else ""
    h = "\n\t\t\t\t(hide yes)" if hide else ""
    return "(effects\n\t\t\t\t(font\n\t\t\t\t\t(size %s %s)\n\t\t\t\t)%s%s\n\t\t\t)" % (size, size, j, h)

def prop(name, value, x, y, rot=0, size=1.27, hide=False, justify=None):
    v = value.replace("\\", "\\\\").replace('"', '\\"')
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %s)\n\t\t\t%s\n\t\t)'
            % (name, v, x, y, rot, eff(size, justify, hide)))

def symbol_inst(ref, libsym, val, fpid, x, y, uid, sheet_uuid, props_extra="", unit=1,
                in_bom="yes", ref_dy=-8.5, val_dy=-6.5):
    return "\n".join([
        "\t(symbol",
        '\t\t(lib_id "%s:%s")' % (PROJ, libsym),
        "\t\t(at %s %s 0)" % (x, y),
        "\t\t(unit %d)" % unit,
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom %s)" % in_bom,
        "\t\t(on_board yes)",
        "\t\t(dnp no)",
        '\t\t(uuid "%s")' % uid,
        prop("Reference", ref, x, y + ref_dy, size=1.27),
        prop("Value", val, x, y + val_dy, size=1.27),
        prop("Footprint", fpid, x, y, hide=True),
        prop("Datasheet", "~", x, y, hide=True),
        prop("Description", "", x, y, hide=True),
        props_extra,
        "\t\t(instances",
        '\t\t\t(project "%s"' % PROJ,
        '\t\t\t\t(path "/%s/%s"' % (U("sch:root"), sheet_uuid),
        '\t\t\t\t\t(reference "%s")' % ref,
        "\t\t\t\t\t(unit %d)" % unit,
        "\t\t\t\t)",
        "\t\t\t)",
        "\t\t)",
        "\t)",
    ]).replace("\n\n", "\n")

def wire(x1, y1, x2, y2, uid):
    return ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
            '\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)' % (x1, y1, x2, y2, uid))

def glabel(name, x, y, rot, uid, shape="passive"):
    justify = "left" if rot in (0, 90) else "right"
    return "\n".join([
        '\t(global_label "%s"' % name,
        "\t\t(shape %s)" % shape,
        "\t\t(at %s %s %s)" % (x, y, rot),
        "\t\t(fields_autoplaced yes)",
        "\t\t" + eff(1.27, justify),
        '\t\t(uuid "%s")' % uid,
        prop("Intersheetrefs", "${INTERSHEET_REFS}", x, y, hide=True),
        "\t)",
    ])

def net_label(name, x, y, rot, uid, global_nets=None):
    """Uvijek globalna oznaka.

    Lokalna oznaka (label) u KiCadu imenuje mrezu s prefiksom putanje lista
    ("/Test Points/+5V"), pa se ime vise ne bi poklapalo s onim na ploci.
    Globalna oznaka daje cisto ime, kakvo je i u izvornoj ploci.
    """
    return glabel(name, x, y, rot, uid)

def text_item(s, x, y, uid, size=1.0):
    v = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t%s\n\t\t(uuid "%s")\n\t)'
            % (v, x, y, eff(size, "left"), uid))

def sch_header(uid, paper, title, comment):
    return "\n".join([
        "(kicad_sch",
        "\t(version 20250114)",
        '\t(generator "cm5_tp_breakout_gen")',
        '\t(generator_version "9.0")',
        '\t(uuid "%s")' % uid,
        '\t(paper "%s")' % paper,
        "\t(title_block",
        '\t\t(title "%s")' % title,
        '\t\t(rev "1")',
        '\t\t(company "izvedeno iz schlae/cm5-reveng, CC BY-SA 4.0")',
        '\t\t(comment 1 "%s")' % comment,
        "\t)",
    ])

def lib_symbols(names):
    txt = open(SYM, encoding="utf-8").read()
    out = ["\t(lib_symbols"]
    for n in names:
        blk = extract(txt, '(symbol "%s"' % n)
        blk = blk.replace('(symbol "%s"' % n, '(symbol "%s:%s"' % (PROJ, n), 1)
        out.append("\t\t" + blk.replace("\n\t", "\n\t\t"))
    out.append("\t)")
    return "\n".join(out)

# ---------------------------------------------------------------- listovi
def wrap(s, w=34, maxlines=6):
    """Prelomi opis; ako ne stane, jasno oznaci da je skracen."""
    lines = textwrap.wrap(s, w)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1].rstrip(" ,;") + " …"
    return "\n".join(lines)

def cross_sheet_nets(parts):
    """Mreze cije su tocke na vise od jednog lista -- samo one trebaju globalnu oznaku."""
    where = {}
    for f in parts:
        sh = sheet_of(f["ref"])
        for _, net in f["pads"]:
            if net:
                where.setdefault(net, set()).add(sh)
    return {n for n, s in where.items() if len(s) > 1}

def build_testpoints(parts):
    key = "testpoints"
    name, fname, paper = sheet_meta(key)
    su = U("sheet:" + key)
    tps = [p for p in parts if p["ref"].upper().startswith("TP")]
    def sortkey(p):
        net = p["pads"][0][1]
        g = tp_info.lookup(net)[0]
        return (GROUP_ORDER.index(g), net, int(re.sub(r"\D", "", p["ref"]) or 0))
    tps.sort(key=sortkey)

    COLS, X0, DX, Y0, DY = 6, 33 * GRID, 72 * GRID, 35 * GRID, 29 * GRID
    gnets = cross_sheet_nets(parts)
    body = []
    for i, p in enumerate(tps):
        col, row = i // 10, i % 10
        x, y = X0 + col * DX, Y0 + row * DY
        net = p["pads"][0][1]
        grp, volt, desc = tp_info.lookup(net)
        uid = U("sym:" + p["ref"])
        body.append(symbol_inst(p["ref"], "TestPoint", p["val"], p["fpid"], x, y, uid, su,
                                props_extra=prop("Description", desc, x, y, hide=True)))
        body.append(wire(x, y, x, y + 5.08, U("w:" + p["ref"])))
        body.append(net_label(net, x, y + 5.08, 0, U("gl:" + p["ref"]), gnets))
        cap = "%s | %s | %s" % (tp_info.GROUPS[grp], volt, desc)
        body.append(text_item(wrap(cap), x - 2.5, y + 12.7, U("txt:" + p["ref"]), 1.0))

    hdr = sch_header(su, paper, "CM5 Test Point Breakout — test-točke",
                     "58 test-točaka na donjem sloju modula; opis signala uz svaku točku")
    intro = text_item(
        "TEST-TOČKE CM5 MODULA (58 komada, sve na donjem sloju, pad promjera 1,0 mm)\n"
        "Poredane po skupini: napajanje, masa, upravljanje, JTAG/UART, I2C, Ethernet, USB, svjetiljke, ostalo.\n"
        "Ime u oznaci jest ime mreže na ploči; puna je tablica u README.md.",
        20, 20, U("txt:tp_intro"), 2.0)
    return "\n".join([hdr, lib_symbols(["TestPoint"]), intro] + body + ["\t(embedded_fonts no)", ")"]) + "\n"

def build_connectors(parts):
    key = "cm5_connectors"
    name, fname, paper = sheet_meta(key)
    su = U("sheet:" + key)
    pins = read_pins("CM5_Conn_100P")
    body = []
    gnets = cross_sheet_nets(parts)
    for ref, (X, Y) in (("J3", (94 * GRID, 116 * GRID)), ("J4", (237 * GRID, 116 * GRID))):
        p = [q for q in parts if q["ref"] == ref][0]
        padnet = {}
        for pad, net in p["pads"]:
            padnet.setdefault(pad, net)
        uid = U("sym:" + ref)
        body.append(symbol_inst(ref, "CM5_Conn_100P", p["val"], p["fpid"], X, Y, uid, su,
                                ref_dy=-70.0, val_dy=-67.0))
        for num, px, py, rot, ln in pins:
            gx, gy = X + px, Y - py
            net = padnet.get(num, "")
            if not net:
                continue
            if px < 0:                      # lijevi stupac, pin gleda udesno
                ex, ey, ang = gx - 3.81, gy, 180
            elif px > 0:                    # desni stupac
                ex, ey, ang = gx + 3.81, gy, 0
            else:                           # mehanicki pin 0 ispod tijela
                ex, ey, ang = gx, gy + 3.81, 270
            body.append(wire(gx, gy, ex, ey, U("w:%s.%s" % (ref, num))))
            body.append(net_label(net, ex, ey, ang, U("gl:%s.%s" % (ref, num)), gnets))
    hdr = sch_header(su, paper, "CM5 Test Point Breakout — konektori modula",
                     "J3 i J4: dva 100-pinska konektora modula; imena mreža istovjetna izvorniku")
    intro = text_item(
        "KONEKTORI CM5 MODULA prema nosivoj ploči (Amphenol 10164228-1001A1RLF, 2 × 100 nožica + 4 mehanička pada)\n"
        "J3 je donji red modula, J4 gornji. Nožica \"0\" objedinjuje četiri mehanička pada (masa).\n"
        "Imena mreža preuzeta su iz izvorne sheme; test-točka koja dijeli mrežu s nožicom vidljiva je preko istoimene oznake.",
        20, 20, U("txt:conn_intro"), 2.0)
    return "\n".join([hdr, lib_symbols(["CM5_Conn_100P"]), intro] + body + ["\t(embedded_fonts no)", ")"]) + "\n"

def build_mechanical(parts):
    key = "mechanical"
    name, fname, paper = sheet_meta(key)
    su = U("sheet:" + key)
    hs = sorted([p for p in parts if p["ref"].upper().startswith("H")], key=lambda p: p["ref"])
    body = []
    for i, p in enumerate(hs):
        x, y = 47 * GRID + i * 36 * GRID, 70 * GRID
        body.append(symbol_inst(p["ref"], "MountingHole", p["val"], p["fpid"], x, y,
                                U("sym:" + p["ref"]), su, in_bom="no"))
    hdr = sch_header(su, paper, "CM5 Test Point Breakout — mehanika",
                     "Četiri rupe za pričvršćenje, raspored 48 × 33 mm kao na CM5 modulu")
    intro = text_item(
        "RUPE ZA PRIČVRŠĆENJE (4 komada)\n"
        "Raspored odgovara CM5 modulu: 48,0 mm × 33,0 mm, središta 3,5 mm od ruba ploče 55 × 40 mm.\n"
        "Rupe nisu električki spojene (simbol nema nožicu), pa ne ulaze u popis mreža.",
        20, 25, U("txt:mech_intro"), 2.0)
    return "\n".join([hdr, lib_symbols(["MountingHole"]), intro] + body + ["\t(embedded_fonts no)", ")"]) + "\n"

def build_root():
    ru = U("sch:root")
    out = [sch_header(ru, "A4", "CM5 Test Point Breakout",
                      "Izvedeno iz obratno projektiranoga CM5 modula (schlae/cm5-reveng)"),
           "\t(lib_symbols\n\t)"]
    geom = [(20.0, 40.0, 70.0, 25.0), (105.0, 40.0, 70.0, 25.0), (190.0, 40.0, 70.0, 25.0)]
    for (key, name, fname, _), (x, y, w, h), page in zip(SHEETS, geom, ("2", "3", "4")):
        su = U("sheet:" + key)
        out.append("\n".join([
            "\t(sheet",
            "\t\t(at %s %s)" % (x, y),
            "\t\t(size %s %s)" % (w, h),
            "\t\t(exclude_from_sim no)",
            "\t\t(in_bom yes)",
            "\t\t(on_board yes)",
            "\t\t(dnp no)",
            "\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)",
            "\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)",
            '\t\t(uuid "%s")' % su,
            prop("Sheetname", name, x, y - 1.2, justify="left bottom"),
            prop("Sheetfile", fname, x, y + h + 1.2, justify="left top"),
            "\t\t(instances",
            '\t\t\t(project "%s"' % PROJ,
            '\t\t\t\t(path "/%s"' % ru,
            '\t\t\t\t\t(page "%s")' % page,
            "\t\t\t\t)",
            "\t\t\t)",
            "\t\t)",
            "\t)",
        ]))
    out.append(text_item(
        "CM5 TEST POINT BREAKOUT\n"
        "Sadrži samo ono što treba za mjerenje na modulu Raspberry Pi Compute Module 5:\n"
        "  • 58 test-točaka s donjeg sloja (list Test Points),\n"
        "  • oba 100-pinska konektora modula, J3 i J4 (list CM5 Connectors),\n"
        "  • četiri rupe za pričvršćenje (list Mechanical).\n"
        "Geometrija je preuzeta 1:1 iz izvorne ploče, pa se položaji poklapaju s pravim modulom.\n"
        "Vodovi, zone i ostale sastavnice izostavljeni su; mreže koje spajaju više elemenata\n"
        "vidljive su kao nespojene veze i u ovome su projektu namjerno neusmjerene.\n"
        "Izvor: github.com/schlae/cm5-reveng (CC BY-SA 4.0), Tube Time. Opis svih točaka: README.md",
        20, 90, U("txt:root_intro"), 1.6))
    out.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)')
    out.append("\t(embedded_fonts no)")
    out.append(")")
    return "\n".join(out) + "\n"

def main():
    parts = read_pcb()
    files = {
        PROJ + ".kicad_sch": build_root(),
        "testpoints.kicad_sch": build_testpoints(parts),
        "cm5_connectors.kicad_sch": build_connectors(parts),
        "mechanical.kicad_sch": build_mechanical(parts),
    }
    for fn, content in files.items():
        path = os.path.join(OUT, fn)
        open(path, "w", encoding="utf-8").write(content)
        print("zapisano: %-32s %6.1f kB" % (fn, os.path.getsize(path) / 1024))

if __name__ == "__main__":
    main()
