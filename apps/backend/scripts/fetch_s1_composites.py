"""Dry-season (June-October) Sentinel-1 VV backscatter medians on the lead grid, used by build_leads.py to
tell new roofs (bright double bounce) from bare fill and fields (dark), which look alike in Sentinel-2.

Source: Sentinel-1 RTC (radiometrically terrain corrected gamma0, 10 m) via the Microsoft Planetary
Computer STAC. One geometry for every year: relative orbit 76, descending.
Writes realdata/semarang/leads/s1_<year>.npz (vv_db: median VV in dB x 100 as int16, NaN-free; 0 = no data).
Usage: python scripts/fetch_s1_composites.py 2022 2026
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
from rasterio.windows import from_bounds

BOUNDS = (415000, 9215000, 465000, 9245000)  # same grid as fetch_s2_composites.py
SHAPE = (3000, 5000)
ORBIT, SCENES = 76, 4
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
OUT = Path(__file__).resolve().parents[3] / "realdata" / "semarang" / "leads"


def scenes(year: int) -> list[dict]:
    body = {"collections": ["sentinel-1-rtc"], "bbox": [110.27, -7.08, 110.72, -6.8],
            "datetime": f"{year}-06-01/{year}-10-31", "limit": 200}
    items = [i for i in requests.post(STAC, json=body, timeout=60).json()["features"]
             if i["properties"]["sat:relative_orbit"] == ORBIT]
    items.sort(key=lambda i: i["properties"]["datetime"])
    step = max(1, len(items) // SCENES)  # spread over the season
    return items[::step][:SCENES]


def read_vv(item: dict, token: str) -> np.ndarray:
    for attempt in range(4):
        try:
            with rasterio.open(f"{item['assets']['vv']['href']}?{token}") as ds:
                assert ds.crs.to_epsg() == 32749, ds.crs
                window = from_bounds(*BOUNDS, transform=ds.transform)
                return ds.read(1, window=window, out_shape=SHAPE, boundless=True, fill_value=0).astype(np.float32)
        except rasterio.errors.RasterioIOError:
            if attempt == 3:
                raise
    raise AssertionError("unreachable")


def main(years: list[int]) -> None:
    for year in years:
        token = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc",
                             timeout=60).json()["token"]  # per year: a SAS token expires in under an hour
        items = scenes(year)
        with ThreadPoolExecutor(max_workers=len(items)) as pool:
            stack = np.stack(list(pool.map(read_vv, items, [token] * len(items))))
        stack[~(stack > 0)] = np.nan
        db = 10 * np.log10(np.nanmedian(stack, axis=0))
        vv = np.where(np.isfinite(db), np.clip(np.round(db * 100), -5000, 3000), 0).astype(np.int16)
        np.savez_compressed(OUT / f"s1_{year}.npz", vv_db=vv,
                            dates=np.array([i["properties"]["datetime"][:10] for i in items]))
        print(year, "S1 scenes", [i["properties"]["datetime"][:10] for i in items],
              "no-data share", round(float((vv == 0).mean()), 4), flush=True)


if __name__ == "__main__":
    main([int(y) for y in sys.argv[1:]])
