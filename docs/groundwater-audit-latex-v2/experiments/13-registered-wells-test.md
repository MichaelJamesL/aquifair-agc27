# 13 Registered pumping wells vs InSAR sinking (pre-registered) - fail

## Question
Does InSAR sinking in Semarang show **where the registered pumping wells are**? Location only: the
source gives no volumes.

## Truth
Deep wells in Lo et al. 2022 (Water 14:201, CC BY), Fig. 12, digitized. The paper says the well
coordinates came from the Mining and Energy Agency of Central Java (the ESDM registry).
- The figure is two embedded rasters (1465 x 908 px together, 30 m per pixel). Georeference: affine fit
  to all 16 graticule ticks, RMS 2.9 m.
- 74 green blobs (legend dot and recharge inset excluded). 13 blobs are overlapping dots (about 91 dots
  by area); each blob counts once. 55 fall inside the 24 x 16 km grid, and 54 of those are on coherent
  land (Sentinel-1).
- Independent check against WorldCover 2021: the eastern river (a canal that WorldCover maps as water
  at 10 m) fits best at a (0, +25) m shift, median misfit 39 m. The Fig. 12 coast lies a median 271 m
  from today's coast. Its north offset changes sign along the coast (west -680 m, east +1,015 m), so this
  is shoreline change plus a schematic boundary, not a georeference shift. Nothing was corrected.

## Setup (fixed in `../code/sem_wells_prereg.md` before digitizing)
- Map: Sentinel-1 2018-22, two tracks. Bowls: the 25 stored detections of the fixed matched filter
  (`cfar_final.json`, rw 2 km, 1 km spacing, quadratic, threshold 60).
- T-A (map level): mean 3x3-cell sinking rate at the well cells, compared with (a) uniform land cells,
  (b) land cells from the same built-up quintile, and (c) the whole well pattern shifted by >= 2 km.
  10,000 draws each.
- T-B (bowl level): share of bowls with a well within 1 km. Nulls: (a) random bowls, (b) built-matched
  bowls, (c) shifted wells.
- Pass: p < 0.05 against both (b) and (c), for each test. The verdict needs both T-A and T-B to pass.

## Results (`realdata/semarang/exp/registry_wells_test.json`)

| Sentinel-1 2018-22 | observed | uniform | built-matched | shifted | p (a / b / c) | |
|---|---|---|---|---|---|---|
| T-A rate at 54 wells (mm/yr) | 35.9 | 54.2 | 48.5 | 57.0 | 0.997 / 0.979 / 0.662 | **fail** |
| T-B bowls with a well <= 1 km | 6 of 25 (0.24) | 0.34 | 0.29 | 0.17 | 0.902 / 0.807 / 0.267 | **fail** |
| T-B <= 500 m | 0.08 | 0.15 | 0.12 | 0.06 | 0.906 / 0.843 / 0.451 | reported |
| T-B <= 2 km | 0.52 | 0.59 | 0.54 | 0.34 | 0.827 / 0.663 / 0.105 | reported |

| Reported, not judged | Result |
|---|---|
| ALOS 2006-10, T-A | 22.9 vs 19.0 / 21.8 / 19.1 mm/yr, p = 0.081 / 0.363 / 0.323 (fail) |
| ALOS 2006-10, T-B 1 km (59 bowls) | 0.20 vs 0.26 / 0.25 / 0.19, p = 0.870 / 0.851 / 0.476 (fail) |
| Digitizing error: 200 repeats, wells jittered 271 m RMS | T-A passes 0 %, T-B 0 % |
| Post hoc: draws limited to the Lo et al. model domain | T-A 35.9 vs 38.6-40.2, p = 0.44-0.69; T-B 1 km (14 bowls) p = 0.91 / 0.87 / 0.12 |

## Verdict
**Sinking areas cannot be labelled pumping areas.** In 2018-22 the registered deep wells sit on ground
that sinks *more slowly* than typical land in the grid, even compared with equally built-up land. Inside
the area the figure covers, they sit where random points would. The detected bowls are no closer to
registered wells than random bowls. In 2006-10 (ALOS) the wells are slightly above average (p = 0.08
against uniform), but not against the built-matched or shifted nulls.

This matches the earlier tests with the PANGAEA sampling wells (files 02 and 10): bowls never pointed
at wells. The fastest sinking is in the north-east (coastal industry, young deposits and fills), where
the figure shows few registered wells.

## Limits
- One figure, one snapshot of the registry (probably the 2000s; reference 59 covers 2001-2010). It shows
  about 91 wells, against about 1,050 registered wells city-wide. Unregistered wells are not shown.
- No volumes: a few large users could drive the sinking while most registered wells pump little.
- Fig. 12 covers only the Lo et al. model domain (up to grid x about 17 km). The fastest-sinking east
  of the grid has no well information. The post hoc domain-limited run addresses this and still finds
  chance.
- Dot positions come from a schematic figure (dot diameter about 210 m). The jitter test shows that a
  271 m error does not change the outcome.
- The shift null drops wells that land off coherent land (on average 29 of 54 remain). That makes T-B
  easier to pass, not harder.
- Sinking is not only pumping: compaction of young deposits and loading under fills also cause sinking
  (file 00).

## Files
- Pre-registration and result: `../code/sem_wells_prereg.md`
- Code: `../code/sem_wells_digitize.py` (figure -> wells, georeference, QA), `../code/sem_wells_test.py` (tests)
- Data (git-ignored): `realdata/semarang/registry_wells/` (`fig12.png`, `fig12_wells.csv`,
  `fig12_georef.json`, `fig12_qa_dots.png`, `fig12_qa_coast.png`, `registry_wells_map.png`,
  `worldcover10m_window.npz`) and `realdata/semarang/exp/registry_wells_test.json`
