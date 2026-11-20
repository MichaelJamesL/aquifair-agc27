"""Fit map polygons to the real coastline (OpenStreetMap land, via Overture) so overlays line up with the basemap.

The 2022 ESDM zone map, the geoBoundaries regency outlines and the GADM kecamatan outlines use simplified
coastlines: they spill into the sea and miss reclaimed land (Tanjung Emas port). For each layer this
1. clips every polygon to land;
2. gives land the layer misses along the coast (within MAX_GAP_M of the layer and of the sea) to the nearest
   polygon, but never across a blocker, i.e. land the same source gives to something else: for regencies the other
   geoBoundaries units, for kecamatan the other GADM kecamatan, for zones the land the PDF shows outside the basin.
3. makes each layer an exact coverage, so neighbours share one border line: GADM's own kecamatan borders gap and
   overlap by tens of metres, and the digitised zones leave half-pixel gaps between colours.

Inputs: realdata/semarang/admin/overture/land_jateng.geojson (scripts/fetch_overture_land.py),
realdata/semarang/admin/idn_adm2.geojson (geoBoundaries), realdata/semarang/admin/gadm41_adm3_jateng.geojson
(GADM 4.1 level 3, NAME_1 == "JawaTengah") and realdata/semarang/zones/pdf_sea.geojson (scripts/digitise_zones.py).
Rewrites data/zones.geojson, data/regions.geojson and the outlines in data/pdam_coverage.json, so run it after
digitise_zones.py, build_seed.py or build_pdam_coverage.py.
Usage: uv run --no-project --with shapely --with pyproj python scripts/fit_coastline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import box, mapping, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"
ADMIN = ROOT / "realdata" / "semarang" / "admin"
MAX_GAP_M = 3000  # Tanjung Emas reclamation reaches ~2 km past the map coastlines
STEP_M = 20  # boundary sampling for the nearest-polygon split
TOLERANCE_M = 10  # coverage simplification: shared borders move together, so neighbours never gap or overlap
GAP_M = 50  # unowned faces with mean width (2 area / perimeter) under 2 x GAP_M are source mismatches, not enclaves
SLIVER_M = 250  # unfilled PDF strips narrower than 500 m are drawing gaps, not land outside the basin
NOTE = "Coastline fitted to OpenStreetMap land (Overture 2026-11-18.0) by scripts/fit_coastline.py"
SOURCE = {
    "id": "OSM-COAST",
    "name": "OpenStreetMap coastline (Overture Maps base land, release 2026-11-18.0)",
    "publisher": "OpenStreetMap contributors, via Overture Maps Foundation",
    "url": "https://docs.overturemaps.org/guides/base/",
    "label": "WEAK",
    "accessed": "2026-11-20",
    "note": (
        "ODbL. The zone, regency and kecamatan outlines are clipped to this land, and coastal land the source maps "
        "leave out (Tanjung Emas, Marina) is given to the nearest zone or unit: an assumption, not the official map."
    ),
}
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True).transform
TO_LL = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True).transform


def polygonal(geom: shapely.Geometry) -> shapely.Geometry:
    """Only the polygon parts: clipping and make_valid can leave stray lines and points."""
    return shapely.MultiPolygon([g for g in shapely.get_parts(shapely.make_valid(geom)) if g.geom_type == "Polygon"])


def utm(geometry: dict) -> shapely.Geometry:
    return polygonal(transform(TO_UTM, shape(geometry)))


def lonlat(geom: shapely.Geometry) -> dict:
    geom = shapely.set_precision(transform(TO_LL, geom), 1e-6)
    polys = [g for g in getattr(geom, "geoms", [geom]) if g.geom_type == "Polygon" and not g.is_empty]
    return mapping(shapely.MultiPolygon(polys))


def polygons(geom: shapely.Geometry) -> list[shapely.Geometry]:
    return [g for g in shapely.get_parts(geom) if g.geom_type == "Polygon" and g.area > 1]


def nearest_split(piece: shapely.Geometry, candidates: list[tuple[object, shapely.Geometry]]) -> dict:
    """Split a gap piece among candidates by the nearest candidate edge; label None is a blocker."""
    reach = piece.buffer(MAX_GAP_M)
    seen: dict[tuple[float, float], object] = {}
    for label, geom in candidates:
        edge = geom.boundary.intersection(reach)
        for line in shapely.get_parts(edge):
            if line.geom_type != "LineString" or line.length == 0:
                continue
            for p in shapely.line_interpolate_point(line, np.linspace(0, line.length, int(line.length // STEP_M) + 2)):
                seen.setdefault((round(p.x, 1), round(p.y, 1)), label)  # shared edges: first label wins
    if not seen:
        return {}
    pts = shapely.points(list(seen))
    cells = shapely.voronoi_polygons(shapely.MultiPoint(pts), extend_to=reach, ordered=True)
    assert len(cells.geoms) == len(pts)
    by: dict[object, list] = {}
    for cell, label in zip(cells.geoms, seen.values(), strict=True):
        if label is not None:
            by.setdefault(label, []).append(cell)
    return {label: shapely.union_all(c, grid_size=0.01).intersection(piece) for label, c in by.items()}


def fit(features: dict, blockers: list[shapely.Geometry], land: shapely.Geometry, band: shapely.Geometry) -> dict:
    clipped = {label: polygonal(geom.intersection(land)) for label, geom in features.items()}
    covered = shapely.union_all(list(clipped.values()))
    gap = land.intersection(band).intersection(covered.buffer(MAX_GAP_M)).difference(covered)
    if blockers:
        gap = gap.difference(shapely.union_all(blockers))
    candidates = [*clipped.items(), *((None, b) for b in blockers)]
    tree = shapely.STRtree([g for _, g in candidates])
    added: dict[object, list] = {}
    for piece in polygons(gap):
        near = [candidates[i] for i in tree.query(piece, predicate="dwithin", distance=MAX_GAP_M)]
        for label, part in nearest_split(piece, near).items():
            added.setdefault(label, []).append(part)
    return {label: polygonal(shapely.union_all([geom, *added.get(label, [])])) for label, geom in clipped.items()}


def tidy(layer: dict) -> dict:
    """Make the layer an exact coverage: every face of the noded outlines gets one owner, thin gaps between
    neighbours go to the neighbour sharing the longest edge (enclaves like Kota Salatiga stay empty), then the
    shared edges are simplified once for both sides."""
    labels = list(layer)
    edges = shapely.union_all([g.boundary for g in layer.values()])  # noded at every crossing
    faces = list(shapely.get_parts(shapely.polygonize(list(shapely.get_parts(edges)))))
    tree = shapely.STRtree(list(layer.values()))
    owner: dict[int, object] = {}
    for k, face in enumerate(faces):
        inside = tree.query(face.point_on_surface(), predicate="within")
        if len(inside):
            owner[k] = labels[min(inside)]  # an overlap goes to the first feature
    gaps = [k for k in range(len(faces)) if k not in owner and 2 * faces[k].area / faces[k].length < 2 * GAP_M]
    face_tree = shapely.STRtree(faces)
    while gaps:
        left = []
        for k in gaps:
            shared: dict[object, float] = {}
            for j in face_tree.query(faces[k], predicate="touches"):
                if j in owner:
                    edge = faces[k].boundary.intersection(faces[j].boundary).length
                    shared[owner[j]] = shared.get(owner[j], 0.0) + edge
            if shared:
                owner[k] = max(shared, key=shared.__getitem__)
            else:
                left.append(k)
        if len(left) == len(gaps):
            break  # a gap touching no owned face
        gaps = left
    merged = [shapely.coverage_union_all([faces[k] for k, o in owner.items() if o == label]) for label in labels]
    simplified = shapely.coverage_simplify(merged, TOLERANCE_M)
    out = {label: polygonal(geom) for label, geom in zip(labels, simplified, strict=True)}
    assert all(not g.is_empty for g in out.values()), [lb for lb, g in out.items() if g.is_empty]
    return out


def area_km2(geom: shapely.Geometry) -> float:
    return round(geom.area / 1e6, 1)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main(out_dir: Path = DATA) -> None:
    land = shapely.union_all([utm(f["geometry"]) for f in load(ADMIN / "overture" / "land_jateng.geojson")["features"]])
    band = box(*land.bounds).difference(land).buffer(MAX_GAP_M)  # land this close to the sea

    # Regencies (geoBoundaries ADM2); blockers are the other geoBoundaries units, so shared borders match exactly.
    # Geometry always comes from the raw sources, so a rerun does not fit an already fitted outline.
    regions = load(DATA / "regions.geojson")
    raw_adm2 = {f["properties"]["shapeID"]: f["geometry"] for f in load(ADMIN / "idn_adm2.geojson")["features"]}
    ids = [f["properties"]["shapeID"] for f in regions["features"]]
    near = box(*land.bounds).buffer(20_000)
    others = [g for i, raw in raw_adm2.items() if i not in ids and (g := utm(raw)).intersects(near)]
    fitted = tidy(fit({n: utm(raw_adm2[i]) for n, i in enumerate(ids)}, others, land, band))
    for i, f in enumerate(regions["features"]):
        f["geometry"] = lonlat(fitted[i])
    regions["coastline"] = NOTE
    save(out_dir / "regions.geojson", json.dumps(regions, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("regions", sum(area_km2(g) for g in fitted.values()), "km2")

    # Kecamatan piped coverage (GADM); blockers are the other GADM kecamatan of Jawa Tengah.
    coverage = load(DATA / "pdam_coverage.json")
    raw_adm3 = {f["properties"]["GID_3"]: f["geometry"] for f in load(ADMIN / "gadm41_adm3_jateng.geojson")["features"]}
    kec = {i: utm(raw_adm3[f["properties"]["gid"]]) for i, f in enumerate(coverage["geojson"]["features"])}
    inside = shapely.union_all(list(kec.values()))
    others = [g for raw in raw_adm3.values() if not inside.contains((g := utm(raw)).representative_point())]
    fitted = tidy(fit(kec, others, land, band))
    for i, f in enumerate(coverage["geojson"]["features"]):
        f["geometry"] = lonlat(fitted[i])
    coverage["coastline"] = NOTE
    save(out_dir / "pdam_coverage.json", json.dumps(coverage, indent=1))  # as build_pdam_coverage
    print("coverage", sum(area_km2(g) for g in fitted.values()), "km2")

    # 2022 zone map; the blocker is land the PDF shows outside the basin or beyond its frame. Opening drops the
    # unfilled slivers along the PDF coastline (between zone and sea fills), which would otherwise block the port.
    sea_path = ROOT / "realdata" / "semarang" / "zones" / "pdf_sea.geojson"
    if not sea_path.exists():
        print("skip zones: run scripts/digitise_zones.py first")  # shortcut: it writes the PDF sea and raw zones
        return
    zones = load(sea_path.with_name("zones_pdf.geojson"))
    pdf = {f["properties"]["kind"]: utm(f["geometry"]) for f in load(sea_path)["features"]}
    raw = {f["properties"]["zone"]: utm(f["geometry"]) for f in zones["features"]}
    outside = box(*land.bounds).difference(pdf["sea"]).difference(shapely.union_all(list(raw.values())))
    outside = polygonal(outside.buffer(-SLIVER_M).buffer(SLIVER_M).intersection(outside))
    fitted = tidy(fit(raw, [outside], land, band))
    for f in zones["features"]:
        geom = fitted[f["properties"]["zone"]]
        f["geometry"] = lonlat(geom)
        f["properties"]["area_km2"] = area_km2(geom)
        print("zone", f["properties"]["zone"], f["properties"]["area_km2"], "km2")
    zones["source"]["coastline"] = NOTE
    save(out_dir / "zones.geojson", json.dumps(zones))  # as digitise_zones
    upsert_source(out_dir)


def upsert_source(out_dir: Path) -> None:
    known = [s for s in load(DATA / "sources.json") if s["id"] != SOURCE["id"]]
    save(out_dir / "sources.json", json.dumps([*known, SOURCE], indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DATA)
