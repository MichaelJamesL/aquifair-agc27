"""Digitise the official 2022 groundwater conservation-zone map of CAT Semarang-Demak.

Source: Dinas ESDM Provinsi Jawa Tengah, "Peta Zona Konservasi Air Tanah Akuifer Tertekan (kedalaman
60-120 mbmt) Cekungan Air Tanah Semarang - Demak, Provinsi Jawa Tengah Tahun 2022", ArcMap vector PDF
published on Portal Data Jawa Tengah (dataset peta-konservasi-air-tanah-cat-semarang-demak-tahun-2023,
resource ad7efa82-553e-4b31-8fc8-5180df02d2a5). The PDF is vector, so the zone fills are re-drawn exactly
(no colour sampling of a scanned image); georeferencing uses the printed UTM 49S tick labels.

Writes data/zones.geojson (zone polygons), data/zone_wells.json (the map's "Sumur Bor" markers) and
realdata/semarang/zones/pdf_sea.geojson (the map's sea fill and frame) and zones_pdf.geojson (the raw zones). The
map's coastline is simplified, so run
scripts/fit_coastline.py afterwards to fit the zones to the real coastline.
Usage: python scripts/digitise_zones.py path/to/cat_semarang_demak_a0.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import fitz
import numpy as np
from pyproj import Transformer

DATA = Path(__file__).resolve().parents[1] / "data"
REAL = Path(__file__).resolve().parents[3] / "realdata" / "semarang" / "zones"
# fill colour in the PDF -> zone class (legend "KETERANGAN" of the map)
ZONES = {
    (0.451, 0.698, 1.0): "safe",  # Sub Zona Aman
    (1.0, 1.0, 0.451): "vulnerable",  # Sub Zona Rawan
    (1.0, 0.498, 0.498): "critical",  # Sub Zona Kritis
    (1.0, 0.0, 0.0): "damaged",  # Sub Zona Rusak
    (0.333, 1.0, 0.0): "recharge",  # Daerah Imbuhan Air Tanah
}
SEA = {(0.745, 0.824, 1.0): "sea"}  # the map's "Laut" fill, used by fit_coastline.py
RULES = {
    "safe": "Head above sea level and not falling. New abstraction up to 150 m3/day (>30 m) or 200 m3/day (>60 m).",
    "vulnerable": (
        "Head 0-10 m below sea level. New wells 30-90 m only for non-industrial use, max 60 m3/day; "
        ">90 m max 150 m3/day."
    ),
    "critical": (
        "Head more than 10 m below sea level. New wells 30-90 m only for non-industrial use, max 40 m3/day; "
        ">90 m max 120 m3/day."
    ),
    "damaged": (
        "No new abstraction; PDAM only, for households and industry. Permit renewals cut at least 15 %; "
        "existing wells phased out."
    ),
    "recharge": "Recharge area: abstraction only for basic daily needs and smallholder farming.",
}
ZOOM = 4.0  # 1 pt = 52.9 m on the 1:150,000 sheet, so ~13 m per pixel
MAP_CLIP = fitz.Rect(150, 360, 2365, 1350)  # inside the neat line, excludes legend swatches
TO_LONLAT = Transformer.from_crs("EPSG:32749", "EPSG:4326", always_xy=True)


def _key(fill: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(round(v, 3) for v in fill)


def georeference(page: fitz.Page) -> tuple[np.ndarray, np.ndarray]:
    """Linear fits pt -> UTM from the printed easting/northing labels (centre of each label = tick)."""
    ex, ey, ny, nv = [], [], [], []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if not text.isdigit():
                    continue
                x0, y0, x1, y1 = span["bbox"]
                if len(text) == 6 and line["dir"] == (1.0, 0.0):
                    ex.append((x0 + x1) / 2)
                    ey.append(float(text))
                elif len(text) == 7 and line["dir"] == (0.0, -1.0):
                    ny.append((y0 + y1) / 2)
                    nv.append(float(text))
    fe = np.polyfit(ex, ey, 1)
    fn = np.polyfit(ny, nv, 1)
    res_e = np.max(np.abs(np.polyval(fe, ex) - ey))
    res_n = np.max(np.abs(np.polyval(fn, ny) - nv))
    assert res_e < 60 and res_n < 60, (res_e, res_n)  # labels agree to within ~1 pt
    return fe, fn


def zone_raster(doc: fitz.Document, colours: dict = ZONES) -> np.ndarray:
    """Redraw only the given fills (in paint order) on a blank page and render without anti-aliasing."""
    page = doc[0]
    out = fitz.open()
    blank = out.new_page(width=page.rect.width, height=page.rect.height)
    shape = blank.new_shape()
    palette = {name: (i + 1) / 255 for i, name in enumerate(colours.values())}
    for path in page.get_drawings():
        fill = path.get("fill")
        if fill is None or _key(fill) not in colours or path["rect"].width < 20:
            continue  # legend swatches are tiny rectangles
        for item in path["items"]:
            if item[0] == "l":
                shape.draw_line(item[1], item[2])
            elif item[0] == "re":
                shape.draw_rect(item[1])
            elif item[0] == "qu":
                shape.draw_quad(item[1])
            elif item[0] == "c":
                shape.draw_bezier(item[1], item[2], item[3], item[4])
        grey = palette[colours[_key(fill)]]
        shape.finish(fill=(grey, grey, grey), color=None, even_odd=path.get("even_odd", True), closePath=True)
    shape.commit()
    fitz.TOOLS.set_aa_level(0)
    pix = blank.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=MAP_CLIP, colorspace=fitz.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    return img


def to_lonlat(px: np.ndarray, fe: np.ndarray, fn: np.ndarray) -> list[list[float]]:
    x_pt = MAP_CLIP.x0 + px[:, 0] / ZOOM
    y_pt = MAP_CLIP.y0 + px[:, 1] / ZOOM
    lon, lat = TO_LONLAT.transform(np.polyval(fe, x_pt), np.polyval(fn, y_pt))
    return [[round(a, 5), round(b, 5)] for a, b in zip(lon, lat, strict=True)]


def mask_polygons(mask: np.ndarray, fe: np.ndarray, fn: np.ndarray) -> list:
    """MultiPolygon coordinates (lon/lat) of a 0/1 mask; slivers under 2 ha are dropped."""
    m_per_px = abs(fe[0]) / ZOOM
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polygons: list = []
    if hierarchy is None:
        return polygons
    for j, contour in enumerate(contours):
        if hierarchy[0][j][3] != -1 or cv2.contourArea(contour) * m_per_px**2 < 20_000:
            continue  # holes are attached to their parent below; drop slivers < 2 ha
        rings = [contour]
        child = hierarchy[0][j][2]
        while child != -1:
            if cv2.contourArea(contours[child]) * m_per_px**2 >= 20_000:
                rings.append(contours[child])
            child = hierarchy[0][child][0]
        coords = []
        for ring in rings:
            ring = cv2.approxPolyDP(ring, 1.5, True).reshape(-1, 2).astype(float)
            if len(ring) < 3:
                continue
            ll = to_lonlat(ring, fe, fn)
            coords.append([*ll, ll[0]])
        if coords:
            polygons.append(coords)
    return polygons


def vectorise(img: np.ndarray, fe: np.ndarray, fn: np.ndarray) -> list[dict]:
    features = []
    m_per_px = abs(fe[0]) / ZOOM
    for i, name in enumerate(ZONES.values()):
        mask = (img == i + 1).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        polygons = mask_polygons(mask, fe, fn)
        if not polygons:
            continue
        area_km2 = float(mask.sum()) * m_per_px**2 / 1e6
        features.append(
            {
                "type": "Feature",
                "properties": {"zone": name, "rule": RULES[name], "area_km2": round(area_km2, 1)},
                "geometry": {"type": "MultiPolygon", "coordinates": polygons},
            }
        )
    return features


def wells(page: fitz.Page, fe: np.ndarray, fn: np.ndarray) -> list[dict]:
    """The red 'Sumur Bor' markers (ESRI marker font, colour e60000, 9.6 pt)."""
    found = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if span["color"] != 0xE60000 or round(span["size"], 1) != 9.6:
                    continue
                for ch in span["chars"]:
                    x0, y0, x1, y1 = ch["bbox"]
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if not MAP_CLIP.contains(fitz.Point(cx, cy)):
                        continue
                    lon, lat = TO_LONLAT.transform(np.polyval(fe, cx), np.polyval(fn, cy))
                    found.append({"lon": round(float(lon), 5), "lat": round(float(lat), 5)})
    return found


def main(pdf_path: str) -> None:
    doc = fitz.open(pdf_path)
    fe, fn = georeference(doc[0])
    img = zone_raster(doc)
    features = vectorise(img, fe, fn)
    well_points = wells(doc[0], fe, fn)
    source = {
        "source_id": "ZONE-2022",
        "title": "Peta Zona Konservasi Air Tanah Akuifer Tertekan CAT Semarang-Demak 2022",
        "accuracy_m": round(abs(fe[0]) / ZOOM * 2),
    }
    REAL.mkdir(parents=True, exist_ok=True)
    zones = json.dumps({"type": "FeatureCollection", "source": source, "features": features})
    (REAL / "zones_pdf.geojson").write_text(zones, encoding="utf-8")  # raw input of fit_coastline.py
    (DATA / "zones.geojson").write_text(zones, encoding="utf-8")
    (DATA / "zone_wells.json").write_text(
        json.dumps({"source": source, "items": well_points}, indent=1), encoding="utf-8"
    )
    h, w = img.shape
    frame = to_lonlat(np.array([[0, 0], [w, 0], [w, h], [0, h], [0, 0]], dtype=float), fe, fn)
    sea = mask_polygons((zone_raster(doc, SEA) == 1).astype(np.uint8), fe, fn)
    (REAL / "pdf_sea.geojson").write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"kind": "sea"},
                        "geometry": {"type": "MultiPolygon", "coordinates": sea},
                    },
                    {
                        "type": "Feature",
                        "properties": {"kind": "frame"},
                        "geometry": {"type": "Polygon", "coordinates": [frame]},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    for f in features:
        print(f["properties"]["zone"], f["properties"]["area_km2"], "km2", len(f["geometry"]["coordinates"]), "parts")
    print("wells", len(well_points))


if __name__ == "__main__":
    main(sys.argv[1])
