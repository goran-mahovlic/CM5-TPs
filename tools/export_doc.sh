#!/bin/bash
# Izvoz dokumentacije: shema u PDF-u i pogled na donji sloj ploce.
set -e
cd "$(dirname "$0")/.."
mkdir -p doc
kicad-cli sch export pdf -o doc/cm5_tp_breakout_schematic.pdf cm5_tp_breakout.kicad_sch
kicad-cli pcb export pdf --layers B.Cu,B.Silkscreen,Edge.Cuts --mode-single --black-and-white \
    -o /tmp/cm5_board.pdf cm5_tp_breakout.kicad_pcb
python3 - <<'PY'
import fitz
d = fitz.open('/tmp/cm5_board.pdf'); p = d[0]
bb = [b[1] for b in p.get_bboxlog()]
clip = fitz.Rect(min(b[0] for b in bb) - 5, min(b[1] for b in bb) - 5,
                 max(b[2] for b in bb) + 5, max(b[3] for b in bb) + 5)
p.get_pixmap(dpi=350, clip=clip).save('doc/ploca_donji_sloj.png')
print('doc/ploca_donji_sloj.png')
PY
echo "gotovo."
