"""Dry-season (June-October) Sentinel-2 L2A median composites over the CAT Semarang-Demak critical and
damaged zones, used by build_leads.py to find buildings that appeared after the 2022 zone map and to date
the year each one appeared.

Source: Copernicus Sentinel-2 L2A via the Microsoft Planetary Computer STAC (public, anonymous SAS token).
Processing baseline 04.00 and later (all scenes from 2022) store reflectance + 1000; that offset is removed
per scene so every year is on the same scale.
Writes realdata/semarang/leads/s2_<year>.npz (uint16 medians of B02 B03 B04 B08 B11 B12 at 10 m, UTM 49S).
Usage: python scripts/fetch_s2_composites.py 2021 2022 2023 2024 2025 2026
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("GDAL_HTTP_TIMEOUT", "60")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

BOUNDS = (415000, 9215000, 465000, 9245000)  # UTM 49S, same crop as the IO land-cover grid
SHAPE = (3000, 5000)
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]
CLOUDY_SCL = [0, 1, 3, 8, 9, 10]  # no data, saturated, cloud shadow, cloud medium/high, cirrus
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
OUT = Path(__file__).resolve().parents[3] / "realdata" / "semarang" / "leads"
SCENES_PER_ORBIT = {89: 6, 132: 4}


def scenes(year: int) -> list[dict]:
    """Clearest scenes per relative orbit: orbit 89 covers ~92 % of tile 49MDN (all of Semarang east of
    ~432,000 E), orbit 132 only the western strip. Ranking both together by cloud % picks mostly orbit-132
    partial scenes (their cloud % is computed over a small, mostly-sea area) and starves the city."""
    body = {
        "collections": ["sentinel-2-l2a"],
        "bbox": [110.27, -7.08, 110.72, -6.8],
        "datetime": f"{year}-06-01/{year}-10-31",
        "query": {"eo:cloud_cover": {"lt": 30}, "s2:mgrs_tile": {"eq": "49MDN"}},
        "limit": 200,
    }
    items = requests.post(STAC, json=body, timeout=60).json()["features"]
    picked: list[dict] = []
    for orbit, n in SCENES_PER_ORBIT.items():
        by_date: dict[str, dict] = {}
        for item in sorted(items, key=lambda i: i["properties"]["eo:cloud_cover"]):
            if item["properties"]["sat:relative_orbit"] == orbit:
                by_date.setdefault(item["properties"]["datetime"][:10], item)
        picked += sorted(by_date.values(), key=lambda i: i["properties"]["eo:cloud_cover"])[:n]
    return picked


def read(href: str, token: str) -> np.ndarray:
    for attempt in range(4):
        try:
            with rasterio.open(f"{href}?{token}") as ds:
                window = from_bounds(*BOUNDS, transform=ds.transform)
                return ds.read(1, window=window, out_shape=SHAPE, resampling=Resampling.nearest)
        except rasterio.errors.RasterioIOError:
            if attempt == 3:
                raise
    raise AssertionError("unreachable")


def scene_bands(item: dict, token: str) -> dict[str, np.ndarray]:
    offset = 1000 if float(item["properties"].get("s2:processing_baseline", "0")) >= 4.0 else 0
    out = {"SCL": read(item["assets"]["SCL"]["href"], token)}
    for band in BANDS:
        dn = read(item["assets"][band]["href"], token).astype(np.int32)
        out[band] = np.where(dn > 0, np.clip(dn - offset, 1, None), 0).astype(np.uint16)
    return out


def main(years: list[int]) -> None:
    for year in years:
        token = requests.get(  # per year: a SAS token expires in under an hour
            "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-2-l2a", timeout=60
        ).json()["token"]
        items = scenes(year)
        with ThreadPoolExecutor(max_workers=len(items)) as pool:
            per_scene = list(pool.map(scene_bands, items, [token] * len(items)))
        clear = np.stack([~np.isin(s["SCL"], CLOUDY_SCL) & (s["B04"] > 0) for s in per_scene])
        out: dict[str, np.ndarray] = {"dates": np.array([i["properties"]["datetime"][:10] for i in items])}
        for band in BANDS:
            stack = np.stack([s[band] for s in per_scene]).astype(np.float32)
            stack[~clear] = np.nan
            out[band] = np.nan_to_num(np.nanmedian(stack, axis=0), nan=0).astype(np.uint16)
        out["clear_count"] = clear.sum(0).astype(np.uint8)
        np.savez_compressed(OUT / f"s2_{year}.npz", **out)
        print(year, "scenes", list(out["dates"]), "min clear", int(out["clear_count"].min()), flush=True)


if __name__ == "__main__":
    main([int(y) for y in sys.argv[1:]])
