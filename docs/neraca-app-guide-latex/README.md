# NERACA: a plain guide to the app

Plain-language guide to the NERACA app: features and screens, how it works, where the data comes from and
how it is used, and the method behind each module. Written for non-specialists; the research reasoning is
in `../groundwater-accounts-latex`.

Build the PDF:   pdflatex main && pdflatex main   (TeX Live or MiKTeX; needs tcolorbox, xltabular, tikz)

`figures/method-overview.png` (Figure 2) was generated with MAI-Image-2.7 (OpenRouter) in a create-critic loop
of five passes, then patched by script for the defects the critic found (one wrong operator, one dead-end node,
one invented caption, one garbled word, one wrong arrow, one missing arrowhead). Its labels were checked against the data below.

Two technical figures sit beside it and are not used in the guide: `figures/roof-detector.png` (how module B
finds new roofs, from `apps/backend/scripts/build_leads.py`) and `figures/accounts-pipes.png` (modules A and C,
from the volume-split experiment and `apps/backend/scripts/prereg_v5_v7_v8.md`). Each came from three passes of
the same loop; their wrong arrows and garbled words were then fixed by script.

In all three figures every text label was then erased and redrawn as crisp text (Arial Narrow) at twice the
generated size (2720 x 1536), so the wording is exact and stays sharp in print.

Numbers are taken from `apps/backend/data/` as of 20 November 2026 (leads funnel, checks V1-V8, SPAM test,
sinking periods). Update the text if those files are rebuilt.
