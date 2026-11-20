"""Build the module C pipe-priority grid (method M5) on one common grid: the 22 4 km blocks of file 07.

Layers per block (report section C, "Method M5"):
  1. groundwater demand not served by PDAM: file 07 demand model, P10/P50/P90 (CALCULATED, unvalidated
     at 4 km) - realdata/semarang/exp/sem_areas/semarang_areas.geojson;
  2. damage potential: mean soft-clay thickness (MEASURED, boreholes; explains ~80 % of sinking, file 14),
     with the 2023-26 Sentinel-1 sinking rate shown alongside - realdata/semarang/sx/bundle.npz;
  3. planned and new supply: SPAM Semarang Barat 2024 uptake (605 L/s, ~19 Mm3/yr), allocated to blocks by
     their area inside the three named kecamatan (Semarang Barat, Tugu, Ngaliyan) because the service map
     is not public (risk R4) - CALCULATED.
Writes data/pipe_cells.json. Usage: python scripts/build_pipe_cells.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MplPath
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"
REAL = ROOT / "realdata" / "semarang"
SPAM_M3_YR = 19_000_000
SPAM_KECAMATAN = {"SemarangBarat", "Tugu", "Ngaliyan"}
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True)
TO_LL = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True)
PRETTY = {"SemarangBarat": "Semarang Barat", "SemarangUtara": "Semarang Utara", "SemarangTengah": "Semarang Tengah",
          "SemarangTimur": "Semarang Timur", "SemarangSelatan": "Semarang Selatan", "KarangTengah": "Karang Tengah"}


def kecamatan_grid(e0: float, n0: float, pix: float, shape: tuple[int, int]) -> np.ndarray:
    gadm = json.loads((REAL / "admin/gadm41_adm3_semarang_demak.geojson").read_text())
    ny, nx = shape
    xx, yy = np.meshgrid(e0 + (np.arange(nx) + 0.5) * pix, n0 + (np.arange(ny) + 0.5) * pix)
    pts = np.c_[xx.ravel(), yy.ravel()]
    names = np.full(ny * nx, "", dtype=object)
    for f in gadm["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = np.array(poly[0])
            x, y = TO_UTM.transform(ring[:, 0], ring[:, 1])
            names[MplPath(np.c_[x, y]).contains_points(pts)] = f["properties"]["NAME_3"]
    return names.reshape(shape)


def served_area_cells(pix: float) -> float:
    """Full area of the three SPAM kecamatan (GADM), in grid cells, so blocks get their true share."""
    gadm = json.loads((REAL / "admin/gadm41_adm3_semarang_demak.geojson").read_text())
    area = 0.0
    for f in gadm["features"]:
        if f["properties"]["NAME_2"] != "KotaSemarang" or f["properties"]["NAME_3"] not in SPAM_KECAMATAN:
            continue
        g = f["geometry"]
        for poly in g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]:
            x, y = TO_UTM.transform(*np.array(poly[0]).T)
            area += 0.5 * abs(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1]))
    return area / pix**2


def main() -> None:
    b = np.load(REAL / "sx/bundle.npz")
    e0, n0, pix = float(b["E0"]), float(b["N0"]), float(b["PIX"])
    clay, sink = b["clay_m"].astype(float), b["D_d2326"].astype(float)
    kec = kecamatan_grid(e0, n0, pix, clay.shape)
    served_cells_total = served_area_cells(pix)

    blocks = [f for f in json.loads((REAL / "exp/sem_areas/semarang_areas.geojson").read_text())["features"]
              if f["properties"]["kind"] == "4km_block"]
    items = []
    for f in blocks:
        ring = np.array(f["geometry"]["coordinates"][0])
        x, y = TO_UTM.transform(ring[:, 0], ring[:, 1])
        bx0, by0 = round(x.min() / 1000) * 1000, round(y.min() / 1000) * 1000
        c0, r0 = int((bx0 - e0) // pix), int((by0 - n0) // pix)
        sl = (slice(r0, r0 + 20), slice(c0, c0 + 20))
        k = kec[sl]
        land = k != ""
        served = np.isin(k, list(SPAM_KECAMATAN))
        names, counts = np.unique(k[land], return_counts=True)
        order = np.argsort(-counts)
        p = f["properties"]
        lon, lat = TO_LL.transform(bx0 + 2000, by0 + 2000)
        square = ((0, 0), (4000, 0), (4000, 4000), (0, 4000), (0, 0))
        corners = [TO_LL.transform(bx0 + dx, by0 + dy) for dx, dy in square]
        items.append({
            "id": f"E{int(bx0 / 1000)}-N{int(by0 / 1000)}",
            "lon": round(float(lon), 5),
            "lat": round(float(lat), 5),
            "polygon": [[round(a, 5), round(c, 5)] for a, c in corners],
            "demand_m3_yr": round(p["pump_p50"] * 1e6),
            "demand_low_m3_yr": round(p["pump_p10"] * 1e6),
            "demand_high_m3_yr": round(p["pump_p90"] * 1e6),
            "clay_m": round(float(np.nanmean(clay[sl])), 1),
            "sinking_mm_yr": round(float(np.nanmean(sink[sl])), 1) if np.isfinite(sink[sl]).any() else None,
            "supply_m3_yr": round(SPAM_M3_YR * served.sum() / served_cells_total),
            "land_share": round(float(land.mean()), 2),
            "districts": [PRETTY.get(n, n) for n in names[order][:3]],
            "source_ids": ["EXP07", "EXP14", "LICSAR", "SPAM-SETKAB", "GADM"],
        })
    items.sort(key=lambda i: i["id"])
    allocated = sum(i["supply_m3_yr"] for i in items)
    assert 0 < allocated <= SPAM_M3_YR  # the rest of the three kecamatan lies outside the 22 blocks
    out = {
        "status": "available",
        "reason": None,
        "grid": "22 blocks of 4 km x 4 km, UTM 49S, the file 07 demand grid",
        "spam_allocated_m3_yr": allocated,
        "items": items,
    }
    (DATA / "pipe_cells.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for i in items:
        print(i["id"], i["districts"], i["demand_m3_yr"], i["clay_m"], i["sinking_mm_yr"], i["supply_m3_yr"])


if __name__ == "__main__":
    main()
