# 05 Arizona: validation against metered pumping (T1-T7)

## Why Arizona
Semarang has no per-well pumping data, so the method was tested where meters exist: ADWR records
annual metered pumping per well. Sub-basins: Eloy and Maricopa-Stanfield ("SOUTH") and East Salt River
Valley (ESRV). InSAR: OPERA DISP-S1 F07091, 2016-08 .. 2021-03. Pumping: mean 2016-2020.

All tests and pass rules were written in `../code/az_prereg.md` before looking at well locations
(with an addendum before each later test). Detector fixed from Semarang (file 02), not tuned.

## Results
| Test | What | Result | Pass rule | Verdict |
|---|---|---|---|---|
| T1 | Share of 202 detections with >= 1000 thousand m3/yr metered pumping within 2 km | 61 % vs 22 % uniform null (p < 0.001); rate-weighted null 59 % (p 0.23) | p < 0.05 vs both | pass / fail |
| T2 | Spearman of map vs subsidence predicted from metered pumping | rho 0.22 at B = 1.5 km (null p95 0.19, p 0.026); B = 3 km p 0.088 | above null p95 | pass at 1.5 km |
| T3 | Volume per detection vs metered pumping within 2 km | rho 0.17; hold-out (ESRV) median error 68 %, 23 % within 30 %; ratio ~3.4 % | rho > 0.3, error < 50 % | fail |
| T4 | Change 2016-20 -> 2021-25: delta subsidence vs delta pumping | map rho -0.04 / -0.12; blocks rho 0.06, hold-out error 64 % | above null | fail |
| T5a | Subsidence rate vs water-level decline at 176 GWSI wells | rho 0.30 (null p95 0.21, p 0.003) | p < 0.05 | pass |
| T5b | Sinking area with rising heads (residual compaction) | 3 % | descriptive | small |
| T6 | 20 sinking areas, pumping range from literature ratio 3-60 % | coverage 6 %; implied ratio 0.2-2 % | descriptive | literature ratio too high |
| T7 | Transferable calibration (C1 subsidence, C2 heads, C3 blend) | none beats the regional mean C0 in both splits; totals off up to 4.7x | beat C0 both ways | fail |

## What it means
- **Where:** detections sit near pumping far more than chance, and sinking follows water-level decline.
  But they are about as near pumping as any other sinking ground (T1 rate-weighted): the detector
  finds sinking, and sinking here is mostly pumping-related.
- **How much:** subsidence per pumped volume is small (0.2-3 % in Arizona) and varies between areas,
  so volumes do not follow from subsidence alone.

Results: `realdata/arizona/az_validate_B1500.json`, `az_change.json`, `az_heads_area.json`, `az_calib.json`.
