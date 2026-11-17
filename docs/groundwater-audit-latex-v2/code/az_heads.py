"""Groundwater depth-to-water measurements (USGS parameter 72019, includes ADWR GWSI data shared
with USGS) in the Arizona box, 2014-2025, from the USGS Water Data OGC API -> heads.csv."""
import json, urllib.request, csv

OUT = "C:/Kuliah/hackathon/agc-26/realdata/arizona/heads/heads.csv"
url = ("https://api.waterdata.usgs.gov/ogcapi/v0/collections/field-measurements/items?"
       "bbox=-112.1,32.6,-111.2,33.45"
       "&parameter_code=72019&limit=10000&f=json")
rows = []
while url:
    d = json.load(urllib.request.urlopen(url, timeout=300))
    for f in d.get("features", []):
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        if p["time"][:4] < "2014":
            continue
        try:
            rows.append(dict(site=p["monitoring_location_id"], time=p["time"][:10], dtw_ft=float(p["value"]),
                             lon=lon, lat=lat, agency=p.get("measuring_agency")))
        except (TypeError, ValueError):
            pass
    url = next((l["href"] for l in d.get("links", []) if l.get("rel") == "next"), None)
    print(len(rows), flush=True)
with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("sites", len({r["site"] for r in rows}), "measurements", len(rows))
