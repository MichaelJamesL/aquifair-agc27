"""Module B lead builder (component S3, method M3): the four filters, no score.

1. Built after the 2022 zone map: a roof detector (gradient boosting on Sentinel-2 dry-season medians,
   trained on Microsoft building footprints vs land cover that stayed non-built 2017-2023 in the IO map)
   marks pixels that were not roof in 2022 (nor 2021) and are roof in every later year up to 2026, for
   at least two dry seasons running (bare fill and one-season flashes do not count). The first such
   year is the built year. Bare fill and fields look like roofs in Sentinel-2, so a patch must also be
   radar-bright in the last year and not in 2022 (Sentinel-1 VV; walls give double bounce, fill does not),
   when the Sentinel-1 composites exist. Connected patches of new roof are the candidate buildings.
   The detector is trained on every year's composite (labels from 2017-2023 land cover and footprints), so
   that year-to-year changes in soil moisture and crop state are not read as new roofs.
2. Footprint >= SIZE_M2 and a water-using class (factory, hotel, mall, hospital), from OpenStreetMap tags on or
   around the patch (MEASURED); else from an Overture place within 30 m (WEAK, scripts/fetch_overture_places.py);
   else from an OSM industrial-estate or retail land-use polygon (WEAK). Warehouses are dropped. A patch with no
   class in any source is kept as "unknown" when it passes filter 3: listed for a site check, not counted as a lead.
3. Inside a critical or damaged zone of the official 2022 map (data/zones.geojson).
4. Hotels, malls and hospitals only: outside the PDAM network - proxy: piped coverage of the kecamatan below
   COVERAGE_MAX (data/pdam_coverage.json); labelled as a proxy. Not applied to factories (PDAM Tirta Moedal sold
   industry 0.22 Mm3 in 2022, Perda Kota Semarang 4/2024 table 2-5, so household piped coverage says little
   about a factory) nor to unknown roofs.

Writes data/leads.json, data/lead_chips/<id>_<year>.png (before/after true colour, inspector-only API) and
realdata/semarang/leads/new_buildings.json (all filter-1 patches, used by check V5).
Usage: python scripts/build_leads.py
"""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from functools import cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from pyproj import Transformer
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"
LEADS = ROOT / "realdata" / "semarang" / "leads"
REAL = ROOT / "realdata" / "semarang"
X0, Y0, PIX, SHAPE = 415000.0, 9245000.0, 10.0, (3000, 5000)  # S2 / IO grid, row 0 = north
BASE_YEARS = (2021, 2022)  # the zone map is dated 2022
LATER_YEARS = (2023, 2024, 2025, 2026)
P_NOT_ROOF, P_ROOF = 0.35, 0.5  # per pixel; a roof must also hold for two dry seasons
SIZE_M2 = 1000
MAX_M2 = 250_000  # above 25 ha a patch is land fill, port works or a field, not a building
COVERAGE_MAX = 0.5
MAX_ELONGATION = 6.0
SEED = 20261120
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True)
TO_LL = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True)
NON_BUILT_IO = [1, 2, 4, 5, 8, 11]  # water, trees, flooded vegetation, crops, bare ground, rangeland
CLASSES = {0: "unknown", 1: "factory", 2: "hotel", 3: "mall", 4: "hospital", 9: "warehouse"}
PIPE_CHECKED = ("hotel", "mall", "hospital")  # filter 4 applies to these only
OVERTURE_FACTORY = {"manufacturer", "chemical_plant", "industrial_facility_or_service"}
SOURCE = {
    "id": "OVERTURE-PLACES",
    "name": "Overture Maps places, release 2026-11-18.0",
    "publisher": "Overture Maps Foundation",
    "url": "https://docs.overturemaps.org/guides/places/",
    "label": "WEAK",
    "accessed": "2026-11-20",
    "note": ("Points of interest with a category (CDLA-Permissive-2.0). Used for the use class of a new roof when "
             "OSM has no tag: a place within 30 m. Positions are geocoded listings, so the class is WEAK."),
}
REGENCY = {"KotaSemarang": "Kota Semarang", "Demak": "Kab. Demak", "Kendal": "Kab. Kendal", "Semarang": "Kab. Semarang",
           "Grobogan": "Kab. Grobogan"}


def pretty(name: str) -> str:
    """GADM writes "SemarangBarat" and "Gajahmungkur"; the coverage table writes "Semarang Barat", "Gajah Mungkur"."""
    return {"Gajahmungkur": "Gajah Mungkur"}.get(name) or re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def to_px(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    x, y = TO_UTM.transform(lon, lat)
    return np.c_[(np.asarray(x) - X0) / PIX, (Y0 - np.asarray(y)) / PIX]


def fill(rings: list[np.ndarray], value: int, out: np.ndarray) -> None:
    cv2.fillPoly(out, [np.round(r).astype(np.int32) for r in rings if len(r) >= 3], value)


# ---------------------------------------------------------------- layers on the 10 m grid
def zone_raster() -> np.ndarray:
    """1 critical, 2 damaged, 3 any other zone, 0 no zone (sea or outside the basin)."""
    codes = {"critical": 1, "damaged": 2}
    out = np.zeros(SHAPE, np.uint8)
    for f in json.loads((DATA / "zones.geojson").read_text(encoding="utf-8"))["features"]:
        code = codes.get(f["properties"]["zone"], 3)
        mask = np.zeros(SHAPE, np.uint8)
        for poly in f["geometry"]["coordinates"]:
            fill([to_px(*np.array(poly[0]).T)], 1, mask)
            for hole in poly[1:]:
                fill([to_px(*np.array(hole).T)], 0, mask)
        out[mask == 1] = code
    return out


def kecamatan_raster() -> tuple[np.ndarray, list[tuple[str, str]]]:
    gadm = json.loads((REAL / "admin/gadm41_adm3_semarang_demak.geojson").read_text(encoding="utf-8"))
    out = np.zeros(SHAPE, np.uint8)
    names: list[tuple[str, str]] = [("", "")]
    for f in gadm["features"]:
        p = f["properties"]
        names.append((REGENCY.get(p["NAME_2"], p["NAME_2"]), pretty(p["NAME_3"])))
        g = f["geometry"]
        for poly in g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]:
            fill([to_px(*np.array(poly[0]).T)], len(names) - 1, out)
    return out, names


def footprint_raster() -> np.ndarray:
    ms = np.load(LEADS / "ms_footprints_500.npz")
    out = np.zeros(SHAPE, np.uint8)
    rings = [to_px(*np.array(json.loads(g)).T) for g in ms["geom"]]
    fill(rings, 1, out)
    return out


def osm_class(tags: dict[str, str]) -> tuple[int, bool]:
    """(class code, specific?) - specific tags beat an industrial-estate land-use polygon."""
    b, ind = tags.get("building", ""), tags.get("industrial", "")
    if b == "warehouse" or ind in ("warehouse", "storage", "port"):
        return 9, True
    if b in ("industrial", "factory", "manufacture") or tags.get("man_made") == "works" or ind:
        return 1, True
    if tags.get("tourism") in ("hotel", "motel", "guest_house", "resort") or b == "hotel":
        return 2, True
    if tags.get("shop") in ("mall", "department_store", "supermarket") or b in ("mall", "retail", "supermarket"):
        return 3, True
    if tags.get("amenity") == "hospital" or b == "hospital" or tags.get("healthcare") == "hospital":
        return 4, True
    if tags.get("landuse") == "industrial":
        return 1, False
    if tags.get("landuse") == "retail":
        return 3, False
    return 0, False


def overture_class(place: dict) -> int:
    """Class code from an Overture place's taxonomy; offices of industrial companies do not count as factories."""
    path, name = set(place["hierarchy"] or []), (place["name"] or "").lower()
    if place["operating_status"] == "permanently_closed":
        return 0
    if "b2b_storage" in path:
        return 9
    if path & OVERTURE_FACTORY or "pabrik" in name.split():
        return 1
    if path & {"hotel", "resort"}:
        return 2
    if path & {"shopping_mall", "department_store"}:
        return 3
    if "hospital" in path:
        return 4
    return 0


def overture_raster() -> tuple[np.ndarray, list[dict]]:
    """Raster of 1-based indices into the classed Overture places, 30 m around each point."""
    path = LEADS / "overture" / "places.json"
    if not path.exists():
        return np.zeros(SHAPE, np.int32), []  # shortcut: without the download OSM is the only class source
    places = [p for p in json.loads(path.read_text(encoding="utf-8"))["items"] if overture_class(p)]
    out = np.zeros(SHAPE, np.int32)
    px = to_px(np.array([p["lon"] for p in places]), np.array([p["lat"] for p in places]))
    for i, (c, r) in enumerate(px, start=1):
        cv2.circle(out, (round(c), round(r)), 3, i, -1)  # cv2 draws int32 with the exact index
    return out, places


def osm_rasters() -> tuple[np.ndarray, np.ndarray, dict[int, str]]:
    """Specific-tag class raster, land-use class raster, and a raster of OSM feature indices for names."""
    elements = json.loads((LEADS / "osm_classes.json").read_text(encoding="utf-8"))["elements"]
    specific = np.zeros(SHAPE, np.uint8)
    landuse = np.zeros(SHAPE, np.uint8)
    names: dict[int, str] = {}
    # land use first, then buildings and points on top in their own raster
    for e in sorted(elements, key=lambda e: e["type"] != "relation"):
        code, is_specific = osm_class(e.get("tags", {}))
        if code == 0:
            continue
        target = specific if is_specific else landuse
        if e["type"] == "node":
            c, r = to_px(np.array([e["lon"]]), np.array([e["lat"]]))[0]
            cv2.circle(target, (round(c), round(r)), 3, code, -1)  # 30 m around a tagged point
        elif e["type"] == "way" and "geometry" in e:
            ring = to_px(np.array([g["lon"] for g in e["geometry"]]), np.array([g["lat"] for g in e["geometry"]]))
            fill([ring], code, target)
        elif e["type"] == "relation":
            for m in e.get("members", []):
                if m.get("role") == "outer" and "geometry" in m:
                    geo = m["geometry"]
                    ring = to_px(np.array([g["lon"] for g in geo]), np.array([g["lat"] for g in geo]))
                    fill([ring], code, target)
        if e.get("tags", {}).get("name") and is_specific:
            names[e["id"]] = e["tags"]["name"]
    return specific, landuse, names


def road_raster() -> np.ndarray:
    out = np.zeros(SHAPE, np.uint8)
    path = LEADS / "osm_roads.json"
    if not path.exists():
        return out  # shortcut: without the road layer only the elongation test removes roads
    for e in json.loads(path.read_text(encoding="utf-8"))["elements"]:
        if "geometry" not in e:
            continue
        line = to_px(np.array([g["lon"] for g in e["geometry"]]), np.array([g["lat"] for g in e["geometry"]]))
        major = e["tags"].get("highway") in ("motorway", "trunk", "construction") or "aeroway" in e["tags"]
        cv2.polylines(out, [np.round(line).astype(np.int32)], False, 1, thickness=4 if major else 2)
    return out


# ---------------------------------------------------------------- roof detector
def features(year: int) -> tuple[np.ndarray, np.ndarray]:
    s = np.load(LEADS / f"s2_{year}.npz")
    b = {k: s[k].astype(np.float32) / 10000 for k in ("B02", "B03", "B04", "B08", "B11", "B12")}
    eps = 1e-6
    ndvi = (b["B08"] - b["B04"]) / (b["B08"] + b["B04"] + eps)
    ndbi = (b["B11"] - b["B08"]) / (b["B11"] + b["B08"] + eps)
    mndwi = (b["B03"] - b["B11"]) / (b["B03"] + b["B11"] + eps)
    x = np.stack([*b.values(), ndvi, ndbi, mndwi], axis=-1)
    valid = (s["clear_count"] >= 2) & (s["B04"] > 0)
    return x, valid


def train(fp: np.ndarray) -> tuple[HistGradientBoostingClassifier, dict]:
    io = np.load(LEADS / "io_lulc_2017_2023.npz")
    stack = np.stack([io[f"y{y}"] for y in range(2017, 2024)])
    stable_non_built = np.isin(stack, NON_BUILT_IO).all(0) & (stack == stack[0]).all(0)
    near_fp = cv2.dilate(fp, np.ones((7, 7), np.uint8)) > 0
    roof = cv2.erode(fp, np.ones((3, 3), np.uint8)) > 0
    rng = np.random.default_rng(SEED)
    xs, ys, cols = [], [], []
    # Every year, not only the base years: a dry year turns fields into bright bare soil, and a detector
    # that only saw wet 2021-22 calls that soil "roof" (40 % of the map in 2026 instead of 19 %).
    years = [y for y in (*BASE_YEARS, *LATER_YEARS) if (LEADS / f"s2_{y}.npz").exists()]
    for year in years:
        x, valid = features(year)
        for label, mask, n in ((1, roof & valid, 80_000 // len(years)), (0, stable_non_built & ~near_fp & valid,
                                                                         120_000 // len(years))):
            r, c = np.nonzero(mask)
            pick = rng.choice(len(r), size=min(n, len(r)), replace=False)
            xs.append(x[r[pick], c[pick]])
            ys.append(np.full(len(pick), label))
            cols.append(c[pick])
    X, y, col = np.concatenate(xs), np.concatenate(ys), np.concatenate(cols)
    west = col < 2500  # spatial hold-out: train west of 440 000 E, test east
    held = HistGradientBoostingClassifier(max_iter=200, random_state=SEED).fit(X[west], y[west])
    pred = held.predict(X[~west])
    stats = {
        "holdout": "trained west of 440,000 E, tested east of it",
        "accuracy": round(float((pred == y[~west]).mean()), 3),
        "roof_recall": round(float((pred[y[~west] == 1] == 1).mean()), 3),
        "non_roof_specificity": round(float((pred[y[~west] == 0] == 0).mean()), 3),
        "samples": len(y),
    }
    return HistGradientBoostingClassifier(max_iter=200, random_state=SEED).fit(X, y), stats


def roof_probability(model: HistGradientBoostingClassifier, year: int) -> np.ndarray:
    x, valid = features(year)
    p = np.full(SHAPE, np.nan, np.float32)
    r, c = np.nonzero(valid)
    for i in range(0, len(r), 2_000_000):
        p[r[i:i + 2_000_000], c[i:i + 2_000_000]] = model.predict_proba(x[r[i:i + 2_000_000], c[i:i + 2_000_000]])[:, 1]
    return p


# ---------------------------------------------------------------- radar check (Sentinel-1)
def edge_p90(vv: np.ndarray, sub: np.ndarray, x: int, y: int, ring: bool = True) -> float:
    """90th percentile VV (dB) over a patch and a 1-pixel ring: walls give bright double bounce at the edge.
    Without the ring (for "was it built before?") so walls of older neighbours do not count."""
    grown = cv2.dilate(np.pad(sub, 1), np.ones((3, 3), np.uint8) if ring else np.ones((1, 1), np.uint8)) > 0
    rr, cc = np.nonzero(grown)
    rr, cc = rr + y - 1, cc + x - 1
    ok = (rr >= 0) & (rr < SHAPE[0]) & (cc >= 0) & (cc < SHAPE[1])
    vals = vv[rr[ok], cc[ok]]
    vals = vals[vals != 0]
    return float(np.percentile(vals, 90)) if len(vals) else float("nan")


def radar_threshold(fp: np.ndarray, vv: np.ndarray, sample: int = 3000) -> float:
    """VV level that 90 % of known buildings of lead size (Microsoft footprints, 0.1-25 ha) reach."""
    _, lab, st, _ = cv2.connectedComponentsWithStats(fp.astype(np.uint8), connectivity=8)
    sizes = st[1:, cv2.CC_STAT_AREA]
    ids = np.nonzero((sizes >= SIZE_M2 / PIX**2) & (sizes <= MAX_M2 / PIX**2))[0] + 1
    ids = np.random.default_rng(SEED).choice(ids, size=min(sample, len(ids)), replace=False)
    vals = []
    for i in ids:
        x, y, w, h = st[i, :4]
        vals.append(edge_p90(vv, (lab[y:y + h, x:x + w] == i).astype(np.uint8), int(x), int(y)))
    return float(np.nanpercentile(vals, 10))


# ---------------------------------------------------------------- chips for the lead card
@cache
def s2_rgb(year: int) -> np.ndarray:
    s = np.load(LEADS / f"s2_{year}.npz")
    return np.stack([s[k] for k in ("B04", "B03", "B02")], -1)


def chip(year: int, r: int, c: int, contour: np.ndarray | None, half: int = 32) -> Image.Image:
    r0, c0 = max(0, r - half), max(0, c - half)
    rgb = s2_rgb(year)[r0:r0 + 2 * half, c0:c0 + 2 * half].astype(np.float32)
    rgb = np.clip((rgb / 10000 / 0.3) ** (1 / 1.8), 0, 1)
    img = np.ascontiguousarray((rgb * 255).astype(np.uint8))
    if contour is not None:
        cv2.polylines(img, [contour - [c0, r0]], True, (255, 230, 0), 1)
    return Image.fromarray(img)  # 64 px at 10 m; the card scales it up with pixelated rendering


def pdam_status(use_class: str, district: str, cov: dict | None) -> str:
    share = f"{cov['coverage']:.0%} household piped coverage in {district}, {cov['year']}" if cov else (
        f"no piped-coverage data for {district}")
    if use_class in PIPE_CHECKED:
        return f"Outside the network (proxy): {share}"
    if use_class == "factory":
        return f"Not checked for factories (PDAM sold industry 0.22 Mm3 in 2022); {share}"
    if use_class == "unknown":
        return f"Not checked while the class is unknown; {share}"
    return f"Not checked: a {use_class} is not a water-using class; {share}"


def main() -> None:
    zones, (kec, kec_names) = zone_raster(), kecamatan_raster()
    fp = footprint_raster()
    specific, landuse, _ = osm_rasters()
    poi_idx, places = overture_raster()
    roads = road_raster()
    coverage = {(row["regency"], row["kecamatan"]): row
                for row in json.loads((DATA / "pdam_coverage.json").read_text(encoding="utf-8"))["items"]}
    bundle = np.load(REAL / "sx/bundle.npz")
    sink, e0, n0, pix = bundle["D_d2326"], float(bundle["E0"]), float(bundle["N0"]), float(bundle["PIX"])

    model, stats = train(fp)
    print("detector", stats, flush=True)
    years = [y for y in (*BASE_YEARS, *LATER_YEARS) if (LEADS / f"s2_{y}.npz").exists()]
    later = [y for y in LATER_YEARS if y in years]
    assert 2022 in years and later and later[-1] == 2026, years
    p = {y: roof_probability(model, y) for y in years}
    # Same detector, every year: existing roofs should stay roof and stable land should stay not-roof.
    roof_px = cv2.erode(fp, np.ones((3, 3), np.uint8)) > 0
    per_year = {
        str(y): {
            "clear_share": round(float(np.isfinite(p[y]).mean()), 3),
            "footprints_called_roof": round(float(np.nanmean(p[y][roof_px] >= P_ROOF)), 3),
            "roof_share_all": round(float(np.nanmean(p[y] >= P_ROOF)), 3),
        }
        for y in years
    }
    print("per year", per_year, flush=True)

    base_ok = p[2022] < P_NOT_ROOF
    if 2021 in p:
        base_ok &= ~(p[2021] >= P_NOT_ROOF)  # NaN (cloudy) in 2021 does not veto
    built_year = np.zeros(SHAPE, np.int16)
    persistent = np.ones(SHAPE, bool)
    for y in reversed(later):  # earliest year from which the pixel stays roof
        persistent &= p[y] >= P_ROOF
        built_year[persistent] = y
    # A roof must hold for at least two dry seasons running (built by the second-last year), so bare fill and
    # one-season flashes do not count; with a single later year this cannot be checked and is skipped.
    last_allowed = later[-2] if len(later) >= 2 else later[-1]
    new = base_ok & (built_year > 0) & (built_year <= last_allowed)
    np.savez_compressed(LEADS / "roof_p.npz", **{f"y{y}": p[y].astype(np.float16) for y in years})

    radar = None
    if all((LEADS / f"s1_{y}.npz").exists() for y in (2022, later[-1])):
        vv = {y: np.load(LEADS / f"s1_{y}.npz")["vv_db"] / 100.0 for y in (2022, later[-1])}
        radar = {"threshold_db": round(radar_threshold(fp, vv[later[-1]]), 2)}
        print("radar threshold", radar, flush=True)

    chips = DATA / "lead_chips"
    shutil.rmtree(chips, ignore_errors=True)
    chips.mkdir()
    n, lab, cc_stats, _ = cv2.connectedComponentsWithStats(new.astype(np.uint8), connectivity=8)
    funnel = Counter()
    radar_dropped: list[dict] = []  # for checking the radar rule by eye, not used by the API
    candidates, leads = [], []
    for i in range(1, n):
        area_m2 = int(cc_stats[i, cv2.CC_STAT_AREA] * PIX * PIX)
        if area_m2 < SIZE_M2:
            continue
        x, y, w, h = cc_stats[i, :4]
        sub = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea) + [x, y]  # noqa: RUF005 - numpy offset, not list concat
        (_, _), (rw, rh), _ = cv2.minAreaRect(contour)
        on_road = roads[y:y + h, x:x + w][sub == 1].mean()
        if max(rw, rh) / max(1.0, min(rw, rh)) > MAX_ELONGATION or on_road > 0.3:
            funnel["dropped_road_like"] += 1
            continue
        rr, cc = np.nonzero(sub)
        rows, cols = rr + y, cc + x
        if area_m2 > MAX_M2:
            funnel["dropped_too_large"] += 1
            continue
        if fp[rows, cols].mean() >= 0.5:  # a pre-2023 Microsoft footprint contradicts "new"
            funnel["dropped_existing_footprint"] += 1
            continue
        if radar is not None:  # Sentinel-1: a roof is radar-bright now and was not before
            now = edge_p90(vv[later[-1]], sub, int(x), int(y))
            before = edge_p90(vv[2022], sub, int(x), int(y), ring=False)
            reason = ("dropped_radar_not_building" if now < radar["threshold_db"] else
                      "dropped_radar_built_before" if before >= radar["threshold_db"] else None)
            if reason:
                funnel[reason] += 1
                radar_dropped.append({"E": round(X0 + (np.median(cols) + 0.5) * PIX),
                                      "N": round(Y0 - (np.median(rows) + 0.5) * PIX),
                                      "area_m2": area_m2, "reason": reason, "vv_now": round(now, 1),
                                      "vv_2022": round(before, 1)})
                continue
        r_c, c_c = int(np.median(rows)), int(np.median(cols))
        easting, northing = X0 + (c_c + 0.5) * PIX, Y0 - (r_c + 0.5) * PIX
        lon, lat = TO_LL.transform(easting, northing)
        in_zone = [v for v in zones[rows, cols].tolist() if v]  # a shoreline roof takes the zone of its land part
        zone_code = Counter(in_zone).most_common(1)[0][0] if in_zone else 0
        zone = {1: "critical", 2: "damaged"}.get(zone_code)
        ring = cv2.dilate(sub, np.ones((7, 7), np.uint8))  # 30 m around the patch for tagged points
        rr2, cc2 = np.nonzero(ring)
        rr2, cc2 = np.clip(rr2 + y - 3, 0, SHAPE[0] - 1), np.clip(cc2 + x - 3, 0, SHAPE[1] - 1)
        spec = [v for v in specific[rr2, cc2].tolist() if v]
        land = [v for v in landuse[rows, cols].tolist() if v]
        near = [places[i - 1] for i in sorted(set(poi_idx[rows, cols].tolist()) - {0})]
        if spec:
            code, basis, cls_label = Counter(spec).most_common(1)[0][0], "OSM building or point tag", "MEASURED"
        elif near:
            code = Counter(overture_class(p) for p in near).most_common(1)[0][0]
            place = next(p for p in near if overture_class(p) == code)
            basis, cls_label = f"Overture place within 30 m: {place['name']} ({place['category']})", "WEAK"
        elif land:
            code, basis, cls_label = Counter(land).most_common(1)[0][0], "inside an OSM industrial/retail area", "WEAK"
        else:
            code, basis, cls_label = 0, "no tag in OpenStreetMap or Overture places", "MISSING"
        use_class = CLASSES[code]
        kec_code = Counter(kec[rows, cols].tolist()).most_common(1)[0][0]
        if kec_code == 0:  # reclaimed port land outside the GADM coastline: nearest kecamatan within 1 km
            top, left = max(0, r_c - 100), max(0, c_c - 100)
            wr, wc = np.nonzero(kec[top:r_c + 100, left:c_c + 100])
            if len(wr):
                k = int(np.argmin((wr + top - r_c) ** 2 + (wc + left - c_c) ** 2))
                kec_code = int(kec[wr[k] + top, wc[k] + left])
        regency, district = kec_names[kec_code]
        cov = coverage.get((regency, district))
        b_year = int(Counter(built_year[rows, cols].tolist()).most_common(1)[0][0])
        f2 = use_class in ("factory", *PIPE_CHECKED)
        f3 = zone is not None
        f4 = use_class not in PIPE_CHECKED or (cov is not None and cov["coverage"] < COVERAGE_MAX)
        candidates.append({"E": round(easting), "N": round(northing), "area_m2": area_m2, "zone": zone,
                           "use_class": use_class, "built_year": b_year, "f2": f2, "f3": f3, "f4": f4,
                           "p_before": round(float(np.nanmean(p[2022][rows, cols])), 3),
                           "p_after": round(float(np.nanmean(p[later[-1]][rows, cols])), 3)})
        funnel["f1"] += 1
        funnel["f1_f2"] += f2
        funnel["f1_f2_f3"] += f2 and f3
        funnel["f1_f2_f3_f4"] += f2 and f3 and f4
        funnel["unknown_f3"] += use_class == "unknown" and f3
        si, sj = int((northing - n0) // pix), int((easting - e0) // pix)
        sinking = None
        if 0 <= si < sink.shape[0] and 0 <= sj < sink.shape[1] and np.isfinite(sink[si, sj]):
            sinking = round(float(sink[si, sj]), 1)
        lead_id = f"L-{round(easting / 10)}-{round(northing / 10)}"
        poly_ll = [[round(a, 6), round(b, 6)] for a, b in zip(*TO_LL.transform(
            X0 + (contour[:, 0, 0] + 0.5) * PIX, Y0 - (contour[:, 0, 1] + 0.5) * PIX), strict=True)]
        leads.append({
            "id": lead_id,
            "district": district,
            "regency": regency,
            "lon": round(lon, 6),
            "lat": round(lat, 6),
            "footprint_m2": area_m2,
            "polygon": [*poly_ll, poly_ll[0]],
            "built_year": b_year,
            "use_class": use_class,
            "use_class_basis": basis,
            "zone": zone,
            # every candidate is kept so the UI can show each funnel step; None = filter not applied to this class
            "filters": {"1": True, "2": f2, "3": f3, "4": f4 if use_class in PIPE_CHECKED else None},
            "pdam_status": pdam_status(use_class, district, cov),
            "pdam_coverage": cov and cov["coverage"],
            "sinking_mm_yr": sinking,
            "source_ids": sorted({"S2-L2A", "MS-BUILDINGS", "IO-LULC", "OSM", "ZONE-2022", "GADM", "LICSAR",
                                  *(["S1-RTC"] if radar else []), *(cov["source_ids"] if cov else []),
                                  *(["OVERTURE-PLACES"] if places and cls_label != "MEASURED" else []),
                                  *([] if use_class in PIPE_CHECKED else ["PERDA-SMG-2024"])}),
            "labels": {"built_year": "MEASURED", "footprint_m2": "MEASURED", "use_class": cls_label,
                       **({"zone": "OFFICIAL"} if zone else {}),
                       "pdam_status": "WEAK" if use_class in PIPE_CHECKED else "MISSING",
                       "sinking_mm_yr": "MEASURED"},
        })
        for year in (2022, 2026):
            chip(year, r_c, c_c, contour if year == 2026 else None).save(chips / f"{lead_id}_{year}.png", optimize=True)

    assert len({d["id"] for d in leads}) == len(leads), "lead ids must be unique"
    leads.sort(key=lambda d: (d["district"], d["id"]))
    out = {
        "status": "available",
        "reason": None,
        "method": {
            "period": ("Sentinel-2 dry seasons (June-October) 2021-2026; new = not roof in 2021-22, "
                       "roof in every dry season from the built year on, for at least two seasons"),
            "detector": stats,
            "per_year": per_year,
            "roof_probability": {"not_roof_before": P_NOT_ROOF, "roof_after": P_ROOF},
            "size_threshold_m2": SIZE_M2,
            "pdam_coverage_max": COVERAGE_MAX,
            "pixel_m": PIX,
            "dropped": {
                "road_or_runway_shape": funnel["dropped_road_like"],
                "larger_than_25_ha": funnel["dropped_too_large"],
                "already_in_microsoft_footprints": funnel["dropped_existing_footprint"],
                "radar_not_a_building_now": funnel["dropped_radar_not_building"],
                "radar_building_already_in_2022": funnel["dropped_radar_built_before"],
            },
            "radar": radar and {
                **radar,
                "source": "Sentinel-1 RTC VV, relative orbit 76 descending, dry-season median",
                "rule": ("90th percentile VV over the patch and a 1-pixel ring must reach the level 90 % of "
                         "known buildings of lead size reach in the last year; inside the patch it must not "
                         "reach it in 2022"),
            },
            "class_sources": ("OSM tag on or within 30 m of the patch (MEASURED); else an Overture place within "
                              "30 m (WEAK); else an OSM industrial or retail land-use area (WEAK); else unknown"),
            "note": ("Footprint is the new-roof patch on 10 m pixels (about +/- 1 pixel at the edges); a patch can "
                     "hold more than one building. Filter 4 uses kecamatan piped coverage until PDAM releases "
                     "coverage per kelurahan, and applies to hotels, malls and hospitals only: PDAM Tirta Moedal "
                     "sold industry 0.22 Mm3 in 2022 (Perda Kota Semarang 4/2024, table 2-5)."),
        },
        "funnel": [
            {"step": "1", "label": f"New roof since 2022, at least {SIZE_M2:,} m2", "count": funnel["f1"]},
            {"step": "1-2", "label": "... in a water-using class (factory, hotel, mall, hospital)",
             "count": funnel["f1_f2"]},
            {"step": "1-3", "label": "... inside a critical or damaged zone", "count": funnel["f1_f2_f3"]},
            {"step": "1-4", "label": (f"... and for hotels, malls and hospitals, kecamatan piped coverage below "
                                      f"{COVERAGE_MAX:.0%} (proxy; not applied to factories)"),
             "count": funnel["f1_f2_f3_f4"]},
            {"step": "unknown", "label": ("Class unknown (no tag in OSM or Overture places), inside a critical or "
                                          "damaged zone: listed for a site check, not counted as leads"),
             "count": funnel["unknown_f3"]},
        ],
        "items": leads,
    }
    (DATA / "leads.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (LEADS / "new_buildings.json").write_text(json.dumps(candidates), encoding="utf-8")
    (LEADS / "radar_dropped.json").write_text(json.dumps(radar_dropped), encoding="utf-8")
    known = [s for s in json.loads((DATA / "sources.json").read_text(encoding="utf-8")) if s["id"] != SOURCE["id"]]
    text = json.dumps([*known, SOURCE], indent=2, ensure_ascii=False) + "\n"
    (DATA / "sources.json").write_text(text, encoding="utf-8")
    print(json.dumps(out["funnel"], indent=1), json.dumps(out["method"]["dropped"]))
    print(Counter((d["district"], d["use_class"]) for d in leads))


if __name__ == "__main__":
    main()
