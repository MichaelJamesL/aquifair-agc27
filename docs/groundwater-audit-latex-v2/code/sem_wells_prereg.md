# Registered-well location test (Semarang): pre-registered design

Written 2026-11-19, before any dot was extracted from the figure. Nothing about the registered
well locations has been looked at yet.

## Question
Does InSAR sinking in Semarang identify the locations of REGISTERED pumping wells? Location only:
the source has no volumes.

## Truth
Deep-well locations digitized from Lo et al. 2022 (Water 14:201, CC BY), Fig. 12 "Schematic of the
computational cell of the Semarang groundwater basin", green "Deep well" dots. The paper states the
well coordinates came from the Mining and Energy Agency of Central Java (ESDM registry).
Registry wells, no volumes.

Wells outside the 24 x 16 km model grid, or whose cell is not coherent land (outside the InSAR
mask, or WorldCover water >= 0.5), are dropped; the count kept is reported. "Coherent land" below
always means: InSAR mask of the map being tested AND WorldCover water < 0.5.

## Map and bowls (fixed, nothing tuned)
- Map: Sentinel-1 2018-22 vertical rate, two tracks (`real_goal_maps.load("da", "1822")`), mm/yr,
  + = sinking, 200 m cells.
- Bowls: the stored detections of the local matched filter with the best settings
  (`real_cfar.py --rw 2000 --nms 1000 --poly 2 --thrs 60`, B = 1.5 km), i.e. `exp/cfar_final.json`
  -> truth.sources (25 detections). Bowls whose cell is not coherent land are dropped (reported).

## T-A (map level)
Statistic: mean over kept wells of the 3x3-cell mean sinking rate around each well's cell (mean
over the coherent land cells of the 3x3 block). Compared with three nulls, 10,000 draws each,
one-sided p = (1 + #{null >= observed}) / (1 + 10,000):
- (a) uniform: the same number of cells drawn uniformly from coherent land cells, same statistic.
- (b) built-matched: for each well, a random coherent land cell from the same built-up-fraction
  quintile as the well's cell (WorldCover built fraction; quintiles = fifths of the coherent land
  cells ranked by built fraction, ties broken by cell index).
- (c) pattern shift: the whole well pattern shifted by one random offset (whole cells) whose
  wrapped (minimum-image) length is >= 2 km, wrapped inside the grid (torus); wells that land on
  coherent land are kept for that draw, the statistic is computed on them.

PASS if p < 0.05 against BOTH (b) and (c).

## T-B (bowl level)
Statistic: share of the kept bowls that have a kept digitized well within 1 km. Nulls, 10,000
draws each, same one-sided p:
- (a) uniform: the same number of bowls placed at random coherent land cell centres.
- (b) built-matched: each bowl replaced by a random coherent land cell from the same built
  quintile as the bowl's cell.
- (c) pattern shift of the WELLS: the kept well pattern shifted as in T-A (c) (wells landing on
  coherent land kept), share of the real bowls within 1 km of the shifted wells.

PASS if p < 0.05 against BOTH (b) and (c).

## Verdict (decided now)
- T-A AND T-B pass: "InSAR sinking identifies areas with registered pumping in Semarang (location
  only, no volumes)".
- T-A only: map-level association, bowls not supported.
- Neither (or T-B only): sinking areas cannot be labelled pumping areas.

## Reported, not judged
- The same T-A and T-B on the ALOS-1 2006-10 map (`alos/alos_rate_grid.npz`, ALOS mask AND
  water < 0.5) with its stored detections from the same fixed detector (`exp/alos_result.json`).
  Its east half carries an unremoved ramp; this is noted, not corrected.
- T-B at 500 m and 2 km.
- Sensitivity to digitizing error: T-A and T-B re-run 200 times with every well moved by an
  independent isotropic Gaussian offset whose radial RMS equals the estimated georeference RMS
  (the larger of the tick-fit RMS and the coastline-check offset); report the share of repeats
  that still pass (each of T-A, T-B, and both).

## Result
(to be appended after the run)
