# Cross-site volume transfer test (Arizona <-> Houston -> Semarang): pre-registered design

Written 2026-11-18, before any Houston InSAR rate, land-cover or ET layer was computed. Seen so far
for Houston: county pumping totals (unit check) and the clay layer only.

## Question
Can a pumping-volume model trained at one site with metered pumping predict pumping at another
site it never saw? If yes (in both directions), its held-out error is the honest error to attach
to Semarang. If no, Semarang volumes stay "demand-model ranges, not validated".

## Data (same definitions at every site)
| layer | Arizona | Houston | Semarang |
|---|---|---|---|
| truth pumping | ADWR metered wells, mean 2016-20 | USGS GULF model WEL input (reported + estimated use), mean 2016-18 | none |
| subsidence | OPERA DISP-S1 F07091 2016-21 | OPERA DISP-S1 F08882 2016-10..2020-12 | LiCSAR 2018-22 (desc+asc) |
| clay thickness | ADWR MSCU isopach (digitized) | GULF fine-grained thickness | Sarah et al. 2020 section (6 boreholes) |
| built / crop | ESA WorldCover 2021 | same | same |
| ET | MODIS MOD16A3GF 2016-20 | same | (not needed: little irrigation) |

Unit = 4 km block (smallest scale that worked in Arizona). Blocks kept if >= 25 % coherent InSAR
cells and clay known, and they have pumping > 0 or subsidence > 5 mm/yr or crop > 1 km2 or built > 2 km2.

## Models (all fit on the training site only)
- M0 baseline: training mean pumping per km2 x block area.
- M1 demand: Q = a*built_km2 + b*crop_km2*ET (non-negative LS).
- M2 subsidence: Q = subsidence volume / r, r = training median of (subsidence volume / Q).
- M3 subsidence + clay: log10 Q = log10 V_sub - (c0 + c1*log10 clay).
- M4 combined: ridge regression of log10 Q on log10 V_sub, log10 clay, log10 built, log10 crop*ET.
Ranges: 10-90 % quantiles of the training residuals (log10).

## Splits
Arizona -> Houston and Houston -> Arizona (site hold-out). Within-site 5-fold block CV reported for
reference only.

## Pass rules (decided now)
A model TRANSFERS if in BOTH directions:
1. Spearman rho > 0.3, and
2. median |log10(pred/true)| <= 0.5 (within a factor ~3), and
3. total error within -50 % .. +100 %.
Clay HELPS if M3 beats M2 on median |log10| in both directions.
An "oracle" run (M2/M3 with r re-fit on the test site's total) is reported only to show how much
an unknown regional share (e.g. piped-water coverage) costs; it is not a pass.

## Semarang
Apply only a model that transfers. Subsidence volume is first reduced by the natural-compaction
share of Sarah et al. 2020 (Semarang city 0-9 %, Semarang-Demak border 28-37 %, Demak 48-92 %).
If no model transfers, the Semarang output stays the demand-model range, labelled unvalidated.

## Addendum 1 (2026-11-18, still before any Houston InSAR result)
OPERA maps are relative to the scene median; Houston sinks broadly, so the Houston rate is shifted
by the median of (GNSS rate - InSAR rate) at the HGSD/UH GNSS stations (realdata/houston/gnss.json,
`Rate2024`, cm/yr, + = sinking; 2-km median of InSAR around each station). Arizona is left as is
(mostly stable desert and rock in the scene). Block subsidence volume = mean of max(D, 0) over the
coherent cells x block area (so sites with different coherence are comparable).

## Result (2026-11-18, xs_model.py -> realdata/xsite_model.json)
Houston InSAR tied to 144 GNSS stations (shift +5.2 mm/yr, rho GNSS vs InSAR 0.65).
Units: Arizona 167 blocks (south region; ESRV has no clay map), Houston 627 blocks.
- No model transfers (M0-M4 all fail): held-out median |log10| 0.68-1.43 (factor 5-27),
  totals -92 % (Houston -> Arizona) to +417 % (Arizona -> Houston).
- Subsidence per pumped m3 differs 11x between sites (median 2.5 % Arizona vs 28 % Houston).
- Clay does not help: M3 is not better than M2 in both directions; within Houston clay vs the
  ratio rho = 0.01 (Arizona 0.32).
- Oracle (site ratio known): factor ~2.3-4 error, total within -63 .. +2 %.
Verdict as pre-registered: no model is applied to Semarang; Semarang volumes stay the demand-model
ranges (sem_demand.py), labelled unvalidated.

## Addendum 2 (2026-11-18): top-down test - regional total known, spread by transferable patterns
Written before running it. Motivation: the oracle run above (site total known) cut the error from
factor 5-27 to 2-4, and Semarang HAS a local total (city groundwater use 38-61 Mm3/yr, published).
Question: given only the regional total (with Semarang-like uncertainty), how accurately can we split it
into areas, using a share model trained at the OTHER site?
- Units: same blocks as above (xs_model.keep). Scores at 4 km, 8 km (2x2) and 16 km (4x4) cells.
- Total given to the model: true site total x U(0.77, 1.23) (the 38-61 spread), 200 draws.
- Share models (fit on the training site, applied as shares at the test site, then x total):
  S0 area; S1 demand (a*built + b*crop*ET, NNLS); S2 subsidence volume; S3 subsidence^a x clay^b
  (log-linear fit); S4 ridge on log [subsidence, clay, built, crop*ET]; S5 geometric mean of S1 and S2.
- ACCURATE at a scale if, in BOTH directions (Arizona->Houston, Houston->Arizona), median
  |log10(pred/true)| <= 0.30 (within factor 2) over cells with pumping > 0, AND the 10-90 % range
  (from the 200 total draws x training-site share residuals) covers 70-90 % of cells.
- Report the smallest passing scale and the best model there. A model is chosen only if it beats S0.
- If something passes, apply it to Semarang with the city total 38-61 Mm3/yr (Kota Semarang cells).
