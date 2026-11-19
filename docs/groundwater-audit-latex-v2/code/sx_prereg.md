# Pre-registration: what explains the sinking in Semarang? (2026-11-19)

Written and committed before any of the experiments below were run. Code: `sx_*.py`; they run in
parallel on the DGX Spark (`~/sx_code`, data downloaded there into `~/sx_data`). The bundle of existing
layers (`sx_bundle.py`) holds only maps already made on the laptop.

## Target and common rules
- **Target T:** Sentinel-1 2018-22 vertical sinking rate (`GM.load("da","1822")`, mm/yr, + = sinking),
  200 m cells, coherent land only (mask and WorldCover water < 0.5).
- **Shift null (S):** the driver field (or point / line set) is moved by a random cyclic offset of at
  least 2 km (999 draws, 199 for model refits); the statistic is recomputed on the cells that stay valid.
  One-sided p = (1 + #null >= observed) / (1 + N), in the expected direction.
- **Matched null (M):** random cells drawn from the same stratum as each feature cell; strata =
  built-up quintile x distance-to-coast quintile (10,000 draws).
- **Geography baseline:** mean T in bins of distance-to-coast decile x elevation quintile. A "partial"
  statistic uses T minus this baseline. Distance to coast = distance to WorldCover water connected to
  the northern edge.
- **Block CV:** 2 km x 2 km blocks, 5-fold grouped CV repeated 5 times, gradient boosting
  (sklearn HistGradientBoostingRegressor, default settings, 200 iterations) unless stated.
- A driver **"is linked to the sinking"** if its statistic has the expected sign, |rho| >= 0.2 (or the
  stated effect size) and p < 0.05 against the shift null. It **"adds beyond geography"** if the
  partial statistic also has p < 0.05 against the shift null.

## Experiments (expected sign in brackets)
| # | Cause tested | Data (downloaded on the Spark) | Primary statistic and PASS rule |
|---|---|---|---|
| X01 | Land reclaimed from sea or ponds | JRC Global Surface Water 1984-2021 (transitions, occurrence) | cells with >= 25 % water-to-land area vs matched null (M) and shift (S): mean T higher by >= 10 mm/yr, p < 0.05 both |
| X02 | Age of new ground (fill / conversion) | Landsat C2 L2 1988-2024 (Planetary Computer), annual MNDWI / NDVI composites | among converted cells (water or vegetation -> built/bare, stays so >= 3 yr): rho(years since conversion, T) <= -0.2 with p_S < 0.05; converted vs never-changed built land (M) higher T, p < 0.05 |
| X03 | Age and volume of buildings (load) | GHSL BUILT-S 1975-2020, BUILT-V 2020, BUILT-H 2018 | (a) rho(years since built-up >= 20 %, T) <= -0.2, p_S < 0.05; (b) partial rho(built volume per m2, T) >= 0.2, p_S < 0.05 |
| X04 | Linear embankments (toll road, roads, rail, runway, dikes) | OpenStreetMap (Overpass) | mean T on lines (<= 200 m) minus 400-1000 m ring >= 5 mm/yr, p_S < 0.05 |
| X05 | Soft-soil thickness / young alluvium | Copernicus DEM 30 m, SoilGrids 2.0, ISRIC depth to bedrock, borehole clay | geography-only model block-CV R2 >= 0.3 and best single proxy |rho| >= 0.3, p_S < 0.05 |
| X06 | Regional drawdown from registered wells x soft soil | 74 digitized ESDM wells (file 13), Cooper-Jacob superposition, R = 5 km (2, 10 km reported) | block-CV R2 gain of (soil proxy + drawdown x soil proxy) over soil proxy alone >= 0.05 and above the 95th percentile of gains with shifted well patterns |
| X07 | Seasonal (elastic aquifer / hydrological) motion | LiCSBAS time series 2018-22 (t076), CHIRPS monthly rain | >= 20 % of land cells with T > 20 have annual amplitude > 3 x SE and phase clustered (resultant length >= 0.5); lag to rain reported |
| X08 | Change over time / response to pumping change | rate maps 2006-10 (ALOS), 2014-17, 2018-22, 2023-26 | registered abstraction fell 27.7 -> 10.4 Mm3 (2018 -> 2022): change (2023-26 minus 2018-22) more negative at registered wells than M and S nulls, p < 0.05 both. Stage 2: rho(conversion age from X02/X03, rate ratio 2023-26 / 2014-17) reported |
| X09 | Tectonics: faults, tilt, uplift | GEM Global Active Faults; asc + desc east component | rate step across mapped faults (mean |grad T| within 300 m) above shift null p < 0.05; uplift area and tilt reported |
| X10 | Independent elevation loss 2000 -> ~2012 | NASADEM (2000) vs Copernicus DEM (TanDEM-X 2011-15) | rho(DEM change, T) <= -0.2, p_S < 0.05 on non-built (WorldCover tree/crop/grass/wetland > 0.5) cells; all-land rho reported |
| X11 | Large water users | OSM industry, works, hotels, malls, hospitals, universities | mean T within 500 m vs matched (M) and shift (S): higher, p < 0.05 both |
| X12 | Many small domestic wells | WorldPop 2000-2020, 100 m | partial rho(population density 2020, T) >= 0.2 and partial rho(growth 2000-20, T) reported; p_S < 0.05 |
| X13 | Attribution (stage 2) | features from X01-X12 + bundle | grouped Shapley split of block-CV R2 into soil/geology, load/fill, pumping, tectonic groups; descriptive |
| X14 | GNSS check | Nevada Geodetic Lab MIDAS velocities | stations inside the grid: InSAR vs GNSS vertical; descriptive |

Local (laptop, the paper PDF is not on the Spark), descriptive:
- L1: Lo et al. 2022 Fig. 14 (simulated subsidence from registered pumping, 2010) digitized; rho with
  ALOS 2006-10 and T. A calibrated pumping-only model that matches the map (rho >= 0.5, p_S < 0.05)
  would mean pumping + clay can explain the pattern.
- L2: Fig. 3a coastlines 1847 and 1991 digitized: T on land added after 1847 vs older land (M, S).

## Verdict wording
Each cause gets "linked", "adds beyond geography" or "not supported". X13 gives shares of explained
variance, which are associations, not proof of cause. No result is used to change a rule above; bugs
found later are fixed and reported.

## Result (2026-11-19, after all runs; details in experiments/14-subsidence-causes.md)

| # | Primary result | Verdict |
|---|---|---|
| X01 | 41 reclaimed cells 58.6 vs matched 78.5 mm/yr (p 0.998), shift p 0.49 | not supported |
| X02 | age rho -0.22 (p_S 0.145): fail. Converted 53.2 vs old built 37.4 (p 0.0001): pass | partly linked |
| X03 | age rho -0.26 (p_S 0.22): fail. Volume partial rho -0.40 (wrong sign): fail. Growth 2000-20 partial 0.41 (p_S 0.001), reported | age/volume not supported; growth adds beyond geography |
| X04 | contrast -5.5 mm/yr (p_S 0.67); runway +10.8 (p 0.04), reported | not supported |
| X05 | CV R2 0.85, best single borehole clay rho 0.81 (p_S 0.003) | **linked (PASS)** |
| X06 | gain 0.026 vs null 95 % 0.029 (p 0.18) | not supported |
| X07 | 12.9 % of fast cells significant (AR(1)-corrected SE; 20.2 % with the plain SE), R 0.97 | not supported (judged with the corrected SE) |
| X08 | change at wells -5.5 vs matched -8.3 (p 1.0, p_S 0.67); stage 2 rho(age, ratio) -0.25 (p 0.93) | not supported |
| X09 | no mapped fault crosses the grid; uplift 0.3 % of land | not supported (no data) |
| X10 | rho -0.37 on non-built land (p_S 0.004) | **PASS** |
| X11 | 36.5 vs matched 53.4 (p 1.0) | not supported (opposite sign) |
| X12 | density partial rho -0.54 (p_S 0.97) | not supported |
| X13 | 2 km: R2 0.95; Shapley soil 0.72, load 0.15, pumping proxies 0.07 | descriptive |
| X14 | no NGL station within ~1 degree | no data |
| L1 | model bowls 58.2 vs 63.3 matched (p 0.98) | not supported |
| L2 | not done: Fig. 3 has no graticule (would need control points) | skipped |

Deviations and fixes (none changed a rule):
- X06: worker processes deadlocked (fork after OpenMP); switched to spawn and reran. Same design.
- X07: CHIRPS (data.chc.ucsb.edu) returned 403 to the Spark, so rainfall timing uses ERA5 daily rain from
  the Open-Meteo archive at the city centre.
- X10: the Copernicus DEM asset key is "data", not "elevation" (code fix only).
- X14: the http URL returned 404; https used, search radius widened to ~1 degree.
- Added after stage 2, labelled as such: X16 (robustness across periods), X19 (sharp edges), X20 (a
  coordinates-only model reaches R2 0.955 at 2 km blocks, so X13 was also run at 4 and 8 km blocks:
  soil 0.80, load 0.10, pumping proxies -0.05 at 8 km), L3 (borehole thickness), L4 (head decline at 6
  observation wells, exploratory: rho 1.0, exact p 0.0014).
