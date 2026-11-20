"""Download Overture Maps places (points of interest) for the lead area: a second source of use class after OSM.

Writes realdata/semarang/leads/overture/places.json (id, name, taxonomy, confidence, lon/lat).
Needs duckdb, which is not a project dependency:
    uv run --no-project --with duckdb python scripts/fetch_overture_places.py
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

RELEASE = "2026-11-18.0"
BBOX = (110.22, -7.10, 110.69, -6.81)  # lon/lat, the Sentinel-2 lead grid
PARQUET = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=places/type=place/*"
OUT = Path(__file__).resolve().parents[3] / "realdata" / "semarang" / "leads" / "overture" / "places.json"
COLS = ["id", "name", "category", "hierarchy", "operating_status", "basic_category", "confidence", "lon", "lat"]


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    x0, y0, x1, y1 = BBOX
    rows = con.execute(f"""
        SELECT id, names.primary, taxonomy.primary, taxonomy.hierarchy, operating_status, basic_category, confidence,
               ST_X(geometry::GEOMETRY), ST_Y(geometry::GEOMETRY)
        FROM read_parquet('{PARQUET}', hive_partitioning=1)
        WHERE bbox.xmin > {x0} AND bbox.xmax < {x1} AND bbox.ymin > {y0} AND bbox.ymax < {y1}
    """).fetchall()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    items = [dict(zip(COLS, row, strict=True)) for row in rows]
    OUT.write_text(json.dumps({"release": RELEASE, "items": items}, ensure_ascii=False), encoding="utf-8")
    print(len(items), "places ->", OUT)


if __name__ == "__main__":
    main()
