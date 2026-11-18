# 08 Cross-site transfer with clay thickness (Arizona <-> Houston)

## Idea
If two sites have the same kinds of layers (land structure, utilities, buildings) and one has well
data, train there, check on another site with well data, and only then trust the model in Semarang.
The honest error is the one on a site the model never saw (leave-one-site-out); Semarang's inputs
should lie inside the training range.

## Setup (pre-registered: `../code/xsite_prereg.md`, `xs_model.py`)
- Houston added: USGS GULF model pumping (2016-18), OPERA F08882 InSAR tied to 144 GNSS stations
  (shift +5.2 mm/yr, rho 0.65), GULF clay thickness. Arizona: ADWR meters, digitized ADWR clay map.
- Units: 4 km blocks (Arizona 167, Houston 627). Models: M0 area mean, M1 demand, M2 subsidence /
  ratio, M3 subsidence + clay, M4 ridge on all. Train on one site, predict the other, both directions.
- Pass: Spearman > 0.3, median |log10| <= 0.5, total within -50..+100 %, both directions.

## Results
- No model transfers: held-out median |log10| 0.68-1.43 (error factor 5-27), totals -92 %
  (Houston -> Arizona) to +417 % (Arizona -> Houston).
- Subsidence per pumped m3: **2.5 % Arizona vs 28 % Houston (11x)**.
- Clay does not explain it: M3 is not better than M2 in both directions; within Houston clay vs the
  ratio rho = 0.01 (Arizona 0.32).
- Oracle (site ratio known): factor ~2.3-4, total within -63 .. +2 %. The blocker is the local ratio
  (head history, clay compressibility), which no open map provides.

## Side finding
Sarah et al. 2020: natural compaction is 0-9 % of sinking in Semarang city, 28-37 % at the border and
48-92 % in Demak.

Results: `realdata/xsite_model.json`; clay layers `realdata/<site>/clay_200m.npz` (`xs_clay.py`).
