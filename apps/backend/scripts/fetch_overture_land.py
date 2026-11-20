"""Download Overture Maps land polygons (from OpenStreetMap coastlines) for Jawa Tengah and Karimunjawa.

scripts/fit_coastline.py fits the zone, regency and kecamatan outlines to this coastline so they line up with the
basemap. Writes realdata/semarang/admin/overture/land_jateng.geojson. Needs duckdb, which is not a project dependency:
    uv run --no-project --with duckdb python scripts/fetch_overture_land.py
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

RELEASE = "2026-11-18.0"
BBOX = (108.5, -8.35, 111.85, -5.6)  # lon/lat, Jawa Tengah with Karimunjawa
PARQUET = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=base/type=land/*"
OUT = Path(__file__).resolve().parents[3] / "realdata" / "semarang" / "admin" / "overture" / "land_jateng.geojson"


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    x0, y0, x1, y1 = BBOX
    rows = con.execute(f"""
        SELECT ST_AsGeoJSON(ST_Intersection(geometry::GEOMETRY, ST_MakeEnvelope({x0}, {y0}, {x1}, {y1})))
        FROM read_parquet('{PARQUET}', hive_partitioning=1)
        WHERE bbox.xmax >= {x0} AND bbox.xmin <= {x1} AND bbox.ymax >= {y0} AND bbox.ymin <= {y1}
          AND subtype = 'land' AND class = 'land'
    """).fetchall()
    features = [{"type": "Feature", "properties": {}, "geometry": json.loads(g)} for (g,) in rows]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    collection = {"type": "FeatureCollection", "release": RELEASE, "features": features}
    OUT.write_text(json.dumps(collection), encoding="utf-8")
    print(len(features), "land polygons ->", OUT)


if __name__ == "__main__":
    main()
