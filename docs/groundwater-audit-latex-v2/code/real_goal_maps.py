"""Cached rate maps on the model grid: stacking of pairs >= 24 d, one or two tracks, any span."""
import os
import numpy as np
import real_lib as R

ROOT = "C:/Kuliah/hackathon/agc-26/realdata/semarang"
grid = R.Grid(428000.0, 9220000.0, 32749)
SPANS = {"1822": ["t076"], "1422": ["t076", "t076_1517"], "1426": ["t076", "t076_1517", "t076_2326"],
         "1826": ["t076", "t076_2326"], "2326": ["t076_2326"]}


def cached_sums(stack):
    """Pair-by-pair stacking sums (pairs >= 24 d) on the native grid; low memory."""
    fn = f"{ROOT}/exp/goal_{stack}.npz"
    if os.path.exists(fn):
        return dict(np.load(fn))
    z = np.load(f"{ROOT}/{stack}/stack.npz")
    pairs, hgt, land = z["pairs"], z["hgt"], z["landmask"]
    unw, cc = z["unw"], z["cc"]
    ta = np.array([np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}") for p in pairs])
    tb = np.array([np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") for p in pairs])
    dt = (tb - ta).astype(int) / 365.25
    ref = (hgt > 60) & (land > 0)
    num = np.zeros(hgt.shape); den = np.zeros(hgt.shape); cnt = np.zeros(hgt.shape); n = 0
    for k in np.flatnonzero(dt * 365.25 >= 23.5):
        v = np.isfinite(unw[k]) & (unw[k] != 0) & (cc[k] >= 0.15 * 255)
        r = v & ref
        if r.sum() < 50:
            continue
        los = (unw[k] - np.median(unw[k][r])) * (-R.LAM / (4 * np.pi) * 1000)
        num += np.where(v, los, 0); den += v * dt[k]; cnt += v; n += 1
    out = dict(num=num, den=den, cnt=cnt, n=n, U=z["U"], hgt=hgt, land=land, transform=z["transform"])
    np.savez(fn, **out)
    return out


def track_map(stacks):
    ss = [cached_sums(s) for s in stacks]
    num, den = sum(s["num"] for s in ss), sum(s["den"] for s in ss)
    cnt, n = sum(s["cnt"] for s in ss), sum(int(s["n"]) for s in ss)
    s0 = ss[0]
    ok = (cnt / n >= 0.5) & (s0["land"] > 0)
    sub = np.where(ok, -(num / np.maximum(den, 1e-9)) / s0["U"], np.nan)
    return dict(sub=sub, hgt=s0["hgt"], transform=s0["transform"])


def load(tracks="da", span="1822"):
    """-> D (mm/yr, + sinking, NaN off-mask), mask, H, info."""
    rms = [track_map(SPANS[span])] + ([track_map(["t127"])] if tracks == "da" else [])
    H = R.grid_hgt(rms[0], grid)
    if len(rms) == 2:
        D, mask, qc = R.combine_tracks(rms, grid, H)
    else:
        D, c = grid.block_mean(rms[0]["sub"], rms[0]["transform"])
        mask, qc = c >= 1, {}
    return np.where(mask, D, np.nan), mask, H, dict(tracks=tracks, span=span, qc=qc,
                                                     stable=R.stable_noise(np.where(mask, D, np.nan), H, mask))
