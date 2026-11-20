# Pre-registration: checks V5, V7 and V8 (NERACA report, Table "Validation checks")

Written 2026-11-20, before `run_checks.py` was run for the first time. The pass marks are copied from the
report (`docs/groundwater-accounts-latex/tex/05-backing.tex`); this file fixes the operational details the
report leaves open. Results go to `data/check_results.json`, and a failure is reported as a failure.

## V7 SPAM Semarang Barat before/after test (module C)

- Data: Sentinel-1 LiCSAR 076D vertical-assumption rate maps on the 200 m model grid
  (`realdata/semarang/sx/bundle.npz`: `D_d1517`, `D_d1822`, `D_d2326`, mm/yr, sinking positive).
- Served cells: grid cells whose centre lies in kecamatan Semarang Barat, Tugu or Ngaliyan (GADM 4.1
  level 3). Named in the government releases; the real service map is missing (risk R4).
- Outcome per cell: change = v(2023-26) - v(2018-22). A slowdown is negative.
- Matching: strata = quintiles of clay thickness (`clay_m`) x quintiles of built-up share (`wc_built`),
  computed over all valid cells. Delta = served-count-weighted mean over strata of
  (mean change served - mean change control); controls are all non-served valid cells in the stratum.
  Strata with no control or no served cell are dropped.
- Shift null: the served mask is translated by a random integer offset (dx, dy) of 10-40 cells (2-8 km) in
  each axis, either sign; offsets that keep fewer than 60 % of the served cells on valid data are redrawn.
  1,000 draws; matching recomputed for every draw. Seed 20261120.
- Pass (from the report): Delta below the 5th percentile of the shift null, AND both placebos between the
  5th and 95th percentiles of their own shift nulls:
  - placebo years: change = v(2018-22) - v(2014-17), same served cells;
  - placebo area: kecamatan Genuk, Pedurungan and Gayamsari (east side, not supplied by SPAM Semarang
    Barat), periods 2018-22 -> 2023-26.
- Outcome wording follows the report's outcome table (needs V8 for the "no extra slowdown" rows).

## V8 positive control in Arizona (module C)

- Data: OPERA DISP-S1 frame F07091, vertical rates on the 200 m grid for P1 = 2016-08..2020-11 and
  P2 = 2021-01..2026-01 (`realdata/arizona/opera_rate_200m_P1/_P2.npz`, `D`), ADWR metered pumping per
  well (`pump_all.csv`), clay and WorldCover built share on the same grid.
- Cut cells: 4 km blocks with mean annual metered pumping in P1 (2016-2020) in the top half of pumped
  blocks and a fall of at least 50 % in P2 (2021-2025). All 200 m cells of those blocks are "served"
  (the analogue of piped water arriving). This is the known, metered cut.
- Same Delta, matching (quintiles of clay x built share) and shift null (offsets 10-40 cells) as V7,
  1,000 draws, seed 20261120.
- Pass: Delta below the 5th percentile of the shift null (the method sees the known cut).
- If no block meets the cut definition, V8 is reported as "not run: no metered cut in the data".

## V5 Semarang permit overlap (module B)

- Permitted wells: the 467 "Sumur Bor" markers of the official 2022 zone map (Dinas ESDM Jateng), plus
  the 54 registered deep wells digitised from Lo et al. 2022 Fig. 12.
- Hit: a building whose footprint centroid is within 250 m of a permitted well (the zone map is printed at
  1:150,000; 250 m is about 1.7 mm on the sheet).
- Leads: buildings passing filters 1-3 (new after 2022, size and water-using class, critical or damaged
  zone). Filter 4 is a proxy and is not used here, so that V5 tests the building filters.
- Null: new buildings (filter 1) in the same zones, of any class, matched on footprint size by drawing,
  for every lead, a random new building from the same size quintile. 10,000 draws, seed 20261120.
- Pass (from the report): lead hit share above the null, one-sided p < 0.05.
- If fewer than 5 leads exist, V5 is reported as "not run: too few leads".

## Erratum (2026-11-20, before V5 was run)

- The Lo et al. 2022 Fig. 12 file (`realdata/semarang/registry_wells/fig12_wells.csv`) holds 74 digitised
  well markers, not 54 as written above. All 74 are used; the file itself was fixed before this document.
- A lead's position is the median pixel of its new-roof patch (10 m Sentinel-2 grid), which stands in for
  the footprint centroid, because new buildings are not yet in the Microsoft footprint set.
- Filter 1 also drops, before any check is run: patches shaped like roads or runways (elongation > 6 or
  > 30 % on an OSM major road), patches larger than 25 ha (land fill, port works, fields), and patches
  at least half inside a Microsoft building footprint (already built).
- Filter 1 needs the roof in at least two dry seasons running (built by 2025 when the last composite is
  2026), and the detector is trained on every year's composite. Both were set from a visual check of
  candidate chips (bare fill and dry fields read as roof), before V5 was run.
- Filter 1 also needs a radar check (Sentinel-1 RTC VV, orbit 76): the patch must be as bright as 90 % of
  known lead-size buildings in the last year and not in 2022. The level is set from Microsoft footprints,
  not from leads. Added for the same reason, before V5 was run.

## V4 Arizona retro test (module B) - written 2026-11-20, before the Arizona data was downloaded

Only the number of dated water wells in the study box was looked at (1,287 exempt or non-exempt wells
approved since 2017), to confirm the test can run. No building data and no hit share were looked at.

- Area: the OPERA F07091 box used by V8 (UTM 12N, 396,800-481,400 E, 3,606,800-3,701,800 N), minus the
  ADWR Community Water System service areas (`CWS_Service_Area`, ADWR ArcGIS Online, current copy).
- New large buildings: IO annual land cover (Impact Observatory v02, 10 m, 2017-2023). A pixel is new in
  year t (2018-2021) if it is not "built area" in every year before t and is built in every year from t
  to 2023. Connected patches (8-neighbour) of 1,000 m2 to 25 ha are the buildings, the same size bounds
  as Semarang filter 1. A patch is outside the service areas if its median pixel is.
- Wells: ADWR Well Registry (Wells 55, `Well_Registry_2024` layer, current copy), groups EXEMPT and
  NON-EXEMPT, not cancelled. Well date = INSTALLED when present, otherwise APPROVED.
- Hit: a well dated in calendar years t to t+2 within 500 m of the patch's median pixel.
- Null (built-matched): pixels that were built in every year 2017-2023, outside the service areas. Each
  new building draws one such pixel from the same quintile of built share in the surrounding 1 km
  (year t-1) and is given the same year t. 10,000 draws, seed 20261120.
- Pass (from the report): lead hit share at least 1.5 x the mean null share and one-sided p < 0.05.
- Fewer than 20 new buildings: reported as "not run: too few new buildings".
