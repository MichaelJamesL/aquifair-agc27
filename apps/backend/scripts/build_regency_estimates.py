"""Estimated groundwater use for all 35 kabupaten/kota, 2020-2023 (method "regency_model", CALCULATED,
not validated). Adds the household and public-supply terms the taxable gap needs.

  estimate = household wells + business wells
  household wells = population x 80-150 L/person/day x share of households on wells
      low share:  households that drink well water (pump, protected and unprotected dug wells)
      high share: plus households that drink bottled/refill water (their washing source is not asked)
  business wells = OSM industrial land in the regency x Kota Semarang's intensity,
      i.e. registered industrial/commercial abstraction 15-25 Mm3/yr (2003-06, file 07) / Semarang's OSM
      industrial land. Assumes industry runs on its own wells as in Semarang (PDAM sold 0.22 Mm3 to industry).
      Never below the declared volume: what is declared and taxed is a floor on real use.
  taxable gap = business wells - declared (household wells are exempt and cancel out).

The 80-150 L and 15-25 Mm3 ranges are the report's file-07 assumptions. Nothing here is validated: the only
validated estimate is Kota Semarang's 16 km split, which stays the one the app uses there.

Inputs (realdata/jateng/, not in git):
  bps/population.json             BPS table 2288 per year; the year picker is a server action, so the four
                                  years were read from the page in a browser (2026-11-20)
  bps/drinking_water_source.json  BPS Susenas drinking-water source by kab/kota (fetch() below; no 2022 table)
  osm/industrial.json             Overpass landuse=industrial in ID-JT (fetch() below)
Usage: python scripts/build_regency_estimates.py [--fetch]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import requests
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "realdata" / "jateng"
DATA = Path(__file__).resolve().parents[1] / "data"
YEARS = (2020, 2021, 2022, 2023)
METHOD = "regency_model"
SEMARANG = "3374"
LITRES = (80, 150)  # L/person/day, file 07
SMG_REGISTERED = (15e6, 25e6)  # m3/yr, registered industrial/commercial abstraction 2003-06, file 07
PIX = 25.0  # m, rasterisation grid for land areas
UA = {"User-Agent": "neraca-data-build/0.1"}
WATER_TABLE = (
    "https://jateng.bps.go.id/id/statistics-table/3/YzBaMlduSlFVbTVrUnpWeU9YRTJka0pVTTFkU1FUMDkjMw==/x.html?year="
)
WATER_COLS = {
    "oj7o4zsc5v": "piped",
    "xdu59v1s3g": "pump",
    "zfwwozyccr": "bottled",
    "nkvwlqpemo": "protected_well",
    "oksqkah0me": "unprotected_well",
    "jprnteaazm": "protected_spring",
    "hwm2sqanbc": "unprotected_spring",
    "yrcosoj5wg": "surface",
    "paizzcrqes": "rain",
    "jt64kcmt66": "other",
    "xz73y0gy7q": "total",
}
SOURCES = [
    {
        "id": "BPS-POP-JT",
        "name": "BPS Jawa Tengah: population by kabupaten/kota (table 2288)",
        "publisher": "Badan Pusat Statistik Provinsi Jawa Tengah",
        "url": "https://jateng.bps.go.id/id/statistics-table/2/MjI4OCMy/",
        "label": "OFFICIAL",
        "accessed": "2026-11-20",
        "note": "2020-2023, based on the 2020 census.",
    },
    {
        "id": "BPS-WATER-JT",
        "name": "BPS Jawa Tengah: households by drinking-water source and kabupaten/kota",
        "publisher": "Badan Pusat Statistik Provinsi Jawa Tengah (Susenas)",
        "url": WATER_TABLE.removesuffix("x.html?year="),
        "label": "OFFICIAL",
        "accessed": "2026-11-20",
        "note": "2020, 2021, 2023; no 2022 edition. Drinking source only, so bottled-water households are a range.",
    },
    {
        "id": "OSM-IND-JT",
        "name": "OpenStreetMap landuse=industrial, Central Java",
        "publisher": "OpenStreetMap contributors (ODbL), via Overpass",
        "url": "https://overpass-api.de/",
        "label": "WEAK",
        "accessed": "2026-11-20",
        "note": "Volunteer mapping; how completely industrial land is mapped differs between regencies.",
    },
    {
        "id": "EXP08",
        "name": "Experiment 8: moving a pumping model between sites (Arizona, Houston)",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-20",
        "note": "No model transferred without a local total: error factor 5-27 on the unseen site.",
    },
]


def fetch() -> None:
    body = (
        '[out:json][timeout:600];area["ISO3166-2"="ID-JT"]->.a;'
        '(way["landuse"="industrial"](area.a);relation["landuse"="industrial"](area.a););out tags geom;'
    )
    osm = requests.post("https://overpass-api.de/api/interpreter", data={"data": body}, headers=UA, timeout=900)
    osm.raise_for_status()
    (RAW / "osm").mkdir(parents=True, exist_ok=True)
    (RAW / "osm" / "industrial.json").write_text(osm.text, encoding="utf-8")

    def value(text: str) -> float:
        dashes = ("-", chr(0x2013), chr(0x2014))  # BPS prints a dash for zero
        return 0.0 if text.strip() in dashes else float(text.replace(".", "").replace(",", "."))

    out: dict[str, dict[str, dict[str, float]]] = {}
    for year in (2020, 2021, 2023):
        page = requests.get(WATER_TABLE + str(year), headers={"User-Agent": "Mozilla/5.0"}, timeout=90).text
        page = page.replace('\\"', '"')
        rows = {}
        for match in re.finditer(r'"kode_wilayah":(\d+),"variables":(\{.*?\}\})', page):
            code = match.group(1)[:4]
            if code.startswith("33") and code != "3300":
                cells = json.loads(match.group(2))
                rows[code] = {WATER_COLS[k]: value(c["value"]) for k, c in cells.items() if k in WATER_COLS}
        assert len(rows) == 35, (year, len(rows))
        out[str(year)] = rows
    (RAW / "bps" / "drinking_water_source.json").write_text(
        json.dumps(
            {
                "source": "BPS Jawa Tengah, households by kabupaten/kota and drinking-water source (Susenas)",
                "url": WATER_TABLE,
                "percent_of_households": out,
            },
            indent=1,
        ),
        encoding="utf-8",
    )


def rings(element: dict) -> list[tuple[list[tuple[float, float]], bool]]:
    """(lon/lat ring, is_hole) for an Overpass way or multipolygon relation with geometry."""
    if element["type"] == "way":
        members = [{"role": "outer", "geometry": element.get("geometry", [])}]
    else:
        members = element.get("members", [])
    return [
        ([(p["lon"], p["lat"]) for p in m["geometry"]], m.get("role") == "inner")
        for m in members
        if m.get("geometry") and len(m["geometry"]) >= 4
    ]


def industrial_km2(regions: dict) -> dict[str, float]:
    """OSM industrial land per region on a 25 m grid (overlapping polygons counted once)."""
    to_utm = Transformer.from_crs(4326, 32749, always_xy=True).transform

    def ring_px(coords: list[tuple[float, float]], origin: tuple[float, float]) -> np.ndarray:
        x, y = to_utm(*zip(*coords, strict=True))
        return np.round(np.column_stack([(np.array(x) - origin[0]) / PIX, (origin[1] - np.array(y)) / PIX])).astype(
            np.int32
        )

    all_x, all_y = [], []
    for feature in regions["features"]:
        for poly in _polygons(feature["geometry"]):
            x, y = to_utm(*zip(*poly[0], strict=True))
            all_x += list(x)
            all_y += list(y)
    origin = (min(all_x), max(all_y))
    shape = (int((origin[1] - min(all_y)) / PIX) + 2, int((max(all_x) - origin[0]) / PIX) + 2)

    label = np.zeros(shape, np.uint8)
    ids = [f["properties"]["region_id"] for f in regions["features"]]
    for index, feature in enumerate(regions["features"], start=1):
        for poly in _polygons(feature["geometry"]):
            cv2.fillPoly(label, [ring_px(poly[0], origin)], index)
            for hole in poly[1:]:
                cv2.fillPoly(label, [ring_px(hole, origin)], 0)

    industry = np.zeros(shape, np.uint8)
    osm = json.loads((RAW / "osm" / "industrial.json").read_text(encoding="utf-8"))
    for element in osm["elements"]:
        parts = rings(element)
        for coords, hole in sorted(parts, key=lambda part: part[1]):  # outers first, then holes
            cv2.fillPoly(industry, [ring_px(coords, origin)], 0 if hole else 1)
    counts = np.bincount(label[industry == 1], minlength=len(ids) + 1)
    return {rid: float(counts[i]) * PIX * PIX / 1e6 for i, rid in enumerate(ids, start=1)}


def _polygons(geometry: dict) -> list[list[list[tuple[float, float]]]]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    return list(geometry["coordinates"])


def well_shares(water: dict, region_id: str, year: int) -> tuple[float, float]:
    """(low, high) share of households on wells; 2022 has no table, so it spans 2021 and 2023."""

    def shares(y: int) -> tuple[float, float]:
        row = water[str(y)][region_id]
        low = row["pump"] + row["protected_well"] + row["unprotected_well"]
        return low / 100, (low + row["bottled"]) / 100

    if year == 2022:
        (a_low, a_high), (b_low, b_high) = shares(2021), shares(2023)
        return min(a_low, b_low), max(a_high, b_high)
    return shares(year)


def main() -> None:
    if "--fetch" in sys.argv:
        fetch()
    regions = json.loads((DATA / "regions.geojson").read_text(encoding="utf-8"))
    names = {r["id"]: r["name"] for r in json.loads((DATA / "regions.json").read_text(encoding="utf-8"))}
    population = json.loads((RAW / "bps" / "population.json").read_text(encoding="utf-8"))["persons"]
    water = json.loads((RAW / "bps" / "drinking_water_source.json").read_text(encoding="utf-8"))
    water = water["percent_of_households"]
    declared = {
        (d["region_id"], d["year"]): d["declared_m3"]
        for d in json.loads((DATA / "accounts.json").read_text(encoding="utf-8"))
        if d["declared_m3"]
    }
    land = industrial_km2(regions)
    per_km2 = (SMG_REGISTERED[0] / land[SEMARANG], SMG_REGISTERED[1] / land[SEMARANG])
    print(
        f"Kota Semarang OSM industrial land {land[SEMARANG]:.2f} km2 -> "
        f"{per_km2[0] / 1e6:.2f}-{per_km2[1] / 1e6:.2f} Mm3/yr per km2"
    )

    estimates = [e for e in json.loads((DATA / "estimates.json").read_text(encoding="utf-8")) if e["method"] != METHOD]
    validated = {(e["region_id"], e["year"]) for e in estimates if e["method"] == "validated_16km_split"}
    terms = [
        t
        for t in json.loads((DATA / "account_terms.json").read_text(encoding="utf-8"))
        if not t.get("household_in_estimate")
    ]
    sources = ["BPS-POP-JT", "BPS-WATER-JT", "OSM-IND-JT", "EXP07", "EXP08"]
    for region_id in sorted(names):
        km2 = land[region_id]
        modelled = (km2 * per_km2[0], km2 * per_km2[1])
        for year in YEARS:
            floor = declared.get((region_id, year), 0)
            business = (max(modelled[0], floor), max(modelled[1], floor))
            floored = (
                (
                    " Declared use is above that, so business wells are set to the declared volume "
                    "(no gap visible to this model)."
                )
                if floor > modelled[0]
                else ""
            )
            people = population[str(year)][region_id]
            share = well_shares(water, region_id, year)
            household = (people * LITRES[0] * 365 / 1000 * share[0], people * LITRES[1] * 365 / 1000 * share[1])
            low, high = household[0] + business[0], household[1] + business[1]
            central = (low + high) / 2  # midpoints, so the household term cancels exactly in the gap
            span = " (2022 has no BPS table: spans 2021 and 2023)" if year == 2022 else ""
            note = (
                f"Regency model, not validated. Household wells {household[0] / 1e6:.1f}-{household[1] / 1e6:.1f} "
                f"Mm3: {people:,} people x {LITRES[0]}-{LITRES[1]} L/day x {share[0]:.0%}-{share[1]:.0%} of "
                f"households on wells{span}. Business wells {business[0] / 1e6:.2f}-{business[1] / 1e6:.2f} Mm3: "
                f"{km2:.2f} km2 of OSM industrial land at Kota Semarang's 2003-06 registered rate, never below "
                f"declared use.{floored} PDAM's own "
                "wells are not included. Moving pumping models between places without a local total has been "
                "off by 5-27x (file 08)."
            )
            estimates.append(
                {
                    "region_id": region_id,
                    "year": year,
                    "method": METHOD,
                    "low_m3": round(low),
                    "central_m3": round(central),
                    "high_m3": round(high),
                    "label": "CALCULATED",
                    "source_ids": sources,
                    "note": note,
                }
            )
            if (region_id, year) not in validated:
                terms.append(
                    {
                        "region_id": region_id,
                        "year": year,
                        "household_wells_low_m3": round(household[0]),
                        "household_wells_high_m3": round(household[1]),
                        "public_supply_low_m3": 0,
                        "public_supply_high_m3": 0,
                        "household_in_estimate": True,
                        "source_ids": sources,
                        "note": (
                            f"Regency model, not validated: business wells ({business[0] / 1e6:.2f}-"
                            f"{business[1] / 1e6:.2f} Mm3, OSM industrial land, never below declared) minus declared "
                            "use. Household "
                            "wells are exempt and cancel out. If PDAM's own wells are in the declared volume, the "
                            "gap is understated by their volume; if the regency's industry uses rivers, the sea or "
                            "PDAM rather than its own wells, it is overstated."
                        ),
                    }
                )
    estimates.sort(key=lambda e: (e["region_id"], e["year"], e["method"]))
    terms.sort(key=lambda t: (t["region_id"], t["year"]))
    for name, rows in (("estimates.json", estimates), ("account_terms.json", terms)):
        (DATA / name).write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    known = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    known = [s for s in known if s["id"] not in {s["id"] for s in SOURCES}] + SOURCES
    (DATA / "sources.json").write_text(json.dumps(known, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    check = next(e for e in estimates if e["region_id"] == SEMARANG and e["year"] == 2023 and e["method"] == METHOD)
    print(
        f"Kota Semarang 2023: regency model {check['low_m3'] / 1e6:.1f}-{check['high_m3'] / 1e6:.1f} Mm3 "
        "vs validated 27.9-54.7"
    )
    for region_id in sorted(land, key=land.get, reverse=True)[:8]:
        print(region_id, names[region_id], f"{land[region_id]:.2f} km2")


if __name__ == "__main__":
    main()
