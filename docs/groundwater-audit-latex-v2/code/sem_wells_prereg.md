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
Run 2026-11-19 (`sem_wells_digitize.py`, `sem_wells_test.py`; `realdata/semarang/exp/registry_wells_test.json`).

Digitizing: 74 green blobs inside the map frame (legend dot and recharge inset excluded); 13 blobs are
overlapping dots (about 91 dots in total by area), counted once each. 55 blobs fall inside the grid
(the rest lie west of it); 54 are on coherent land for Sentinel-1, 55 for ALOS.

Georeference: affine fit to all 16 graticule ticks, RMS 2.9 m (max 4.5 m; 1 figure pixel = 30 m).
Coastline check: the Fig. 12 coast lies a median 271 m from the WorldCover 2021 coast, but the signed
north offset changes sign along the coast (west -680 m, harbour -250 m, east +1,015 m). This is shoreline
change (reclamation in the west, land lost to the sea in the east) plus a schematic boundary, not a
rigid shift. The eastern river, a canal wide enough to show as WorldCover 10 m water, gives a sharp
best fit at (dE 0, dN +25) m, median misfit 39 m. The georeference was not changed. Jitter RMS used
= max(2.9, 271) = 271 m (the 2-D best-shift search on the coast alone was ill-posed: it slid along the
coast to the edge of the search window and is not used).

| Sentinel-1 2018-22 (judged) | observed | null (a) uniform | null (b) built | null (c) shift | p (a) / (b) / (c) |
|---|---|---|---|---|---|
| T-A mean 3x3 rate at 54 wells (mm/yr) | 35.9 | 54.2 | 48.5 | 57.0 | 0.997 / 0.979 / 0.662 |
| T-B share of 25 bowls with a well <= 1 km | 0.24 (6) | 0.34 | 0.29 | 0.17 | 0.902 / 0.807 / 0.267 |
| T-B at 500 m (reported) | 0.08 | 0.15 | 0.12 | 0.06 | 0.906 / 0.843 / 0.451 |
| T-B at 2 km (reported) | 0.52 | 0.59 | 0.54 | 0.34 | 0.827 / 0.663 / 0.105 |

T-A FAIL, T-B FAIL. **Verdict: sinking areas cannot be labelled pumping areas.** The registered wells sit
on ground that sinks more slowly than typical coherent land (median 3x3 rate at the wells 25 mm/yr;
median land cell 49 mm/yr), also when the comparison is limited to equally built-up cells.

Reported, not judged:
- ALOS 2006-10 (55 wells, 59 of 74 bowls on coherent land): T-A 22.9 vs 19.0 / 21.8 / 19.1 mm/yr,
  p = 0.081 / 0.363 / 0.323; T-B 1 km 0.20 vs 0.26 / 0.25 / 0.19, p = 0.870 / 0.851 / 0.476. Both fail.
- Jitter (200 repeats, radial RMS 271 m, Sentinel-1): T-A passes in 0 %, T-B in 0 %, both in 0 %
  (median p: T-A 0.99 / 0.67, T-B 0.69 / 0.18 vs built / shift).
- Post hoc, not pre-registered: with every draw limited to the Lo et al. model domain (Fig. 12 covers
  only grid x < ~17 km), the wells are at chance: Sentinel-1 T-A 35.9 vs 38.6 / 39.0 / 40.2 mm/yr,
  p = 0.66 / 0.69 / 0.44; T-B 1 km (14 bowls) 0.36 vs 0.50 / 0.46 / 0.16, p = 0.91 / 0.87 / 0.12.

Note on the shift null: shifted wells that land off coherent land are dropped (on average 29 of 54
remain for Sentinel-1). For T-B this lowers the null share and makes the test easier to pass, so the
T-B failure is not caused by the null being too strict.
