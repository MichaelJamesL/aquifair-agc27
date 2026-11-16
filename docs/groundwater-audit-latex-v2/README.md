# Groundwater Audit from Space — sources

Build the PDF:   cd tex && pdflatex main && pdflatex main   (TeX Live; needs tcolorbox, pgf-umlsd, xltabular, needspace)
Rerun the experiment (about 10 min on a laptop):
    cd code
    python run_all.py A & python run_all.py B & python run_all.py C & python run_all.py D
    python analyze.py     # writes tex/results.tex (every number in the report)
    python figures.py     # writes tex/fig/*.pdf
    python figures_exec.py   # writes tex/fig/exec_solution.pdf (executive summary)
Python: numpy, scipy, scikit-learn, matplotlib.

tex/main.tex       preamble, tag macros (\Q \D \M \V \R \U \Sx \Ox)
tex/00-exec.tex    two-page executive summary
tex/00..06-*.tex   front, problem, method, experiment, feasibility, software, traceability
tex/results.tex    generated macros; do not edit by hand
code/synth.py      forward model, sparse inversion, baselines, bootstrap
