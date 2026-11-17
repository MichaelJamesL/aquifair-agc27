"""Search ALOS-1 PALSAR L1.0 scenes over the Semarang box (no login needed) and pick the
path/frame stack with the most acquisitions. Writes realdata/semarang/alos/scenes.json."""
import json, collections, time
import asf_search as asf

OUT = "/mnt/c/Kuliah/hackathon/agc-26/realdata/semarang/alos/scenes.json"
wkt = "POLYGON((110.34 -7.06,110.57 -7.06,110.57 -6.91,110.34 -6.91,110.34 -7.06))"
for k in range(5):
    try:
        res = asf.geo_search(platform=asf.PLATFORM.ALOS, intersectsWith=wkt, processingLevel="L1.0")
        break
    except Exception as e:
        print("retry", k, e)
        time.sleep(20)
rows = []
for r in res:
    p = r.properties
    rows.append(dict(name=p["sceneName"], date=p["startTime"][:10], path=p["pathNumber"], frame=p["frameNumber"],
                     orbit=p["flightDirection"], beam=p["beamModeType"], url=p["url"], size=p.get("bytes"),
                     pol=p.get("polarization")))
c = collections.Counter((x["path"], x["frame"], x["orbit"], x["beam"]) for x in rows)
print(len(rows), "scenes")
for k, v in c.most_common(10):
    ds = sorted(x["date"] for x in rows if (x["path"], x["frame"], x["orbit"], x["beam"]) == k)
    print(k, v, ds[0], ds[-1])
json.dump(rows, open(OUT, "w"), indent=1)
