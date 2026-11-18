# 12 Relative pumping heatmap inside one region (not validated)

## Question
Without predicting volumes, can we show **where pumping is most severe inside one city**, i.e. rank
areas correctly?

## 12a Ranking test (addendum 4, `xs_rank.py`) - fail
- Index fixed: S5 = sqrt(demand x subsidence volume). Compared: demand only, subsidence only.
- Regions: R1 Arizona ESRV, R2 Texas west (no fitting done on them). Scales 2, 4, 8 km.
- Useful if, in both regions, Spearman >= 0.5 and the top 20 % of cells hold >= 40 % of the true pumping.
- Result: S5 fails at every scale. 2 km: all rho <= 0.27.
- Exploratory: demand only met the rule at 8 km in both regions (0.71 / 51 %, 0.51 / 43 %).

## 12b Confirmation on 5 new regions (addendum 5, DGX Spark) - fail
- Five new regions in the USGS GULF model area (Beaumont, Brazos valley, Brazoria coast, north of
  Conroe, Jasper), built in parallel on the DGX Spark (`xs_spark_run.sh`: OPERA search, frame and grid
  setup `xs_site_setup.py`, granule fetch, WorldCover, MODIS ET, rate map), all downloaded on the Spark.
  Scored on the laptop against GULF pumping (`xs_confirm_rank.py`).
- Rule: demand only at 8 km must pass in >= 75 % of eligible regions (>= 20 cells, >= 10 Mm3/yr).

| Region | Total Mm3/yr | Demand rho / top-20 % | S5 | Subsidence |
|---|---|---|---|---|
| R3 Beaumont | 58.3 | -0.05 / 5 % | -0.12 / 5 % | -0.18 / 8 % |
| R4 Brazos | 27.8 | -0.07 / 17 % | 0.31 / 26 % | 0.55 / 29 % |
| R5 south coast | 16.2 | 0.17 / 30 % | 0.11 / 29 % | 0.12 / 31 % |
| R6 north (not eligible) | 7.9 | 0.18 / 21 % | -0.08 / 10 % | -0.14 / 6 % |
| R7 north-east | 17.6 | 0.39 / 68 % | 0.38 / 55 % | 0.15 / 18 % |

0 of 4 eligible regions pass.

## Why it fails
In R3 the largest pumping cell (24.5 Mm3/yr, 42 % of the region) is forest with almost no built-up land,
consistent with a single industrial user; the highest-demand cells are rice fields that use surface
water and pump almost nothing. **Who pumps depends on who has another water source and where single
large users sit**, and neither is visible in land cover or InSAR.

## Meaning for Semarang
Registered abstraction in Semarang is 96 % industrial (Perda 2024), the case that failed worst here.
A within-city map needs **user data**: the ESDM / city well registry (~1050 registered wells with
locations and permitted volumes), or industrial-site locations with water use. With that list, the
heatmap is a direct map of permits, and InSAR sinking can flag areas of sinking with no permitted wells.

## Operational notes
- Spark env `xs` (Python 3.13, rasterio 1.5 for the Float16 OPERA DEM, libgdal-hdf4 for MODIS),
  separate from the ISCE env `alos`. Data in `~/xs_data/<region>`, code in `~/xs_code`.
- Five regions built in about 30 minutes in parallel; only ~3 MB per region copied back.

Results: `realdata/xsite_rank.json`, `realdata/xsite_confirm_rank.json`, `realdata/r3_east` .. `r7_northeast`.
