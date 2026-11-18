# 09 Known regional total, split by patterns (validated)

## Idea
File 08 showed the regional ratio is the blocker, and knowing the site total cut the error a lot.
Semarang has a local total (city groundwater use 38-61 Mm3/yr). So: take the total as known and only
predict **how it is shared** between areas.

## 9a Top-down test (addendum 2, `xs_share.py`) - fail
- Share models trained on one site, applied at the other: S0 area, S1 demand, S2 subsidence volume,
  S3 subsidence x clay, S4 ridge, S5 sqrt(demand x subsidence volume).
- Total given with Semarang-like uncertainty (true total x U(0.77, 1.23)), scored at 4, 8, 16 km.
- Pass: unweighted median |log10| <= 0.30 in both directions, range coverage 70-90 %.
- Result: nothing passes. Best 16 km: S5 Houston -> Arizona 0.135 but Arizona -> Houston 0.357.

## Exploratory (not pre-registered, `xs_calcurve.py`)
- Houston with county totals known: S5 16 km 0.21, 8 km 0.32.
- **Volume-weighted** median (the big pumping areas, which an audit cares about): S5 16 km 0.26 / 0.13.
- Because this score was chosen after looking, it had to be confirmed on new data.

## 9b Confirmatory test (addendum 3, `xs_confirm.py`) - PASS
Written before any data of the new regions were looked at.
- Method fixed: S5 = sqrt(demand x subsidence volume); demand = 221.5 x built km2 + 0.823 x crop km2 x
  ET mm (thousand m3/yr, NNLS on all Arizona + Houston blocks used so far).
- Regions never used before: R1 Arizona East Salt River Valley; R2 Texas, GULF area west of Houston
  (OPERA F08882, tied to 7 GNSS stations, +1.4 mm/yr).
- Pass: volume-weighted median |log10| <= 0.30 at 16 km in both regions, and better than S0.

| Region | 16 km cells | Total (Mm3/yr) | S0 weighted | **S5 weighted** | S5 unweighted | Volume within 2x |
|---|---|---|---|---|---|---|
| R1 Arizona ESRV | 13 | 202.0 | 0.203 | **0.164** | 0.338 | 55 % |
| R2 Texas west | 45 | 134.7 | 0.248 | **0.140** | 0.146 | 86 % |

Weak spot: the largest ESRV cell (71 Mm3, 35 % of that region) was under-predicted ~10x. The
total-only 10-90 % range covered only ~20 % of cells, so ranges are built from the measured errors.

## Applied to Semarang (`xs_apply_semarang.py`)
Kota Semarang part of the grid, city total U(38, 61) Mm3/yr, subsidence reduced by 0-9 % natural
compaction, 4000 draws; each draw applies a per-cell error sampled (volume-weighted) from 9b and
rescales to the total.

| 16 km cell | Kota area | P10 / P50 / P90 (Mm3/yr) |
|---|---|---|
| West + central | 192 km2 | 27.9 / 43.8 / 54.7 |
| East edge | 7 km2 | 0.4 / 3.8 / 20.9 |

8 km and 4 km cells are written but flagged not validated.

Results: `realdata/xsite_share.json`, `xsite_calcurve.json`, `xsite_confirm.json`,
`realdata/semarang/exp/sem_areas/xsite_semarang_split.json/.geojson`.
