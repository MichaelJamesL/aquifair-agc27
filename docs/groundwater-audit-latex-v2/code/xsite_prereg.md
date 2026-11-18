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
