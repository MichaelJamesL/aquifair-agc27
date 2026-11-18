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

Result (xs_share.py -> realdata/xsite_share.json): nothing passes at 4, 8 or 16 km
(best 16 km: S5 Houston->Arizona 0.135 but Arizona->Houston 0.357; coverage 0.26-0.69).

## Exploratory findings after addendum 2 (not pre-registered; xs_calcurve.py -> xsite_calcurve.json)
- Local calibration blocks help Arizona (n=20 known blocks: 16 km 0.22) but not Houston (n=80: 4 km 0.52).
- Houston with county totals known: S5 16 km 0.21, 8 km 0.32.
- Volume-weighted median |log10| (the big pumping areas, what an audit cares about), S5 + regional total:
  16 km 0.26 (Arizona->Houston) and 0.13 (Houston->Arizona); 8 km 0.36 / 0.15.

## Addendum 3 (2026-11-18): confirmatory test of the exploratory winner on unseen regions
Written before any data of the new regions were looked at.
Method fixed: S5 = sqrt(demand x subsidence volume), demand = a*built + b*crop*ET with a, b from NNLS on
all Arizona + Houston blocks used so far (xs_model.keep); shares x the region's true total x U(0.77, 1.23).
Test regions (never used before):
- R1 Arizona East Salt River Valley: Arizona blocks with unknown clay (ESRV) that pass the other keep rules.
- R2 Texas, GULF model area west of the Houston box: lon -97.0..-96.0, lat 28.75..29.75 (OPERA frame
  covering it, same 2016-10..2020-12 window; GNSS tie if stations exist, else none).
Scale: 16 km cells (4 x 4 blocks).
PASS if in BOTH regions the volume-weighted median |log10(pred/true)| <= 0.30 (within factor 2) and S5
beats S0 (area share) on it. Also reported: unweighted median and 10-90 % range coverage.
If it passes, that is the validated method ("known regional total, split by sqrt(demand x subsidence),
16 km cells, within factor 2 for most of the pumped volume"), applied to Semarang with the city total.

Result of addendum 3 (xs_confirm.py -> realdata/xsite_confirm.json): PASS.
Demand weights (all Arizona + Houston blocks): 221.5 thousand m3/yr per km2 built + 0.823 x crop km2 x ET mm.
| region | cells (16 km) | total Mm3 | S0 weighted | S5 weighted | S5 unweighted |
|---|---|---|---|---|---|
| R1 Arizona ESRV | 13 | 202.0 | 0.203 | 0.164 | 0.338 |
| R2 Texas west (GNSS tie 7 stations, +1.4 mm/yr) | 45 | 134.7 | 0.248 | 0.140 | 0.146 |
Share of volume within factor 2: 55 % (ESRV), 86 % (Texas). Weak spot: the largest ESRV cell (71 Mm3,
35 % of the region) was under-predicted ~10x. The total-only 10-90 % range covered only ~20 % of cells, so
Semarang ranges use the confirmatory errors (volume-weighted) applied to shares, then rescaled to the total.

Semarang (xs_apply_semarang.py -> exp/sem_areas/xsite_semarang_split.json/.geojson), Kota Semarang part of
the grid, city total 38-61 Mm3/yr, 16 km cells (validated): west+central 192 km2 P10/50/90 27.9/43.8/54.7;
east edge 7 km2 0.4/3.8/20.9 Mm3/yr. 8 km and 4 km cells written but flagged not validated.

## Addendum 4 (2026-11-19, before running): relative severity heatmap (no volumes)
Question: inside one region, does the index rank areas by pumping correctly, so a RELATIVE heatmap
("where pumping is most severe in this city") can be shown without claiming volumes?
- Index fixed: S5 = sqrt(demand x subsidence volume), demand weights from xsite_confirm.json
  (fit on Arizona south + Houston only). Reported for comparison: demand only, subsidence only.
- Regions: R1 Arizona ESRV and R2 Texas west (no fitting done on them; their volumes were scored in
  addendum 3, their rankings were not looked at). Houston reported for reference only (training site).
- Scales: 2, 4, 8 km cells (cells kept by the addendum-3 rules).
- Scores per region and scale: Spearman(index, true pumping) over all kept cells; top-20 % capture =
  share of true pumped volume inside the 20 % of cells with the highest index (chance = 20 %);
  quintile agreement = share of cells whose index quintile is within 1 of their true quintile.
- USEFUL as a relative heatmap at a scale if in BOTH R1 and R2: Spearman >= 0.5 AND top-20 % capture
  >= 40 % (2x chance). The finest passing scale is used for Semarang; if none passes, no heatmap finer
  than the 16 km volume split is published.

Result of addendum 4 (xs_rank.py -> realdata/xsite_rank.json): FAIL at 2, 4 and 8 km.
| region | scale | S5 rho / top-20 % | demand rho / top-20 % | subsidence rho / top-20 % |
|---|---|---|---|---|
| R1 ESRV | 4 km | 0.19 / 25 % | 0.51 / 35 % | 0.08 / 25 % |
| R1 ESRV | 8 km | 0.53 / 27 % | 0.71 / 51 % | 0.34 / 27 % |
| R2 Texas west | 4 km | 0.40 / 45 % | 0.46 / 48 % | 0.17 / 31 % |
| R2 Texas west | 8 km | 0.47 / 43 % | 0.51 / 43 % | 0.30 / 33 % |
| Houston (training, ref) | 8 km | 0.56 / 39 % | 0.47 / 40 % | 0.41 / 36 % |
2 km: all rho <= 0.27. Exploratory (seen only now): DEMAND ONLY meets the rule at 8 km in both R1 and R2;
subsidence adds nothing to the within-region ranking.

## Addendum 5 (2026-11-19, before any data of the new regions exist): confirm demand-only ranking at 8 km
Index fixed: demand = 221.5*built_km2 + 0.823*crop_km2*ET_mm (xsite_confirm.json), summed to 8 km cells.
Reported, not judged: S5, subsidence, and 4 km.
New regions (all inside the USGS GULF model grid, no overlap with Houston or Texas-west boxes):
- R3 east (Beaumont / Port Arthur): lon -94.9..-93.8, lat 29.6..30.45
- R4 north-west (Brazos valley): -97.0..-96.0, 29.75..30.75
- R5 south coast (Brazoria / Bay City): -96.0..-95.0, 28.75..29.35
- R6 north (Conroe north / Huntsville): -96.0..-94.9, 30.45..31.3
- R7 north-east (Jasper / Woodville): -94.9..-93.8, 30.45..31.3
Truth: GULF WEL mean 2016-18. InSAR: OPERA DISP-S1, best-covering frame, 2016-10..2020-12 (needed for the
cell keep rule and for S5). Keep rule as addendum 4. A region is ELIGIBLE if it has >= 20 kept 8 km cells
and true pumping >= 10 Mm3/yr (decided now, without looking).
CONFIRMED (a relative heatmap at 8 km may be shown) if demand-only reaches Spearman >= 0.5 AND top-20 %
capture >= 40 % in at least 75 % of eligible regions (rounded up). Otherwise no within-city heatmap is
claimed as validated; Semarang keeps only the 16 km split.
