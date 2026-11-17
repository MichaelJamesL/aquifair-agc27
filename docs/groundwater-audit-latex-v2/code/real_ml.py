"""Ablation: learned interferogram-stack rate estimators vs stacking (Semarang, descending 076D).

Every learned model reads each interferogram (all pair lengths, 6-48 d) as one token: LOS
displacement, per-pair rate, coherence, validity + pair start/end/length. Models are trained on
REAL stable-ground noise (hills, H > 30 m, real motion patches excluded from the loss) with an
injected, spatially smooth deformation of known rate; held-out spatial blocks are used for
validation. The physics inversion downstream is unchanged.

Methods
  classical : stack_all, stack24 (pairs >= 24 d), median (median of per-pair rates)
  learned   : deepsets (no attention, learned weighted pooling)
              t0       (temporal transformer, own pixel)
              t0_24    (t0 fed only pairs >= 24 d: do short pairs carry information?)
              t1       (t0 + 3x3 neighbourhood in each token)
              stpix    (temporal then spatial attention over 15x15 pixel tokens)
              vit      (temporal then spatial attention over 5x5 patches of 3x3 px =
                        ViViT factorised encoder with ViT patch embedding)
Metrics
  M1 synthetic rate error on held-out blocks (all / low-coherence pixels)
  M2 real stable-ground noise on held-out blocks (robust sd, mm/yr)
  M3 agreement with the independent ascending track on the coastal plain (never trained on)
  M4 planted K0 cones (planted in the interferograms) -> unchanged sparse inversion:
     recall, new false sources, volume error

Usage: python real_ml.py OUT.json [--steps N] [--quick] [--only m1,m2]
"""
import sys, json, time, math, os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy import ndimage
import synth as S
import real_lib as R

ROOT = "C:/Kuliah/hackathon/agc-26/realdata/semarang"
OUTP = sys.argv[1]
ARG = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
STEPS = ARG("--steps", 2500)
QUICK = "--quick" in sys.argv
CLASSIC = ["stack_all", "stack24", "median"]
LEARNED = ["deepsets", "t0", "t0_24", "t1", "stpix", "vit"]
ONLY = ARG("--only", "")
METHODS = CLASSIC + ([m for m in LEARNED if m in ONLY.split(",")] if ONLY else LEARNED)
dev = torch.device("cuda")
torch.manual_seed(0)
T0 = time.time()
W, WP, PS = 15, 17, 3                     # window, window + 1 px halo, ViT patch size


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


grid = R.Grid(428000.0, 9220000.0, 32749)


def pair_times(pairs):
    d0 = np.datetime64("2018-01-01")
    ta = np.array([(np.datetime64(f"{p[:4]}-{p[4:6]}-{p[6:8]}") - d0).astype(int) for p in pairs]) / 365.25
    tb = np.array([(np.datetime64(f"{p[9:13]}-{p[13:15]}-{p[15:]}") - d0).astype(int) for p in pairs]) / 365.25
    return ta, tb


def referenced_los(stackdir):
    """LOS displacement per pair (mm, + towards satellite), referenced to the stable hills, as in
    real_lib.rate_map (no GACOS: it had no measurable effect). Pair-by-pair to save RAM."""
    z = np.load(f"{stackdir}/stack.npz")
    hgt, land = z["hgt"], z["landmask"]
    unw, cc = z["unw"], z["cc"]
    ref = (hgt > 60) & (land > 0)
    valid = np.isfinite(unw) & (unw != 0) & (cc >= 0.15 * 255)
    los = np.zeros(unw.shape, np.float16)
    for k in range(len(unw)):
        r = valid[k] & ref
        if r.sum() < 50:
            valid[k] = False
            continue
        los[k] = np.where(valid[k], (unw[k] - np.median(unw[k][r])) * (-R.LAM / (4 * np.pi) * 1000), 0.0)
    del unw
    return z, los, valid, cc


# ---- ascending reference (independent noise) for M3: stacking >= 24 d -----------------------------
ASC = f"{ROOT}/exp/ml_asc24_grid.npz"
if not os.path.exists(ASC):
    za, la, va, _ = referenced_los(f"{ROOT}/t127")
    ta_, tb_ = pair_times(za["pairs"])
    sel = (tb_ - ta_) * 365.25 >= 23.5
    used = va.any((1, 2))
    num = np.zeros(la.shape[1:]); den = np.zeros(la.shape[1:])
    for k in np.flatnonzero(sel & used):
        num += np.where(va[k], la[k].astype(float), 0); den += va[k] * (tb_[k] - ta_[k])
    ok = (va[sel & used].mean(0) >= 0.5) & (za["landmask"] > 0)
    sub = np.where(ok, -(num / np.maximum(den, 1e-9)) / za["U"], np.nan)
    A, c = grid.block_mean(sub, za["transform"])
    np.savez(ASC, A=np.where(c >= 1, A, np.nan))
    del za, la, va
ASC_D = np.load(ASC)["A"]
log("ascending reference ready")

# ---- descending data -----------------------------------------------------------------------------
z, los, valid, cc = referenced_los(f"{ROOT}/t076")
pairs, hgt, U, land, TR = z["pairs"], z["hgt"], z["U"], z["landmask"], z["transform"]
ta, tb = pair_times(pairs)
dt = tb - ta
NP, NYn, NXn = los.shape
LONG = dt * 365.25 >= 23.5
used = valid.any((1, 2))
OK = (valid[used].mean(0) >= 0.5) & (valid[used & LONG].mean(0) >= 0.5) & (land > 0)
H = R.grid_hgt(dict(hgt=hgt, transform=TR, sub=np.where(OK, 0.0, np.nan)), grid)

GL = torch.tensor(los, device=dev)                       # fp16 (P, ny, nx)
GV = torch.tensor(valid, device=dev)
GC = torch.tensor(cc, device=dev)                        # uint8
del los, cc
GU = torch.tensor(U, device=dev, dtype=torch.float32)
GDT = torch.tensor(dt, device=dev, dtype=torch.float32)
GTA = torch.tensor(ta, device=dev, dtype=torch.float32)
GTB = torch.tensor(tb, device=dev, dtype=torch.float32)
GLONG = torch.tensor(LONG, device=dev)
TF = torch.stack([GTA / 4.5 - .5, GTB / 4.5 - .5, GDT * 4, torch.log(GDT * 365.25) / 4,
                  torch.sin(2 * math.pi * GTA), torch.cos(2 * math.pi * GTA),
                  torch.sin(2 * math.pi * GTB), torch.cos(2 * math.pi * GTB)], 1)   # (P, 8)
log(f"desc stack {NP} pairs {NYn}x{NXn}, OK px {OK.sum()}")

# ---- classical estimators (dim 1 = pairs, inputs (B, P, h, w)) ------------------------------------
DT4 = GDT.view(1, -1, 1, 1)


def stack_rate(L, V, sel=None):
    v = V if sel is None else V & sel.view(1, -1, 1, 1)
    return (L.float() * v).sum(1) / (v * DT4).sum(1).clamp_min(1e-9)


def median_rate(L, V):
    return torch.nanmedian(torch.where(V, L.float() / DT4, torch.nan), 1).values


# ---- training region: stable hills, spatial block split -------------------------------------------
v24 = stack_rate(GL[None], GV[None], GLONG)[0].cpu().numpy()
st = OK & (hgt > 30)
med = np.median(v24[st]); mad = 1.4826 * np.median(np.abs(v24[st] - med))
CLEAN = st & (np.abs(v24 - med) < 3 * mad)              # exclude real moving patches from the loss
rng = np.random.default_rng(0)
BLK = 24
bid = (np.arange(NYn)[:, None] // BLK) * 100 + np.arange(NXn)[None] // BLK
blocks = np.unique(bid[st])
VALB = np.isin(bid, rng.choice(blocks, max(2, len(blocks) // 4), replace=False))
near_val = ndimage.binary_dilation(VALB, iterations=WP)


def centers(region, need):
    out = []
    for r in range(0, NYn - WP + 1):
        for c in range(0, NXn - WP + 1):
            if region[r + WP // 2, c + WP // 2] and CLEAN[r + 1:r + WP - 1, c + 1:c + WP - 1].mean() >= need:
                out.append((r, c))
    return out


TRC = [rc for rc in centers(st & ~near_val, 0.4) if not VALB[rc[0]:rc[0] + WP, rc[1]:rc[1] + WP].any()]
VAC = centers(VALB & st, 0.4)
VAC = [rc for rc in VAC if VALB[rc[0]:rc[0] + WP, rc[1]:rc[1] + WP].all()] or VAC
log(f"clean px {CLEAN.sum()} (thr {3 * mad:.1f} mm/yr LOS), train windows {len(TRC)}, val windows {len(VAC)}")

GUc = GU


def cut(rc, A):
    return torch.stack([A[..., r:r + WP, c:c + WP] for r, c in rc])


def field(rng):
    """Random smooth vertical subsidence-rate field (mm/yr) on the window + seasonal amplitude."""
    y, x = np.mgrid[0:WP, 0:WP] - WP / 2
    if rng.random() < 0.25:
        s = np.full((WP, WP), rng.uniform(-5, 5))
    else:
        s = np.full((WP, WP), rng.uniform(-10, 140))
        if rng.random() < 0.5:
            th, w, o = rng.uniform(0, 2 * np.pi), rng.uniform(1, 8), rng.uniform(-WP / 2, WP / 2)
            s += rng.uniform(-100, 100) / (1 + np.exp(-(x * np.cos(th) + y * np.sin(th) - o) / w))
    for _ in range(rng.poisson(1.5)):
        cx, cy = rng.uniform(-WP, WP, 2)
        sg = rng.uniform(1.5, 12)
        s += rng.uniform(-30, 80) * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * sg ** 2))
    return s, rng.uniform(0, 8), rng.uniform(0, 2 * np.pi)


def batch(rc, rng):
    """Window tensors with injected deformation; returns L, V, C, target v_los (B, W, W), label mask."""
    L, V, C = cut(rc, GL), cut(rc, GV), cut(rc, GC)
    Uw = cut(rc, GU)
    fs = [field(rng) for _ in rc]
    s = torch.tensor(np.stack([f[0] for f in fs]), device=dev, dtype=torch.float32)
    a = torch.tensor([f[1] for f in fs], device=dev, dtype=torch.float32).view(-1, 1, 1, 1)
    ph = torch.tensor([f[2] for f in fs], device=dev, dtype=torch.float32).view(-1, 1, 1, 1)
    TA, TB = GTA.view(1, -1, 1, 1), GTB.view(1, -1, 1, 1)
    dd = s[:, None] * DT4 + a * (torch.sin(2 * math.pi * TB + ph) - torch.sin(2 * math.pi * TA + ph))
    L = (L.float() + torch.where(V, -Uw[:, None] * dd, 0.0)).half()
    tgt = (-Uw * s)[:, 1:-1, 1:-1]
    lab = torch.stack([torch.tensor(CLEAN[r + 1:r + WP - 1, c + 1:c + WP - 1]) for r, c in rc]).to(dev)
    return L, V, C, tgt, lab


# ---- models -------------------------------------------------------------------------------------------
D_ = 64


class TEnc(nn.Module):
    """Interferogram tokens -> pixel/patch embedding. attn=False: DeepSets (learned weighted pooling)."""

    def __init__(s, fin, attn=True, L=3):
        super().__init__()
        s.attn = attn
        s.inp = nn.Sequential(nn.Linear(fin + 8, D_), nn.GELU(), nn.Linear(D_, D_))
        if attn:
            s.cls = nn.Parameter(torch.zeros(1, 1, D_))
            s.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(D_, 4, 2 * D_, 0.0, batch_first=True,
                                                                     norm_first=True), L, enable_nested_tensor=False)
        else:
            s.phi = nn.Sequential(nn.Linear(D_, 2 * D_), nn.GELU(), nn.Linear(2 * D_, D_))
            s.score = nn.Linear(D_, 1)
        s.norm = nn.LayerNorm(D_)

    def forward(s, x, m):                                  # x (N, P, fin), m (N, P)
        e = s.inp(torch.cat([x, TF.expand(len(x), -1, -1)], -1))
        if s.attn:
            e = torch.cat([s.cls.expand(len(e), -1, -1), e], 1)
            pad = torch.cat([torch.zeros(len(m), 1, dtype=torch.bool, device=m.device), ~m], 1)
            return s.norm(s.enc(e, src_key_padding_mask=pad)[:, 0])
        h = s.phi(e)
        w = s.score(h).squeeze(-1).float().masked_fill(~m, -1e4).softmax(1)
        return s.norm((w.unsqueeze(-1) * h.float()).sum(1))


class Pix(nn.Module):
    def __init__(s, fin, attn=True):
        super().__init__()
        s.t, s.head = TEnc(fin, attn), nn.Linear(D_, 1)

    def forward(s, x, m):
        return s.head(s.t(x, m)).squeeze(-1)


class Spat(nn.Module):
    """Factorised space-time encoder: temporal attention per token, then spatial attention."""

    def __init__(s, fin, n, p):
        super().__init__()
        s.t = TEnc(fin)
        s.pos = nn.Parameter(torch.randn(1, n, D_) * 0.02)
        s.sp = nn.TransformerEncoder(nn.TransformerEncoderLayer(D_, 4, 2 * D_, 0.0, batch_first=True,
                                                                norm_first=True), 2, enable_nested_tensor=False)
        s.head = nn.Linear(D_, p * p)

    def forward(s, x, m):                                  # x (B, n, P, f)
        B, n = x.shape[:2]
        e = s.t(x.flatten(0, 1), m.flatten(0, 1)).view(B, n, -1) + s.pos
        return s.head(s.sp(e))                             # (B, n, p*p)


def feats(L, V, C):
    """(B, P, h, w) -> (B, P, h, w, 4): displacement, per-pair rate, coherence, validity."""
    Vf = V.float()
    Lf = L.float() * Vf
    return torch.stack([Lf / 50, (Lf / DT4 / 200).clamp(-5, 5), C.float() / 255 * Vf, Vf], -1)


def build(name):
    return {"deepsets": lambda: Pix(4, attn=False), "t0": lambda: Pix(4), "t0_24": lambda: Pix(4),
            "t1": lambda: Pix(36), "stpix": lambda: Spat(4, W * W, 1),
            "vit": lambda: Spat(4 * PS * PS, (W // PS) ** 2, PS)}[name]().to(dev)


def run(name, model, L, V, C, chunk=None):
    """Rate prediction (v_los, mm/yr) for window tensors (B, P, WP, WP) -> (B, W, W)."""
    B, P = L.shape[:2]
    if name == "stack_all":
        return stack_rate(L, V)[:, 1:-1, 1:-1]
    if name == "stack24":
        return stack_rate(L, V, GLONG)[:, 1:-1, 1:-1]
    if name == "median":
        return median_rate(L, V)[:, 1:-1, 1:-1]
    if name == "t0_24":
        V = V & GLONG.view(1, -1, 1, 1)
    f = feats(L, V, C)                                     # (B, P, WP, WP, 4)
    Vc = V[:, :, 1:-1, 1:-1]
    with torch.autocast("cuda", dtype=torch.bfloat16):
        if name in ("deepsets", "t0", "t0_24", "t1"):
            if name == "t1":
                x = torch.cat([f[:, :, 1 + dy:WP - 1 + dy, 1 + dx:WP - 1 + dx]
                               for dy in (-1, 0, 1) for dx in (-1, 0, 1)], -1)
            else:
                x = f[:, :, 1:-1, 1:-1]
            x = x.permute(0, 2, 3, 1, 4).reshape(B * W * W, P, -1)
            m = Vc.permute(0, 2, 3, 1).reshape(B * W * W, P)
            ch = chunk or len(x)
            out = torch.cat([model(x[i:i + ch], m[i:i + ch]) for i in range(0, len(x), ch)])
            return out.float().view(B, W, W) * 50
        if name == "stpix":
            x = f[:, :, 1:-1, 1:-1].permute(0, 2, 3, 1, 4).reshape(B, W * W, P, 4)
            m = Vc.permute(0, 2, 3, 1).reshape(B, W * W, P)
        else:                                              # vit: 3x3 patches
            n = W // PS
            x = f[:, :, 1:-1, 1:-1].reshape(B, P, n, PS, n, PS, 4).permute(0, 2, 4, 1, 3, 5, 6)
            x = x.reshape(B, n * n, P, PS * PS * 4)
            m = Vc.reshape(B, P, n, PS, n, PS).permute(0, 2, 4, 1, 3, 5).reshape(B, n * n, P, -1).any(-1)
        ch = chunk or B
        out = torch.cat([model(x[i:i + ch], m[i:i + ch]) for i in range(0, B, ch)]).float()
        if name == "stpix":
            return out.view(B, W, W) * 50
        n = W // PS
        return out.view(B, n, n, PS, PS).permute(0, 1, 3, 2, 4).reshape(B, W, W) * 50


def train(name):
    model = build(name)
    nb = {"stpix": 1, "vit": 8}.get(name, 2)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    sch = torch.optim.lr_scheduler.LambdaLR(opt, lambda k: min(1, (k + 1) / 100) * 0.5 * (1 + math.cos(math.pi * k / STEPS)))
    r = np.random.default_rng(1)
    tl = []
    for k in range(STEPS):
        rc = [TRC[i] for i in r.integers(len(TRC), size=nb)]
        L, V, C, tgt, lab = batch(rc, r)
        pred = run(name, model, L, V, C)
        loss = F.smooth_l1_loss(pred[lab] / 50, tgt[lab] / 50, beta=0.04)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()
        tl.append(loss.item())
        if (k + 1) % 500 == 0 or k == STEPS - 1:
            log(f"  {name} step {k + 1} loss {np.mean(tl[-200:]):.4f}")
    model.eval()
    return model


# ---- full-scene prediction ---------------------------------------------------------------------------
PAD = 8


def scene(name, model, L, V, C):
    """v_los (mm/yr) map for full-scene tensors (P, ny, nx); NaN outside OK."""
    with torch.no_grad():
        if name in CLASSIC:
            v = run(name, None, F.pad(L, (1, 1, 1, 1))[None], F.pad(V, (1, 1, 1, 1))[None],
                    F.pad(C, (1, 1, 1, 1))[None])[0]
            return np.where(OK, v.cpu().numpy(), np.nan)
        Lp, Vp, Cp = F.pad(L, (PAD,) * 4), F.pad(V, (PAD,) * 4), F.pad(C, (PAD,) * 4)
        okp = np.pad(OK, PAD)
        hh, ww = okp.shape
        spatial = name in ("stpix", "vit")
        stride = 9 if spatial else W
        wt1 = np.sin(np.pi * (np.arange(W) + .5) / W) + 1e-3 if spatial else np.ones(W)
        wt = torch.tensor(np.outer(wt1, wt1), device=dev, dtype=torch.float32)
        rows = sorted(set(list(range(0, hh - WP + 1, stride)) + [hh - WP]))
        cols = sorted(set(list(range(0, ww - WP + 1, stride)) + [ww - WP]))
        rc = [(r, c) for r in rows for c in cols if okp[r + 1:r + WP - 1, c + 1:c + WP - 1].any()]
        acc = torch.zeros(hh, ww, device=dev); ws = torch.zeros(hh, ww, device=dev)
        nb = 8 if spatial else 4
        for i in range(0, len(rc), nb):
            b = rc[i:i + nb]
            out = run(name, model, cut(b, Lp), cut(b, Vp), cut(b, Cp), chunk=1024 if not spatial else 4)
            for (r, c), o in zip(b, out):
                acc[r + 1:r + WP - 1, c + 1:c + WP - 1] += o * wt
                ws[r + 1:r + WP - 1, c + 1:c + WP - 1] += wt
        v = (acc / ws.clamp_min(1e-9))[PAD:-PAD, PAD:-PAD].cpu().numpy()
        return np.where(OK, v, np.nan)


def to_grid(v):
    D, c = grid.block_mean(-v / U, TR)
    return np.where(c >= 1, D, np.nan), c >= 1


# ---- train ---------------------------------------------------------------------------------------------
models, res = {}, dict(steps=STEPS, methods=METHODS, n_clean=int(CLEAN.sum()), n_train_win=len(TRC),
                       n_val_win=len(VAC), m1={}, m2={}, m3={}, m4={}, params={}, train_s={})
for name in METHODS:
    if name in LEARNED:
        t = time.time()
        ck = f"{ROOT}/exp/ml_ckpt/{name}_{STEPS}.pt"     # resume: a killed run keeps finished models
        if os.path.exists(ck):
            models[name] = build(name)
            models[name].load_state_dict(torch.load(ck))
            models[name].eval()
        else:
            models[name] = train(name)
            os.makedirs(os.path.dirname(ck), exist_ok=True)
            torch.save(models[name].state_dict(), ck)
        res["train_s"][name] = round(time.time() - t)
        res["params"][name] = sum(p.numel() for p in models[name].parameters())
        log(f"trained {name}: {res['params'][name]} params, {res['train_s'][name]} s")
    else:
        models[name] = None

# ---- M1 synthetic, held-out blocks --------------------------------------------------------------------
r = np.random.default_rng(123)
vwin = [VAC[i] for i in r.integers(len(VAC), size=20 if QUICK else 160)]
vb = [batch(vwin[i:i + 8], r) for i in range(0, len(vwin), 8)]
for name in METHODS:
    err, lowc = [], []
    with torch.no_grad():
        for L, V, C, tgt, lab in vb:
            p = run(name, models[name], L, V, C, chunk=1024 if name not in ("stpix", "vit") else 4)
            coh = (C[:, :, 1:-1, 1:-1].float().mean(1) / 255)
            e = (p - tgt)[lab] / GU.mean()                       # vertical-equivalent error
            err.append(e.cpu().numpy()); lowc.append((coh[lab] < 0.35).cpu().numpy())
    e, lc = np.concatenate(err), np.concatenate(lowc)
    res["m1"][name] = dict(mae=float(np.mean(np.abs(e))), rmse=float(np.sqrt(np.mean(e ** 2))), bias=float(np.mean(e)),
                           mae_lowcoh=float(np.mean(np.abs(e[lc]))) if lc.any() else None,
                           mae_highcoh=float(np.mean(np.abs(e[~lc]))), n=int(len(e)), frac_lowcoh=float(lc.mean()))
    log("M1", name, {k: round(v, 2) if isinstance(v, float) else v for k, v in res["m1"][name].items()})

# ---- M2 / M3 real, clean scene ------------------------------------------------------------------------
valcell = grid.block_mean(VALB.astype(float), TR)[0] > 0.5
clean_maps = {}
for name in METHODS:
    v = scene(name, models[name], GL, GV, GC)
    clean_maps[name] = v
    D, mask = to_grid(v)
    sd_v, rsd_v = R.stable_noise(D, H, mask & valcell)
    sd_a, rsd_a = R.stable_noise(D, H, mask)
    res["m2"][name] = dict(val_sd=sd_v, val_robust_sd=rsd_v, all_sd=sd_a, all_robust_sd=rsd_a)
    plain = mask & np.isfinite(ASC_D) & (H < 30)
    d = D[plain] - ASC_D[plain]
    res["m3"][name] = dict(n=int(plain.sum()), median_diff=float(np.median(d)),
                           robust_sd_diff=float(1.4826 * np.median(np.abs(d - np.median(d)))),
                           sd_diff=float(np.std(d)), pearson=float(np.corrcoef(D[plain], ASC_D[plain])[0, 1]),
                           p99=float(np.nanpercentile(D, 99)))
    log("M2", name, {k: round(v, 2) for k, v in res["m2"][name].items()})
    log("M3", name, {k: round(v, 3) if isinstance(v, float) else v for k, v in res["m3"][name].items()})
json.dump(res, open(OUTP, "w"), indent=1)
np.savez_compressed(OUTP.replace(".json", "_maps.npz"), **{k: v.astype(np.float32) for k, v in clean_maps.items()})

# ---- M4 planted cones in the interferograms -> unchanged physics inversion ------------------------------
LON, LAT = np.meshgrid(TR[2] + TR[0] * (np.arange(NXn) + .5), TR[5] + TR[4] * (np.arange(NYn) + .5))
E_, N_ = grid.fw.transform(LON, LAT)
PX, PY = E_ - grid.E0, N_ - grid.N0
_, mask0 = to_grid(clean_maps["stack_all"])
mp = np.flatnonzero(ndimage.binary_erosion(mask0, iterations=5).ravel())
QS = (200.0,) if QUICK else (100.0, 200.0, 400.0)
NT = 1 if QUICK else 3
trials = []
r = np.random.default_rng(7)
for q in QS:
    for t in range(NT):
        pts = []
        while len(pts) < 5:
            j = r.choice(mp)
            p = np.array([S.XX.ravel()[j], S.YY.ravel()[j]])
            if all(np.hypot(*(p - o)) > 2500 for o in pts):
                pts.append(p)
        trials.append((q, t, np.array(pts)))
planted = {n: [] for n in METHODS}
for q, t, pts in trials:
    s = sum(q * S.kern(np.hypot(PX - x, PY - y), "k0", 1500.0) for x, y in pts)    # mm/yr subsidence
    dl = torch.tensor(-U * s, device=dev, dtype=torch.float32)
    Lp = (GL.float() + torch.where(GV, dl[None] * GDT.view(-1, 1, 1), 0.0)).half()
    for name in METHODS:
        planted[name].append(scene(name, models[name], Lp, GV, GC))
    del Lp
    log(f"planted maps q={q} trial {t}")
del models
torch.cuda.empty_cache()

R.use_robust_floor()
for name in METHODS:
    D, mask = to_grid(clean_maps[name])
    clay = R.background("edge", H, np.nan_to_num(D), mask, grid)
    sc = R.model_input_grid(np.nan_to_num(D), mask, clay)
    base = S.fit_sparse(sc, params=(1500.,), seed=0)["sources"]
    out = {}
    for (q, t, pts), v in zip(trials, planted[name]):
        Dp, _ = to_grid(v)
        est = S.fit_sparse(dict(sc, d=np.where(mask, np.nan_to_num(Dp), 0.0)), params=(1500.,), seed=t)["sources"]
        pr = S.match(pts, est)
        got = {jj for _, jj in pr}
        o = out.setdefault(q, dict(rec=[], fal=[], vol=[]))
        o["rec"].append(len(pr) / 5)
        o["vol"].extend(float((est[j, 2] - q) / q) for _, j in pr)
        o["fal"].append(sum(1 for j in range(len(est)) if j not in got and
                            (len(base) == 0 or np.hypot(base[:, 0] - est[j, 0], base[:, 1] - est[j, 1]).min() > 1000)))
    res["m4"][name] = {str(q): dict(recall=float(np.mean(o["rec"])), new_false=float(np.mean(o["fal"])),
                                    median_vol_err=float(np.median(o["vol"])) if o["vol"] else None,
                                    median_abs_vol_err=float(np.median(np.abs(o["vol"]))) if o["vol"] else None)
                       for q, o in out.items()}
    res["m4"][name]["n_base_sources"] = int(len(base))
    log("M4", name, json.dumps(res["m4"][name]))
    json.dump(res, open(OUTP, "w"), indent=1)
log("done")
