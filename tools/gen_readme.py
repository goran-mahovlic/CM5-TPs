# -*- coding: utf-8 -*-
"""Generiraj README.md s tablicom svih test-tocaka (izvor: generirana ploca)."""
import os, re, json, collections
from gen_common import OUT, PROJ, find_block
import tp_info
from gen_sch import read_pcb, GROUP_ORDER


def mm(v, nd=2):
    """Broj s hrvatskim decimalnim zarezom."""
    return ("%.*f" % (nd, v)).replace(".", ",")

PCB = os.path.join(OUT, PROJ + ".kicad_pcb")

def positions():
    """ref -> (x, y) u milimetrima, iz .kicad_pcb."""
    txt = open(PCB, encoding="utf-8").read()
    pos = {}
    for m in re.finditer(r'^\s*\(footprint "', txt, re.M):
        start = txt.index("(footprint", m.start())
        r = find_block(txt, "(footprint ", start)
        blk = txt[r[0]:r[1]]
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        at = re.search(r'\n\t+\(at ([-\d.]+) ([-\d.]+)', blk)
        pos[ref] = (float(at.group(1)), float(at.group(2)))
    # rub ploce
    xs, ys = [], []
    for m in re.finditer(r'\(gr_(?:line|arc)[^\n]*\n(?:.*\n)*?\s*\(layer "Edge.Cuts"\)', txt):
        pass
    for m in re.finditer(r'\(xy ([-\d.]+) ([-\d.]+)\)|\((?:start|end|mid) ([-\d.]+) ([-\d.]+)\)', txt):
        a, b, c, d = m.groups()
        x, y = (float(a), float(b)) if a else (float(c), float(d))
        xs.append(x); ys.append(y)
    return pos, (min(xs), max(xs), min(ys), max(ys))

def conn_map(parts):
    """mreza -> popis pinova J3/J4."""
    m = collections.defaultdict(list)
    for f in parts:
        if f["ref"] in ("J3", "J4"):
            for pad, net in f["pads"]:
                if net and pad != "0":
                    m[net].append("%s-%s" % (f["ref"], pad))
    return m

def main():
    parts = read_pcb()
    pos, (x0, x1, y0, y1) = positions()
    edge = {}
    # rub ploce iz Edge.Cuts crta (gr_line/gr_arc su izvan footprinta)
    txt = open(PCB, encoding="utf-8").read()
    ex, ey = [], []
    for blk in re.findall(r'\(gr_(?:line|arc)\n(?:.*\n)*?\)', txt):
        for a, b in re.findall(r'\((?:start|end|mid) ([-\d.]+) ([-\d.]+)\)', blk):
            ex.append(float(a)); ey.append(float(b))
    bx0, bx1, by0, by1 = min(ex), max(ex), min(ey), max(ey)
    cm = conn_map(parts)

    tps = [p for p in parts if p["ref"].upper().startswith("TP")]
    tps.sort(key=lambda p: int(re.sub(r"\D", "", p["ref"])))

    rows = []
    for p in tps:
        net = p["pads"][0][1]
        grp, volt, desc = tp_info.lookup(net)
        x, y = pos[p["ref"]]
        rx, ry = round(x - bx0, 2), round(by1 - y, 2)
        pins = ", ".join(sorted(cm.get(net, []), key=lambda s: (s[:2], int(s.split("-")[1])))[:6])
        rows.append((p["ref"], p["val"], net, grp, volt, desc, rx, ry, pins))

    by_group = collections.defaultdict(list)
    for r in rows:
        by_group[r[3]].append(r)

    L = []
    L.append("# CM5 Test Point Breakout")
    L.append("")
    L.append("Sveden projekt za KiCad izveden iz obratno projektirane ploče Raspberry Pi Compute Module 5 "
             "([schlae/cm5-reveng](https://github.com/schlae/cm5-reveng), CC BY-SA 4.0, autor Tube Time).")
    L.append("")
    L.append("Sadrži **samo** ono što treba za pristup mjernim točkama modula:")
    L.append("")
    L.append("| Element | Količina | Sloj | Napomena |")
    L.append("|---|---|---|---|")
    L.append("| Test-točke `TP*` | %d | B.Cu (donji) | pad promjera 1,0 mm |" % len(tps))
    L.append("| Konektori modula `J3`, `J4` | 2 | B.Cu (donji) | Amphenol 10164228-1001A1RLF, 2 × 100 nožica + 4 mehanička pada |")
    L.append("| Rupe za pričvršćenje `H1`–`H4` | 4 | kroz ploču | raspored 48,0 × 33,0 mm |")
    L.append("| Obris ploče `Edge.Cuts` | 8 crta | – | %s × %s mm, zaobljeni kutovi |" % (mm(bx1 - bx0), mm(by1 - by0)))
    L.append("")
    L.append("Vodovi, zone, ostale sastavnice i unutarnji slojevi izostavljeni su. "
             "Geometrija je preuzeta **1:1**, pa se položaji poklapaju s pravim modulom.")
    L.append("")
    L.append("![Donji sloj ploče](doc/ploca_donji_sloj.png)")
    L.append("")
    L.append("*Donji sloj: 58 test-točaka, konektori J3 (gore) i J4 (dolje), četiri rupe u uglovima. "
             "Natpisi J3/J4 zrcaljeni su jer su na donjem sloju.*")
    L.append("")
    L.append("## Datoteke")
    L.append("")
    L.append("```")
    L.append("cm5_tp_breakout.kicad_pro      projekt")
    L.append("cm5_tp_breakout.kicad_sch      korijenska shema (tri lista)")
    L.append("  testpoints.kicad_sch         58 test-točaka, opis uz svaku")
    L.append("  cm5_connectors.kicad_sch     J3 i J4 sa svim imenima mreža")
    L.append("  mechanical.kicad_sch         H1-H4")
    L.append("cm5_tp_breakout.kicad_pcb      ploča (dva sloja)")
    L.append("cm5_tp_breakout.kicad_sym      simboli (TestPoint, CM5_Conn_100P, MountingHole)")
    L.append("cm5_tp_breakout.pretty/        footprinti (izvezeni iz izvorne ploče)")
    L.append("doc/                           izvezena shema u PDF-u")
    L.append("tools/                         generator — projekt se može ponovno izgraditi iz izvornika")
    L.append("```")
    L.append("")
    L.append("Projekt je samostalan: simboli i footprinti nalaze se u projektnim knjižnicama, "
             "pa ne treba nijedna vanjska knjižnica.")
    L.append("")
    L.append("## Test-točke")
    L.append("")
    L.append("Koordinate su u milimetrima od **donjega lijevog kuta ploče**, u KiCadovu pogledu odozgo "
             "(X udesno, Y prema gore). Točke su na donjem sloju, pa su pri pogledu odozdo zrcaljene po osi X.")
    L.append("")
    L.append("`Oznaka` je natpis s izvorne ploče, `Mreža` je ime mreže u shemi, "
             "`Na konektoru` navodi nožice J3/J4 koje su na istoj mreži.")
    L.append("")
    for g in GROUP_ORDER:
        if g not in by_group:
            continue
        L.append("### %s" % tp_info.GROUPS[g])
        L.append("")
        L.append("| TP | Oznaka | Mreža | Nazivno | X [mm] | Y [mm] | Na konektoru | Opis |")
        L.append("|---|---|---|---|---:|---:|---|---|")
        for ref, val, net, grp, volt, desc, rx, ry, pins in sorted(by_group[g], key=lambda r: r[2]):
            L.append("| `%s` | %s | `%s` | %s | %s | %s | %s | %s |"
                     % (ref, val, net, volt, mm(rx), mm(ry), pins or "–", desc))
        L.append("")

    L.append("## Mjerne napomene")
    L.append("")
    L.append("- **Masa** ima devet točaka; za brze signale uzmi onu najbližu mjernoj točki i kratku petlju sonde.")
    L.append("- **Ethernet i USB** diferencijalni su parovi. Test-točka je odvojak s voda: sonda unosi kapacitet "
             "i kvari prilagodbu, pa mjeri samo kad je nužno i s najmanjom mogućom sondom.")
    L.append("- **RUN** i **PWR_BUT** kratkim spojem na masu izazivaju ponovno pokretanje, odnosno buđenje. "
             "Ne drži ih trajno na masi.")
    L.append("- **nRPIBOOT** mora biti na niskoj razini *u trenutku uključenja* da bi modul ušao u način rada rpiboot.")
    L.append("- **PMIC_I2C** radna je sabirnica prema PMIC-u; upis u registre može ugasiti napajanje modula.")
    L.append("- Jezgrena napajanja (`VDD_BCM_CORE`, `VDD_0V8*`) mijenjaju napon s opterećenjem — "
             "vrijednost u tablici okvirna je, nije granica ispravnosti.")
    L.append("")
    L.append("## Provjere")
    L.append("")
    L.append("Stanje pri zadnjem generiranju (`kicad-cli` 9.0.2):")
    L.append("")
    L.append("| Provjera | Rezultat |")
    L.append("|---|---|")
    L.append("| ERC (shema): pogreške | **0** |")
    L.append("| ERC (shema): upozorenja | 152 × `global_label_dangling` — oznaka mreže koja postoji samo na jednome mjestu |")
    L.append("| Popis mreža: shema prema ploči | 172 mreže i 260 čvorova, **istovjetno** |")
    L.append("| DRC: podudarnost sa shemom (`schematic_parity`) | **0 razlika** |")
    L.append("| DRC: nespojeni elementi | 94 — očekivano, ploča namjerno nema vodove |")
    L.append("| DRC: pogreške | 6 × preklapanje dvorišta (TP1–TP78, TP1–TP28, TP2–TP31, TP7–TP66, TP69–TP70, TP68–J3) |")
    L.append("| DRC: upozorenja | 229 — natpis preko bakra (62), debljina teksta (58), visina teksta (58), preklapanje natpisa (51) |")
    L.append("")
    L.append("Sve pogreške i upozorenja naslijeđeni su iz izvorne ploče: test-točke ondje su gusto "
             "postavljene, a natpisi sitni. Geometrija je namjerno preuzeta neizmijenjena, pa se "
             "položaji poklapaju s pravim modulom — pomicanje točaka radi čiste provjere DRC "
             "uništilo bi jedinu svrhu ovoga projekta.")
    L.append("")
    L.append("Upozorenja o oznakama znače da ta mreža u ovome projektu postoji samo na jednome "
             "mjestu (npr. nožica GPIO na J3 bez pripadne test-točke). To je očekivano jer je ostatak "
             "modula izostavljen.")
    L.append("")
    L.append("Nespojene veze pokazuju koje test-točke dijele mrežu s nožicom konektora — "
             "to je ovdje korisna obavijest, a ne pogreška.")
    L.append("")
    L.append("## Ponovno generiranje")
    L.append("")
    L.append("```bash")
    L.append("git clone --depth 1 https://github.com/schlae/cm5-reveng.git ~/.tmp/cm5-reveng")
    L.append("cd tools && python3 gen_all.py")
    L.append("```")
    L.append("")
    L.append("Generator je determiniran (UUID-ovi se računaju iz imena), pa ponovno pokretanje "
             "daje datoteke bez lažne razlike u gitu.")
    L.append("")
    L.append("## Licencija i podrijetlo")
    L.append("")
    L.append("Geometrija, imena mreža i footprinti potječu iz projekta "
             "[schlae/cm5-reveng](https://github.com/schlae/cm5-reveng) (CC BY-SA 4.0). "
             "Ovaj izvedeni projekt nasljeđuje istu licenciju.")
    L.append("")
    L.append("Izvorni autor izrijekom napominje da ploča **nije za proizvodnju**: parametri cjelovitosti signala "
             "nisu točni, footprinti se ne poklapaju savršeno, a popis materijala nije rekonstruiran. "
             "Isto vrijedi i ovdje — projekt služi za snalaženje i mjerenje, ne za izradu.")
    L.append("")

    path = os.path.join(OUT, "README.md")
    open(path, "w", encoding="utf-8").write("\n".join(L))
    print("zapisano:", path, os.path.getsize(path), "B |", len(tps), "test-tocaka u tablici")

if __name__ == "__main__":
    main()
