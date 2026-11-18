# State of the art (temporary final result, 2026-11-18)

## In one paragraph
From open satellite and map data, the system can (1) find sinking bowls and the areas where they
repeat year after year, and (2) given a known regional groundwater total, split that total into
16 km areas within about a factor of 1.5 for most of the pumped volume. That split was validated on two
regions it had never seen. It cannot give accurate pumping volumes for small areas (4-8 km), and it
cannot predict a region's total from the satellite alone: the sinking produced per cubic metre pumped
differs about 11 times between sites.

## What to use

| Output | Method | Validated how | Accuracy | Code |
|---|---|---|---|---|
| Sinking map (mm/yr) | Stack of pairs >= 24 days, two tracks combined | Repeat periods; GNSS in Houston (rho 0.65) | noise ~3.5 mm/yr robust (Semarang) | `real_goal_maps.py` |
| Sinking bowls (where) | Local matched filter: K0 cone B = 1.5 km + local quadratic in 2 km disc, threshold 60, 1 km spacing | Planted cones; blind realistic fields; repeat periods; Arizona meters | recall 73-87 %; near pumping 61 % vs 22 % random (Arizona) | `real_mf.py`, `real_cfar.py` |
| Pumping per area (how much) | Known regional total x share; share = sqrt(demand x subsidence volume) | Pre-registered confirmation on Arizona ESRV and Texas west | 16 km cells: volume-weighted median error factor 1.38-1.46; 55-86 % of volume within 2x | `xs_confirm.py`, `xs_apply_semarang.py` |
| Range per area | Errors measured on the unseen regions, applied to shares, rescaled to the total | same | P10-P90 | `xs_apply_semarang.py` |

Demand = 221.5 thousand m3/yr per km2 built area + 0.823 x cropland km2 x ET (mm/yr), fitted on Arizona
and Houston. Subsidence volume = mean positive sinking over coherent cells x area.

## Semarang numbers (current best)

Validated scale (16 km cells, Kota Semarang part of the 24 x 16 km grid, city total 38-61 Mm3/yr):

| Cell | Kota area | Pumping P10 / P50 / P90 (Mm3/yr) |
|---|---|---|
| West + central city | 192 km2 | 27.9 / 43.8 / 54.7 |
| East edge (Genuk side) | 7 km2 | 0.4 / 3.8 / 20.9 |

8 km and 4 km cells are in `realdata/semarang/exp/sem_areas/xsite_semarang_split.geojson` but flagged
`validated: false`. The older demand-only areas and hotspots (`semarang_areas.geojson`, file 07) remain
useful for ranking where to inspect.

## Known limits
- **Scale:** 16 km cells are coarse (two cells over Semarang). In Houston, 8 km cells were still ~2.3x
  off even with county totals known.
- **Big misses:** in Arizona ESRV the largest pumping cell (35 % of that region's volume) was under-
  predicted ~10x.
- **The total is an input:** Semarang's 38-61 Mm3/yr comes from 2000-2010 studies; registered
  abstraction was 13.1 (2016), 27.7 (2018) and 10.4 (2022) Mm3 (Perda Kota Semarang 2024), with
  unregistered wells on top.
- **Not all sinking is pumping:** 28-92 % of sinking in Demak is natural compaction (Sarah et al.
  2020); landfill loading dominates under fills (Perda 2024). Detected bowls do not coincide with
  sampled wells (Semarang, any period).
- **No direct check in Semarang:** there is no per-area pumping data; only the city total.

## What would improve it most
1. Groundwater use or PDAM piped-water coverage **per kecamatan** (Houston: knowing county totals
   cut the 16 km error from 0.36 to 0.21).
2. Metered abstraction for a sample of Semarang wells (the ESDM registry lists ~1050 wells).
3. Removing the east-west ramp from the ALOS-1 map, to compare 2006-10 with 2018-22 sinking rates.

## How to use the output
Use it to decide **where to inspect first**, then compare the high-pumping areas with the permit list.
Do not use the volumes to bill or fine anyone.
