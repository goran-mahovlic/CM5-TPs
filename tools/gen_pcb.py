# -*- coding: utf-8 -*-
"""Iz izvorne CM5 ploce izvuci TP + J3/J4 + H1..H4 + Edge.Cuts u novu 2-slojnu plocu.

Radi izravno na S-expressionu (bez pcbnew API-ja) jer masovno brisanje preko SWIG-a
rusi tumac. Geometrija se ne dira -- elementi zadrzavaju izvorne koordinate.
"""
import os, re
from gen_common import SRCPCB, OUT, PROJ, short_net, sheet_of, sheet_meta, pcb_path, FP_REMAP

DST = os.path.join(OUT, PROJ + ".kicad_pcb")

KEEP_TOP = {"version", "generator", "generator_version", "general", "paper",
            "layers", "setup", "embedded_fonts"}
DROP_TOP = {"segment", "via", "zone", "group", "image", "embedded_files",
            "dimension", "arc", "target", "gr_text_box"}

def split_children(text):
    """Podijeli tijelo '(kicad_pcb ...)' na djecu prve razine: [(tag, tekst), ...]."""
    i = text.index("(") + 1
    while text[i] not in " \t\n":
        i += 1
    out, depth, start, instr, esc = [], 0, None, False, False
    j = i
    while j < len(text):
        c = text[j]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        elif c == '"':
            instr = True
        elif c == "(":
            if depth == 0: start = j
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                blk = text[start:j + 1]
                tag = re.match(r'\(([\w-]+)', blk).group(1)
                out.append((tag, blk))
            elif depth < 0:
                break
        j += 1
    return out

def keep_ref(ref):
    u = ref.upper()
    return u.startswith("TP") or u in ("J3", "J4", "H1", "H2", "H3", "H4")

def main():
    src = open(SRCPCB, encoding="utf-8").read()
    kids = split_children(src)
    print("elemenata prve razine u izvorniku:", len(kids))

    head, foots, edges, nets = [], [], [], []
    stats = {}
    for tag, blk in kids:
        stats[tag] = stats.get(tag, 0) + 1
        if tag == "net":
            nets.append(blk)
        elif tag == "footprint":
            ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
            if ref and keep_ref(ref.group(1)):
                foots.append((ref.group(1), blk))
        elif tag.startswith("gr_"):
            if '(layer "Edge.Cuts")' in blk:
                edges.append(blk)
        elif tag in KEEP_TOP:
            head.append((tag, blk))
    print("izvornik:", {k: v for k, v in sorted(stats.items(), key=lambda x: -x[1])[:8]})
    print("zadrzano: footprinta=%d, Edge.Cuts crta=%d" % (len(foots), len(edges)))

    # --- footprinti: putanja prema shemi + ime lista ---
    out_foots = []
    for ref, blk in foots:
        key = sheet_of(ref)
        name, fname, _ = sheet_meta(key)
        blk = re.sub(r'\n\t\t\(path "[^"]*"\)', "", blk)
        blk = re.sub(r'\n\t\t\(sheetname "[^"]*"\)', "", blk)
        blk = re.sub(r'\n\t\t\(sheetfile "[^"]*"\)', "", blk)
        tail = ('\t\t(path "%s")\n\t\t(sheetname "/%s/")\n\t\t(sheetfile "%s")\n\t)'
                % (pcb_path(ref), name, fname))
        assert blk.rstrip().endswith(")")
        blk = blk.rstrip()[:-1].rstrip() + "\n" + tail
        out_foots.append((ref, blk))

    # footprinti pokazuju na knjiznicu ovog projekta, ne na knjiznicu izvornika
    out_foots = [(r, re.sub(r'^\(footprint "([^"]+)"',
                            lambda m: '(footprint "%s"' % FP_REMAP.get(m.group(1), m.group(1)), b))
                 for r, b in out_foots]

    body = "\n".join("\t" + b for _, b in sorted(out_foots, key=lambda x: (x[0][0], len(x[0]), x[0])))

    # --- mreze: preimenuj i zadrzi samo one koje neki pad jos koristi ---
    used = set(re.findall(r'\(net \d+ "([^"]*)"\)', body))
    kept_nets, ren = [], 0
    for blk in nets:
        m = re.match(r'\(net (\d+) "([^"]*)"\)', blk)
        code, nm = m.group(1), m.group(2)
        if code != "0" and nm not in used:
            continue
        new = short_net(nm)
        if new != nm: ren += 1
        kept_nets.append('\t(net %s "%s")' % (code, new))
    for old in sorted(used, key=len, reverse=True):
        new = short_net(old)
        if new != old:
            body = body.replace('"%s")' % old, '"%s")' % new)
    print("mreza zadrzano: %d (od %d), preimenovano: %d" % (len(kept_nets), len(nets), ren))

    # --- zaglavlje: 2 sloja, bez stackupa iz 10-slojne ploce ---
    hd = {}
    for tag, blk in head:
        if tag == "layers":
            blk = "\n".join(l for l in blk.split("\n") if not re.search(r'"In\d+\.Cu"', l))
        if tag == "setup":
            blk = re.sub(r'\n\t\t\(stackup\n(?:.*\n)*?\t\t\)', "", blk)
        hd[tag] = "\t" + blk if not blk.startswith("\t") else blk

    title = ('\t(title_block\n\t\t(title "CM5 Test Point Breakout")\n'
             '\t\t(rev "1")\n'
             '\t\t(company "izvedeno iz schlae/cm5-reveng, CC BY-SA 4.0")\n'
             '\t\t(comment 1 "Samo test-tocke, konektori modula J3/J4 i rupe za pricvrscenje")\n'
             '\t\t(comment 2 "Geometrija preuzeta 1:1 iz izvorne ploce; bez vodova i zona")\n\t)')

    order = ["version", "generator", "generator_version", "general", "paper"]
    parts = ["(kicad_pcb"] + [hd[t] for t in order if t in hd]
    parts.append(title)
    parts += [hd[t] for t in ("layers", "setup") if t in hd]
    parts += kept_nets
    parts.append(body)
    parts += ["\t" + e for e in edges]
    if "embedded_fonts" in hd:
        parts.append(hd["embedded_fonts"])
    parts.append(")")
    open(DST, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    print("zapisano:", DST, round(os.path.getsize(DST) / 1024, 1), "kB")

if __name__ == "__main__":
    main()
