# 07 Semarang demand model (areas + volume ranges)

## Idea
Output areas (not points) with a pumping **range**, from the water demand that groundwater must
supply, since Semarang has no pumping meters.

## Model (`sem_popcal.py`, `sem_demand.py`, 2000 Monte Carlo draws)
Per 200 m cell: domestic = building footprint / (m2 per person) x litres per person per day x
(1 - piped coverage); industrial = OSM industrial area x intensity matched to registered industrial
abstraction. Per 4 km block a structural error (sigma_log10 = 0.55, from Arizona) is added and
renormalised so the regional total stays unbiased.

| Parameter | Range | Source |
|---|---|---|
| m2 footprint per person | calibrated 35.6 (Kota), 33.1 (Demak) | BPS population / Microsoft footprints |
| litres per person per day | 80-150 | assumption |
| PDAM coverage | Kota 52-65 %, Demak 20-45 % | Tirta Moedal, ANTARA; Demak assumed |
| industrial registered | 15-25 Mm3/yr | 2003-2006 figures |

## Results (`realdata/semarang/exp/sem_areas/`)
- Kota Semarang cells: **25-48 Mm3/yr (median 36.5)** vs published city total 38-61: consistent.
- 22 blocks of 4 km and 24 InSAR hotspot areas (matched-filter regions + 1 km buffer), each with
  P10-P50-P90 pumping, subsidence volume and industrial share. Ranges are ~10-25x wide.
- Files: `semarang_areas.geojson`, `summary.json`, `semarang_areas.png`, `popcal.json`.

## Verdict
A sensible but **unvalidated** ranking of where pumping likely is. Superseded for volumes by the
validated split in file 09; still useful at 4 km for "where to inspect".
