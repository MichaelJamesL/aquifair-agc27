# 01 Data sources

All raw data are in `realdata/` (git-ignored). Grids are 200 m cells in UTM.

## Semarang, Indonesia (target site)
| Data | Source | Notes |
|---|---|---|
| Sentinel-1 InSAR | LiCSAR frames 076D_09725_121107 (desc) and 127A_09749_121312 (asc); extra stacks 2014-17 and 2023-26 | windowed remote reads (`real_fetch.py`); spans in `real_goal_maps.SPANS` |
| GACOS troposphere | LiCSAR epochs `*.sltd.geo.tif` | no effect on noise; dropped |
| Model grid | 24 x 16 km, SW corner E 428000 N 9220000, EPSG 32749 | `real_lib.Grid`, `synth.py` |
| Wells | PANGAEA 862987, sampled wells 1992-2007 | hydrochemistry wells, not an abstraction inventory |
| Registered deep wells | Lo et al. 2022, Water 14:201, Fig. 12 (ESDM registry coordinates), digitized | 74 blobs (~91 wells), locations only; `sem_wells_digitize.py`, `registry_wells/` |
| Industrial land | OpenStreetMap | `osm.json` |
| Land cover | ESA WorldCover 2021 | `worldcover_grid.npz` |
| Buildings | Microsoft building footprints | `msbuild/` |
| Admin | geoBoundaries ADM2 | Kota Semarang, Demak |
| Population | BPS 2023 (Kota 1,694,740), Census 2020 (Demak 1,203,956) | footprint per person 35.6 / 33.1 m2 |
| ET | MODIS MOD16A3GF 2016-20 | `et_200m.npz` |
| Clay thickness | Sarah et al. 2020, IJOG 7(3), section A-A', 6 boreholes (40-115 m) | `xs_clay.py` |
| City pumping totals | literature 38 (2000s) - 61 (2010 model) Mm3/yr; Perda Kota Semarang 2024: registered 13.1 (2016), 27.7 (2018), 10.4 (2022) Mm3, 96 % industrial | `realdata/semarang/perda/` |
| PDAM coverage | Tirta Moedal 52 %, ANTARA 60-65 %, Perda 2024 62 % | city-level only |
| ALOS-1 PALSAR | ASF, path 431, 2006-12 .. 2010-11 | processed on DGX Spark (file 10) |
| Surface-water history | JRC Global Surface Water 1984-2021 (transitions, occurrence), Google Cloud | file 14, X01 |
| Landsat 1988-2024 | Collection 2 Level 2 via Microsoft Planetary Computer (689 scenes) | annual MNDWI/NDVI, X02 |
| Built-up history | GHSL R2023A BUILT-S 1975-2020, BUILT-V 2020, BUILT-H 2018 (tile R10_C30) | X03 |
| OSM roads, rail, dikes, big water users | Overpass API | X04, X11 |
| DEMs | Copernicus DEM GLO-30 (AWS, Planetary Computer), NASADEM (Planetary Computer) | X05, X10 |
| Soil | SoilGrids 2.0 (clay, sand, silt, SOC, bulk density), ISRIC depth to bedrock | X05 |
| Rain | ERA5 daily via Open-Meteo archive (CHIRPS server refused the Spark) | X07 |
| Population | WorldPop 2000 and 2020, 100 m | X12 |
| Faults / GNSS | GEM Global Active Faults (none cross the grid); NGL MIDAS (no station within ~1 degree) | X09, X14 |
| Lo et al. 2022 figures | Fig. 5 sections + Fig. 4 positions (16 boreholes), Fig. 14 model bowls and observed heads | L1, L3, L4 |

## Arizona, USA (validation site 1)
| Data | Source | Notes |
|---|---|---|
| InSAR | OPERA DISP-S1 frame F07091 (track 27 desc), 2016-08 .. 2021-03 (+ later period for T4) | `az_opera_search/fetch/rate.py`, ministack chaining, IRLS fit |
| Pumping truth | ADWR Wells 55 "Pump Data Export", metered annual per well, 2984 wells | via Chrome (Cloudflare), batches of 100 IDs; `az_pump_parse.py`, `az_pump_merge.py` |
| Water levels | ADWR GWSI export | USGS API has no recent data here; `az_heads_area.py` |
| Land cover / ET | WorldCover 2021, MODIS MOD16A3GF | `az_features.py`, `az_et.py` |
| Clay | ADWR Pinal AMA geology update (Dubas & Liu 2010) Fig. 7 MSCU isopach, digitized | south region only; ESRV has none |

## Houston and Texas west (validation sites 2 and 3)
| Data | Source | Notes |
|---|---|---|
| InSAR | OPERA DISP-S1 frame F08882 (track 34 asc), 2016-10 .. 2020-12 | `SITE=houston` / `SITE=texas_w` in `opera_site.py` |
| Pumping truth | USGS GULF model WEL input (Knight et al. 2023, doi 10.5066/P9XM8A1P), 1 km cells, m3/day, monthly 2016-18 | TACC CKAN mirror `source_data.zip`; checked against HGSD county totals |
| Clay | GULF fine-grained thickness `fine_m2..m5` | metres |
| GNSS | HGSD / UH stations, `Rate2024` | 144 stations tie Houston (+5.2 mm/yr), 7 tie Texas west (+1.4) |
| Land cover / ET | WorldCover 2021, MODIS | same scripts |

## Access notes
- NASA Earthdata (OPERA, MODIS, ALOS) uses a `~/.netrc` created by the user; scripts never read it.
- ScienceBase is behind Cloudflare; the GULF files came from the TACC mirror.
- No open per-well pumping data was found for Indonesia or other ASEAN cities.
