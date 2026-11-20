"""Inputs for check V4 (Arizona retro test, see prereg_v5_v7_v8.md) into realdata/arizona/v4/.

- io_lulc.npz: Impact Observatory annual land cover v02 (10 m, 2017-2023) over the OPERA F07091 box,
  via the Microsoft Planetary Computer STAC (anonymous SAS token).
- cws.json: ADWR Community Water System service areas (ADWR ArcGIS Online, CWS_Service_Area), Esri JSON
  rings in UTM 12N.
- wells55.json: ADWR Well Registry (Wells 55) water wells in the box with their dates.
Usage: python scripts/fetch_az_v4.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from pyproj import Transformer
from rasterio.windows import from_bounds

OUT = Path(__file__).resolve().parents[3] / "realdata" / "arizona" / "v4"
BOX = (396800, 3606800, 481400, 3701800)  # UTM 12N, the OPERA F07091 200 m grid used by V8
PIX = 10
SHAPE = ((BOX[3] - BOX[1]) // PIX, (BOX[2] - BOX[0]) // PIX)
YEARS = range(2017, 2024)
ADWR = "https://services.arcgis.com/C34zQ7veRS0V1t04/arcgis/rest/services"
UA = {"User-Agent": "neraca-data-build/0.1"}
ENVELOPE = {"geometry": json.dumps({"xmin": BOX[0], "ymin": BOX[1], "xmax": BOX[2], "ymax": BOX[3],
                                    "spatialReference": {"wkid": 32612}}),
            "geometryType": "esriGeometryEnvelope", "inSR": 32612, "outSR": 32612,
            "spatialRel": "esriSpatialRelIntersects"}


def query_all(layer: str, where: str, fields: str) -> list[dict]:
    rows: list[dict] = []
    while True:
        params = {**ENVELOPE, "where": where, "outFields": fields, "f": "json", "resultOffset": len(rows),
                  "resultRecordCount": 2000, "orderByFields": "OBJECTID"}
        page = requests.get(f"{ADWR}/{layer}/query", params=params, headers=UA, timeout=180).json()
        rows += page["features"]
        if not page.get("exceededTransferLimit"):
            return rows


def land_cover() -> None:
    token = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/io-lulc-annual-v02",
                         timeout=60).json()["token"]
    lon, lat = Transformer.from_crs(32612, 4326, always_xy=True).transform([BOX[0], BOX[2]], [BOX[1], BOX[3]])
    out = {}
    for year in YEARS:
        body = {"collections": ["io-lulc-annual-v02"], "bbox": [lon[0], lat[0], lon[1], lat[1]],
                "datetime": f"{year}-01-01/{year}-12-31", "limit": 50}
        items = requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search", json=body,
                              timeout=60).json()["features"]
        grid = np.zeros(SHAPE, np.uint8)
        for item in items:
            with rasterio.open(f"{item['assets']['data']['href']}?{token}") as ds:
                if ds.crs.to_epsg() != 32612:
                    continue  # tiles of the neighbouring UTM zone; zone 12 tiles cover the box
                window = from_bounds(*BOX, transform=ds.transform)
                data = ds.read(1, window=window, out_shape=SHAPE, boundless=True, fill_value=0)
            grid = np.where(grid == 0, data, grid)
        out[f"y{year}"] = grid
        print(year, len(items), "tiles, no-data share", round(float((grid == 0).mean()), 4), flush=True)
    np.savez_compressed(OUT / "io_lulc.npz", e0=BOX[0], n1=BOX[3], pix=PIX, **out)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    cws = query_all("CWS_Service_Area/FeatureServer/0", "1=1", "OBJECTID")
    (OUT / "cws.json").write_text(json.dumps(cws), encoding="utf-8")
    print("CWS service areas", len(cws), flush=True)
    wells = query_all(
        "Well_Registry_2024/FeatureServer/0",
        "WELL_TYPE_GROUP IN ('EXEMPT','NON-EXEMPT')",
        "REGISTRY_ID,WELL_TYPE_GROUP,WELL_CANCELLED,WATER_USE,INSTALLED,APPROVED,UTM_X_METERS,UTM_Y_METERS",
    )
    rows = [w["attributes"] for w in wells]
    (OUT / "wells55.json").write_text(json.dumps(rows), encoding="utf-8")
    print("wells", len(rows), flush=True)
    land_cover()


if __name__ == "__main__":
    main()
