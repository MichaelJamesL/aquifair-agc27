"""Run the pre-registered checks V5, V7 and V8 (see prereg_v5_v7_v8.md) and write data/check_results.json.

V7: SPAM Semarang Barat difference-in-differences on the Sentinel-1 rate maps, with placebos.
V8: the same test on a known metered pumping cut in Arizona (positive control).
V5: leads vs permitted wells (needs data/leads.json from build_leads.py).
V4: Arizona retro test (needs realdata/arizona/v4 from fetch_az_v4.py).
Usage: python scripts/run_checks.py [--only=V4,V5,V7,V8] [--v5-only]
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"
REAL = ROOT / "realdata"
SEED = 20261120
DRAWS = 1000


def quintile_strata(clay: np.ndarray, built: np.ndarray, valid: np.ndarray) -> np.ndarray:
    def q(a: np.ndarray) -> np.ndarray:
        edges = np.nanpercentile(a[valid], [20, 40, 60, 80])
        return np.digitize(a, edges)

    return np.where(valid, q(clay) * 5 + q(built), -1)


def did(change: np.ndarray, served: np.ndarray, strata: np.ndarray, valid: np.ndarray) -> float:
    """Served-count-weighted mean over strata of (served mean change - control mean change)."""
    s, c = served & valid, ~served & valid
    num = den = 0.0
    for k in np.unique(strata[s]):
        ins, inc = s & (strata == k), c & (strata == k)
        if ins.sum() == 0 or inc.sum() == 0:
            continue
        num += ins.sum() * (change[ins].mean() - change[inc].mean())
        den += ins.sum()
    return num / den if den else float("nan")


def shifted(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros_like(mask)
    ny, nx = mask.shape
    ys, xs = np.nonzero(mask)
    ys, xs = ys + dy, xs + dx
    keep = (ys >= 0) & (ys < ny) & (xs >= 0) & (xs < nx)
    out[ys[keep], xs[keep]] = True
    return out


def shift_null(change: np.ndarray, served: np.ndarray, strata: np.ndarray, valid: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    need = 0.6 * (served & valid).sum()
    sims: list[float] = []
    while len(sims) < DRAWS:
        dy, dx = rng.integers(10, 41, size=2) * rng.choice([-1, 1], size=2)
        moved = shifted(served, int(dy), int(dx))
        if (moved & valid).sum() < need:
            continue
        sims.append(did(change, moved, strata, valid))
    return np.array(sims)


def test(change: np.ndarray, served: np.ndarray, strata: np.ndarray, valid: np.ndarray) -> dict:
    delta = did(change, served, strata, valid)
    null = shift_null(change, served, strata, valid)
    return {
        "delta_mm_yr": round(float(delta), 2),
        "null_p05": round(float(np.percentile(null, 5)), 2),
        "null_p95": round(float(np.percentile(null, 95)), 2),
        "p_lower": round(float((null <= delta).mean()), 3),
        "served_cells": int((served & valid).sum()),
    }


def kecamatan_mask(names: set[str], e0: float, n0: float, pix: float, shape: tuple[int, int]) -> np.ndarray:
    gadm = json.loads((REAL / "semarang/admin/gadm41_adm3_semarang_demak.geojson").read_text())
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True)
    ny, nx = shape
    xx, yy = np.meshgrid(e0 + (np.arange(nx) + 0.5) * pix, n0 + (np.arange(ny) + 0.5) * pix)
    pts = np.c_[xx.ravel(), yy.ravel()]
    mask = np.zeros(ny * nx, dtype=bool)
    for f in gadm["features"]:
        p = f["properties"]
        if p["NAME_2"] != "KotaSemarang" or p["NAME_3"] not in names:
            continue
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = np.array(poly[0])
            x, y = to_utm.transform(ring[:, 0], ring[:, 1])
            mask |= MplPath(np.c_[x, y]).contains_points(pts)
    return mask.reshape(shape)


def v7() -> dict:
    b = np.load(REAL / "semarang/sx/bundle.npz")
    e0, n0, pix = float(b["E0"]), float(b["N0"]), float(b["PIX"])
    v1517, v1822, v2326 = (b[k].astype(float) for k in ("D_d1517", "D_d1822", "D_d2326"))
    valid = np.isfinite(v1517) & np.isfinite(v1822) & np.isfinite(v2326) & np.isfinite(b["clay_m"])
    strata = quintile_strata(b["clay_m"], b["wc_built"], valid)
    served = kecamatan_mask({"SemarangBarat", "Tugu", "Ngaliyan"}, e0, n0, pix, valid.shape)
    placebo_area = kecamatan_mask({"Genuk", "Pedurungan", "Gayamsari"}, e0, n0, pix, valid.shape)
    main = test(v2326 - v1822, served, strata, valid)
    years = test(v1822 - v1517, served, strata, valid)
    area = test(v2326 - v1822, placebo_area, strata, valid)
    s = served & valid
    means = {k: round(float(np.mean(v[s])), 1) for k, v in (("2014_17", v1517), ("2018_22", v1822), ("2023_26", v2326))}
    c = ~served & valid
    ctrl = {k: round(float(np.mean(v[c])), 1) for k, v in (("2014_17", v1517), ("2018_22", v1822), ("2023_26", v2326))}

    def inside(r: dict) -> bool:
        return r["null_p05"] <= r["delta_mm_yr"] <= r["null_p95"]

    return {
        "main": main,
        "placebo_years": years,
        "placebo_area": area,
        "placebo_year_clean": inside(years),
        "placebo_area_clean": inside(area),
        "passed": bool(main["delta_mm_yr"] < main["null_p05"] and inside(years) and inside(area)),
        "served_mean_mm_yr": means,
        "control_mean_mm_yr": ctrl,
        "grid": {"e0": e0, "n0": n0, "pix": pix, "epsg": 32749},
    }


def v8() -> dict:
    a = REAL / "arizona"
    p1, p2 = np.load(a / "opera_rate_200m_P1.npz"), np.load(a / "opera_rate_200m_P2.npz")
    e0, n0, pix = float(p1["E0"]), float(p1["N0"]), float(p1["PIX"])
    valid = p1["mask"].astype(bool) & p2["mask"].astype(bool)
    change = np.where(valid, p2["D"].astype(float) - p1["D"].astype(float), np.nan)
    clay = np.load(a / "clay_200m.npz")["clay_m"].astype(float)
    built = np.load(a / "features_200m.npz")["wc_built"].astype(float)
    valid &= np.isfinite(clay) & np.isfinite(built)
    strata = quintile_strata(clay, built, valid)

    w = pd.read_csv(a / "pump_all.csv", dtype={"REGISTRY_ID": str})
    w["q1"] = w[[str(y) for y in range(2016, 2021)]].fillna(0).mean(axis=1)
    w["q2"] = w[[str(y) for y in range(2021, 2026)]].fillna(0).mean(axis=1)
    ny, nx = valid.shape
    block = int(4000 // pix)
    bx = ((w["UTM_X_METERS"] - e0) // (block * pix)).astype(int)
    by = ((w["UTM_Y_METERS"] - n0) // (block * pix)).astype(int)
    inside = (bx >= 0) & (by >= 0) & (bx < -(-nx // block)) & (by < -(-ny // block))
    blocks = w[inside].groupby([by[inside], bx[inside]])[["q1", "q2"]].sum()
    pumped = blocks[blocks.q1 > 0]
    big = pumped[pumped.q1 >= pumped.q1.median()]
    cut = big[big.q2 <= 0.5 * big.q1]
    served = np.zeros_like(valid)
    for (iy, ix) in cut.index:
        served[iy * block : (iy + 1) * block, ix * block : (ix + 1) * block] = True
    if not served.any():
        return {"ran": False, "reason": "no 4 km block with a >= 50 % metered cut"}
    result = test(np.nan_to_num(change), served, strata, valid)
    return {
        "ran": True,
        "cut_blocks": len(cut),
        "pumped_blocks": len(pumped),
        "cut_acre_ft_yr": [round(float(cut.q1.sum())), round(float(cut.q2.sum()))],
        "main": result,
        "passed": bool(result["delta_mm_yr"] < result["null_p05"]),
    }


def v5(radius_m: float = 250, draws: int = 10_000) -> dict:
    """Leads (filters 1-3) vs size-matched new buildings in the same zones: share within 250 m of a permitted well."""
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32749", always_xy=True)
    zone_wells = json.loads((DATA / "zone_wells.json").read_text(encoding="utf-8"))["items"]
    zx, zy = to_utm.transform([w["lon"] for w in zone_wells], [w["lat"] for w in zone_wells])
    lo = pd.read_csv(REAL / "semarang/registry_wells/fig12_wells.csv")
    wells = np.r_[np.c_[zx, zy], lo[["E", "N"]].to_numpy()]
    b = pd.DataFrame(json.loads((REAL / "semarang/leads/new_buildings.json").read_text(encoding="utf-8")))
    pool = b[b.f3].reset_index(drop=True)
    if pool.empty:
        return {"ran": False, "reason": "not run: no new building in a critical or damaged zone"}
    d = np.sqrt(((pool[["E", "N"]].to_numpy()[:, None, :] - wells[None, :, :]) ** 2).sum(-1)).min(1)
    pool["hit"] = d <= radius_m
    pool["q"] = pd.qcut(pool.area_m2.rank(method="first"), 5, labels=False) if len(pool) >= 5 else 0
    leads = pool[pool.f2]
    if len(leads) < 5:
        return {"ran": False, "reason": f"not run: too few leads ({len(leads)}) for the permit-overlap test"}
    rng = np.random.default_rng(SEED)
    null = np.zeros(draws)
    for q, n in leads.q.value_counts().items():
        hits = pool.hit[pool.q == q].to_numpy()
        null += rng.choice(hits, size=(draws, n), replace=True).sum(1)
    null /= len(leads)
    share = float(leads.hit.mean())
    p = float((np.sum(null >= share) + 1) / (draws + 1))
    return {
        "ran": True,
        "radius_m": radius_m,
        "wells": len(wells),
        "leads": len(leads),
        "lead_hits": int(leads.hit.sum()),
        "lead_share": round(share, 4),
        "pool": len(pool),
        "null_share": round(float(null.mean()), 4),
        "null_p95": round(float(np.percentile(null, 95)), 4),
        "p": round(p, 4),
        "passed": bool(share > null.mean() and p < 0.05),
    }


def v4(radius_m: float = 500, draws: int = 10_000) -> dict:
    """Arizona retro test: do new large buildings outside water-provider areas get a new well nearby?"""
    import cv2
    from scipy.spatial import cKDTree

    d = REAL / "arizona" / "v4"
    io = np.load(d / "io_lulc.npz")
    e0, n1, pix = float(io["e0"]), float(io["n1"]), float(io["pix"])
    years = list(range(2017, 2024))
    cover = np.stack([io[f"y{y}"] for y in years])
    built, valid = cover == 7, (cover > 0).all(0)  # IO class 7 = built area
    served = np.zeros(valid.shape, np.uint8)
    for f in json.loads((d / "cws.json").read_text(encoding="utf-8")):
        rings = [np.round((np.array(r) - [e0, n1]) / [pix, -pix]).astype(np.int32) for r in f["geometry"]["rings"]]
        cv2.fillPoly(served, rings, 1)
    outside = valid & (served == 0)

    w = pd.DataFrame(json.loads((d / "wells55.json").read_text(encoding="utf-8")))
    w = w[w.WELL_CANCELLED.fillna("N") != "Y"]
    w["year"] = pd.to_datetime(w.INSTALLED.fillna(w.APPROVED), unit="ms").dt.year
    w = w.dropna(subset=["year", "UTM_X_METERS", "UTM_Y_METERS"])

    def hits(rows: np.ndarray, cols: np.ndarray, t: int) -> np.ndarray:
        dated = w[(w.year >= t) & (w.year <= t + 2)]
        if dated.empty:
            return np.zeros(len(rows), bool)
        tree = cKDTree(dated[["UTM_X_METERS", "UTM_Y_METERS"]].to_numpy())
        pts = np.c_[e0 + (cols + 0.5) * pix, n1 - (rows + 0.5) * pix]
        return np.isfinite(tree.query(pts, distance_upper_bound=radius_m)[0])

    rng = np.random.default_rng(SEED)
    stable = np.nonzero(built.all(0) & outside)
    pool_pick = rng.choice(len(stable[0]), size=min(200_000, len(stable[0])), replace=False)
    pool_r, pool_c = stable[0][pool_pick], stable[1][pool_pick]
    new_rows: list[tuple[int, int, int, float]] = []
    pools: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for t in range(2018, 2022):
        i = t - 2017
        new = valid & ~built[:i].any(0) & built[i:].all(0)
        n, lab, st, _ = cv2.connectedComponentsWithStats(new.astype(np.uint8), connectivity=8)
        share = cv2.blur(built[i - 1].astype(np.float32), (101, 101))  # built share within ~1 km, year t-1
        for k in range(1, n):
            if not 1000 <= st[k, cv2.CC_STAT_AREA] * pix * pix <= 250_000:
                continue
            x, y, ww, hh = st[k, :4]
            rr, cc = np.nonzero(lab[y:y + hh, x:x + ww] == k)
            r, c = int(np.median(rr)) + y, int(np.median(cc)) + x
            if outside[r, c]:
                new_rows.append((t, r, c, float(share[r, c])))
        pools[t] = (share[pool_r, pool_c], hits(pool_r, pool_c, t))
    if len(new_rows) < 20:
        return {"ran": False, "reason": f"not run: too few new buildings ({len(new_rows)})"}
    leads = pd.DataFrame(new_rows, columns=["t", "r", "c", "share"])
    leads["hit"] = False
    for t, g in leads.groupby("t"):
        leads.loc[g.index, "hit"] = hits(g.r.to_numpy(), g.c.to_numpy(), int(t))
    edges = np.percentile(leads.share, [20, 40, 60, 80])
    leads["q"] = np.digitize(leads.share, edges)
    null = np.zeros(draws)
    for (t, q), g in leads.groupby(["t", "q"]):
        pool_share, pool_hit = pools[t]
        cand = pool_hit[np.digitize(pool_share, edges) == q]
        if len(cand) == 0:
            return {"ran": False, "reason": f"not run: no built-matched null pixels for year {t}, quintile {q}"}
        null += rng.choice(cand, size=(draws, len(g)), replace=True).sum(1)
    null /= len(leads)
    share_hit = float(leads.hit.mean())
    p = float((np.sum(null >= share_hit) + 1) / (draws + 1))
    return {
        "ran": True,
        "radius_m": radius_m,
        "new_buildings": len(leads),
        "by_year": {int(t): int(n) for t, n in leads.t.value_counts().sort_index().items()},
        "hits": int(leads.hit.sum()),
        "share": round(share_hit, 4),
        "null_share": round(float(null.mean()), 4),
        "null_p95": round(float(np.percentile(null, 95)), 4),
        "ratio": round(share_hit / null.mean(), 2) if null.mean() > 0 else None,
        "p": round(p, 4),
        "wells": len(w),
        "passed": bool(null.mean() > 0 and share_hit >= 1.5 * null.mean() and p < 0.05),
    }


def main() -> None:
    import sys

    out_path = DATA / "check_results.json"
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), ["V4", "V5", "V7", "V8"])
    if "--v5-only" in sys.argv:
        only = ["V5"]
    if "V7" in only:
        results["V7"] = v7()
        print("V7", json.dumps(results["V7"], indent=1))
    if "V8" in only:
        results["V8"] = v8()
        print("V8", json.dumps(results["V8"], indent=1))
    if "V4" in only and (REAL / "arizona" / "v4" / "io_lulc.npz").exists():
        results["V4"] = v4()
        print("V4", json.dumps(results["V4"], indent=1))
    leads_file = DATA / "leads.json"
    if "V5" in only and leads_file.exists() and json.loads(leads_file.read_text())["status"] == "available":
        results["V5"] = v5()
        print("V5", json.dumps(results["V5"], indent=1))
    results["preregistration"] = PREREG
    results["run_date"] = RUN_DATE
    out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
    publish(results)


PREREG = "apps/backend/scripts/prereg_v5_v7_v8.md"
RUN_DATE = "2026-11-20"
OUTCOME_WORDING = {
    "placebo_effect": "A placebo shows an effect. The method is picking up noise. No claim is made.",
    "pipes_slowed_sinking": "Sinking slowed more where the pipes arrived. This is evidence for pipes as a local fix.",
    "no_extra_slowdown_control_passed": (
        "The method can see a known pumping cut and saw no extra slowdown here. Pipe "
        "priority should follow the volume replaced, not the location."
    ),
    "no_extra_slowdown_control_failed": "Inconclusive. The app shows the before/after maps without a claim either way.",
}


def outcome_code(v7r: dict, v8r: dict) -> tuple[str, str]:
    """The report's outcome table for module C (section C, 'Did the pipes slow the sinking?')."""
    if not (v7r["placebo_year_clean"] and v7r["placebo_area_clean"]):
        return "inconclusive", "placebo_effect"
    if v7r["main"]["delta_mm_yr"] < v7r["main"]["null_p05"]:
        return "pass", "pipes_slowed_sinking"
    if v8r.get("ran") and v8r["passed"]:
        return "fail", "no_extra_slowdown_control_passed"
    return "inconclusive", "no_extra_slowdown_control_failed"


def publish(results: dict) -> None:
    """Copy the results into the seed files the API serves (pipes.json, validation.json)."""
    v7r, v8r = results["V7"], results["V8"]
    pipes = json.loads((DATA / "pipes.json").read_text(encoding="utf-8"))
    status, code = outcome_code(v7r, v8r)
    spam = pipes["spam"]
    spam.update({
        "status": status,
        "outcome_code": code,
        "delta_mm_yr": v7r["main"]["delta_mm_yr"],
        "shift_null_p05": v7r["main"]["null_p05"],
        "shift_null_p95": v7r["main"]["null_p95"],
        "p_lower": v7r["main"]["p_lower"],
        "served_cells": v7r["main"]["served_cells"],
        "placebo_year_clean": v7r["placebo_year_clean"],
        "placebo_area_clean": v7r["placebo_area_clean"],
        "placebo_years_delta_mm_yr": v7r["placebo_years"]["delta_mm_yr"],
        "placebo_area_delta_mm_yr": v7r["placebo_area"]["delta_mm_yr"],
        "served_mean_mm_yr": v7r["served_mean_mm_yr"],
        "control_mean_mm_yr": v7r["control_mean_mm_yr"],
        "positive_control_passed": v8r["passed"] if v8r.get("ran") else None,
        "positive_control_delta_mm_yr": v8r["main"]["delta_mm_yr"] if v8r.get("ran") else None,
        "positive_control_null_p05": v8r["main"]["null_p05"] if v8r.get("ran") else None,
        "positive_control_note": (
            f"Arizona, OPERA F07091: {v8r['cut_blocks']} 4 km blocks where metered pumping fell from "
            f"{v8r['cut_acre_ft_yr'][0]:,} to {v8r['cut_acre_ft_yr'][1]:,} acre-ft/yr (2016-20 -> 2021-25)."
            if v8r.get("ran") else v8r.get("reason")
        ),
        "preregistration": PREREG,
        "run_date": RUN_DATE,
        "outcome_wording": OUTCOME_WORDING[code],  # the API recomputes it with interpret_spam_test
    })
    for key in ("ADWR", "EXP05", "GADM"):
        if key not in spam["source_ids"]:
            spam["source_ids"].append(key)
    (DATA / "pipes.json").write_text(json.dumps(pipes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checks = json.loads((DATA / "validation.json").read_text(encoding="utf-8"))
    by_code = {c["code"]: c for c in checks}
    m = v7r["main"]
    by_code["V7"].update({
        "status": "done",
        "result": "pass" if v7r["passed"] else "fail",
        "detail": (
            f"Delta {m['delta_mm_yr']:+.1f} mm/yr (shift null 5th-95th: {m['null_p05']:+.1f} to {m['null_p95']:+.1f}, "
            f"p = {m['p_lower']:.2f}); placebo years {v7r['placebo_years']['delta_mm_yr']:+.1f} "
            f"({'clean' if v7r['placebo_year_clean'] else 'not clean'}), placebo area "
            f"{v7r['placebo_area']['delta_mm_yr']:+.1f} ({'clean' if v7r['placebo_area_clean'] else 'not clean'}). "
            "Served kecamatan did not slow more than matched controls."
            if not v7r["passed"] else "Sinking slowed more where SPAM Semarang Barat arrived."
        ),
    })
    if v8r.get("ran"):
        n = v8r["main"]
        by_code["V8"].update({
            "status": "done",
            "result": "pass" if v8r["passed"] else "fail",
            "detail": (
                f"{v8r['cut_blocks']} Arizona blocks with a >= 50 % metered cut: Delta {n['delta_mm_yr']:+.2f} mm/yr "
                f"vs shift-null 5th percentile {n['null_p05']:+.2f} (p = {n['p_lower']:.2f}). "
                + ("The method sees the known cut." if v8r["passed"]
                   else "The method does not see a known, metered cut.")
            ),
        })
    if "V5" in results and results["V5"].get("ran"):
        r = results["V5"]
        by_code["V5"].update({
            "status": "done",
            "result": "pass" if r["passed"] else "fail",
            "detail": (
                f"{r['leads']} buildings passing filters 1-3: {r['lead_hits']} within {r['radius_m']} m of a "
                "permitted well "
                f"({r['lead_share']:.0%}) vs {r['null_share']:.0%} for size-matched new buildings, p = {r['p']:.3f}. "
                + ("Leads sit on permitted wells more often than chance." if r["passed"]
                   else f"Above the null, but not significant with {r['leads']} buildings."
                   if r["lead_share"] > r["null_share"] else "Not above the null.")
            ),
        })
    elif "V5" in results:
        by_code["V5"]["detail"] = results["V5"].get("reason")
    if "V4" in results and results["V4"].get("ran"):
        r = results["V4"]
        by_code["V4"].update({
            "status": "done",
            "result": "pass" if r["passed"] else "fail",
            "detail": (
                f"{r['new_buildings']} new built patches (1,000 m2 to 25 ha, IO land cover 2018-2021) outside "
                f"ADWR water-provider areas: {r['hits']} got a new registered well within {r['radius_m']:.0f} m in "
                f"t to t+2 ({r['share']:.1%}) vs {r['null_share']:.1%} for built-matched existing sites "
                f"(ratio {r['ratio']}, p = {r['p']:.4f}). "
                + ("New buildings do pull new wells, at the pass mark." if r["passed"] else
                   "New buildings pull new wells more than chance, but less than the 1.5x pass mark.")
            ),
        })
    elif "V4" in results:
        by_code["V4"]["detail"] = results["V4"].get("reason")
    extra_sources = {"V7": ["LICSAR", "EXP14", "GADM"], "V8": ["ADWR", "EXP05"], "V5": ["ZONE-2022", "LO-2022"],
                     "V4": ["ADWR", "IO-LULC"]}
    for key, src in extra_sources.items():
        for s in src:
            if s not in by_code[key]["source_ids"]:
                by_code[key]["source_ids"].append(s)
    (DATA / "validation.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
