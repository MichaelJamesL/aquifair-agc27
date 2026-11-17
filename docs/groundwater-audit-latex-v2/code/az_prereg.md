# Arizona level-1 validation: pre-registered design (written before looking at well locations)

Data: OPERA DISP-S1 F07091 (T27 desc), 2016-08-09 .. 2021-03-16, vertical-only rate D (mm/yr) on
200 m UTM 12N grid. Truth: ADWR metered annual pumping per well, mean of 2016-2020 (acre-ft/yr ->
thousand m3/yr x 1.23348), wells in Eloy, Maricopa-Stanfield, East Salt River Valley sub-basins.

Detector (fixed, from Semarang): local matched filter, K0 cone B = 1500 m + local quadratic in a
2000 m disc, threshold 60 (thousand m3/yr subsidence-volume units), 1000 m peak spacing; global
background = cubic polynomial surface. Sensitivity run (reported, not tuned): B = 3000 m, disc 4000 m.

Tests
- T1 location: share of detections with >= 1000 thousand m3/yr metered pumping within 2 km.
  Nulls: (a) uniform random placement on valid cells; (b) placement weighted by subsidence rate
  (are detections nearer pumping than other sinking ground?). 4000 draws, one-sided p.
- T2 map: Spearman correlation between D and the subsidence predicted from metered pumping
  (sum q_i K0(r, B), B = 1.5 and 3 km) on valid cells; null = pumping field shifted by random
  offsets (>= 5 km, wrapped) 500 times.
- T3 volume: per detection, estimated q vs metered pumping within 2 km; Spearman rho. One
  calibration factor c = median(q_det / q_pump) fitted on Eloy + Maricopa-Stanfield, applied to
  East Salt River Valley (hold-out): median |q_det/c - q_pump| / q_pump and share within 30 %.

Success criteria (stated in advance): T1 p < 0.05 vs both nulls; T2 rho above the 95th null
percentile; T3 rho > 0.3 and hold-out median volume error < 50 %.

Caveats known in advance: subsidence lags pumping (aquitard drainage), so current pumping explains
only part of current subsidence; irrigated fields are decorrelated (masked); the export totals
include recovery pumping of stored water.

## Addendum (written after T1-T3, before computing any period maps): T4 change over time
Rate maps for P1 = 2016-08..2020-12 and P2 = 2021-01..2026-02 (same chain, same fit); pumping
P1 = mean 2016-2020, P2 = mean 2021-2025. Delta = P2 - P1 for both.
- T4a map: Spearman between observed delta-subsidence and delta predicted from delta-pumping
  (sum dq_i K0(r, B), B = 1.5 and 3 km) on cells valid in both periods; null = delta-pumping field
  shifted by random offsets (>= 5 km, wrapped), 500 times. Pass: rho above the null 95th percentile.
- T4b blocks: 3 km blocks with >= 500 thousand m3/yr pumping in either period; Spearman between
  block delta-subsidence volume (sum of delta-rate x cell area) and block delta-pumping. Pass:
  rho > 0.3 with shift-null p < 0.05. Volume: slope (delta-subsidence volume per delta-pumped
  volume) fitted on Eloy + Maricopa-Stanfield blocks, applied to East Salt River Valley blocks;
  report hold-out median error.

## Addendum 2 (before parsing any water-level data): T5 heads, T6 area + volume-range output
- T5a: head-decline rate per GWSI well 2016-08..2021-03 (robust slope of depth-to-water, wells with
  >= 3 measurements spanning >= 3 years, remark-coded readings such as 'pumping' excluded) vs the
  2016-21 subsidence rate (3x3-cell mean at the well). Spearman; null = rate map shifted by random
  offsets (>= 5 km, wrapped), 1000 times. Pass: p < 0.05.
- T5b: share of sinking area (> 10 mm/yr) whose nearest head trend is RISING (residual aquitard
  compaction not driven by current pumping). Descriptive; explains volume mismatch if large.
- T6: output = sinking AREAS, not points: connected regions with subsidence > 10 mm/yr and
  >= 1 km2 on the 2016-21 map. Per area: subsidence volume V (sum of rate x area) and a pumped-volume
  RANGE V/c_hi .. V/c_lo with c from the literature span only (USGS: ~0 to 0.6; we use 0.03-0.6,
  NOT fitted in Arizona). Truth = metered 2016-2020 pumping by wells inside the area or within
  2 km of it. Report: share of areas whose truth lies in the range (coverage), median range width
  (factor 20 by construction), and the share of metered pumping (by volume) inside any area.
  Known before running: the Arizona fit suggested c ~ 0.03-0.10, so coverage depends on the lower
  bound; this is reported as a property of the prior, not tuned.

## Addendum 3 (before running): T7 transferable volume-calibration METHODS
Goal: test calibration methods that use only data types Semarang also has (InSAR subsidence,
water-level trends, ONE regional pumping total), with per-well meters used only for scoring.
Units: 4 km blocks with metered 2016-2020 pumping > 0 or mean subsidence > 5 mm/yr.
Predictors per block: Vsub = sum of positive subsidence rate x area (2016-21 map);
Hdec = IDW (10 km, power 2) head-decline rate from GWSI wells x block land area.
Methods (k fitted ONLY from the calibration region's total pumping / total predictor):
- C1: Q = k1 * Vsub      - C2: Q = k2 * Hdec (positive part)
- C3: Q = k3 * sqrt(Vsub * Hdec+)   (geometric blend)
- C0 baseline: Q = regional mean per block (no spatial information).
Ranges: from the calibration region's blocks, the 10th-90th percentiles of log(true/pred) give an
80 % range applied in the hold-out. Splits: Eloy + Maricopa-Stanfield -> East Salt River Valley,
and reverse. Scores in hold-out: Spearman(pred, true), median |log10 ratio|, coverage of the 80 %
range (target 0.8), median range width factor, error of the hold-out regional total.
A method is useful if it beats C0 on Spearman and median |log ratio| in both splits and its
coverage is 0.65-0.95.
