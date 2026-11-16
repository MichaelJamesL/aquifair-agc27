import json, sys, time, warnings, numpy as np, synth as S
PART = sys.argv[1]
warnings.filterwarnings("ignore")
R = {}
t0 = time.time()
def dump():
    json.dump(R, open(f"results_{PART}.json", "w"), indent=1, default=float)
    print("saved", round(time.time() - t0), "s", flush=True)

def summarize(sc, fit, ci=None, stab=None):
    s = S.score(sc, fit["sources"])
    rec = dict(n_true=s["n_true"], n_est=s["n_est"], tp=s["tp"], tot_ratio=s["tot_ratio"],
               rel_err=s["rel_err"], loc_err=s["loc_err"], param=fit.get("param"))
    rec["matched"] = [dict(q_true=float(sc["q"][i]), q_est=float(fit["sources"][j, 2]),
                           lo=float(ci[j, 0]) if ci is not None else None,
                           hi=float(ci[j, 2]) if ci is not None else None,
                           stab=float(stab[j]) if stab is not None else None) for i, j in s["pairs"]]
    mt = {i for i, _ in s["pairs"]}; me = {j for _, j in s["pairs"]}
    rec["missed_q"] = [float(sc["q"][i]) for i in range(len(sc["q"])) if i not in mt]
    rec["fp"] = [dict(q_est=float(fit["sources"][j, 2]), stab=float(stab[j]) if stab is not None else None)
                 for j in range(len(fit["sources"])) if j not in me]
    return rec

# ---------- E1: main ensemble ----------
R["E1"] = []
for seed in (range(101, 111) if PART == "A" else range(111, 121) if PART == "B" else []):
    sc = S.make_scenario(seed)
    fcv = S.fit_sparse(sc, seed=seed)
    ci, st = S.bootstrap(sc, fcv, seed=seed)
    fcal = S.fit_sparse(sc, params=(1500.,), seed=seed)
    ci2, st2 = S.bootstrap(sc, fcal, seed=seed)
    fsm = S.fit_smooth(sc, seed=seed)
    fbo = S.fit_bowls(sc)
    R["E1"].append(dict(seed=seed, noise_sd=sc["noise_sd"], cv=summarize(sc, fcv, ci, st),
                        cal=summarize(sc, fcal, ci2, st2), smooth=summarize(sc, fsm), bowls=summarize(sc, fbo)))
    if seed == 103:
        np.savez("example.npz", d=sc["d"], mask=sc["mask"], v_src=sc["v_src"], bg=sc["bg"], pts=sc["pts"], q=sc["q"],
                 est=fcal["sources"], ci=ci2, stab=st2, qsmooth=fsm["qgrid"], smooth_src=fsm["sources"],
                 bowls=fbo["sources"], qgrid=fcal["qgrid"])
    dump()
    print("E1", seed, R["E1"][-1]["cv"]["param"], R["E1"][-1]["cal"]["tp"], R["E1"][-1]["cal"]["n_true"], R["E1"][-1]["cal"]["n_est"], flush=True)
dump()

# ---------- E2: noise sweep (kernel width calibrated) ----------
R["E2"] = []
for scale in ([0.5, 1.0, 2.0, 3.0, 4.0] if PART == "C" else []):
    for seed in range(201, 209):
        sc = S.make_scenario(seed, noise_scale=scale)
        f = S.fit_sparse(sc, params=(1500.,), seed=seed)
        r = summarize(sc, f); r.update(scale=scale, noise_sd=sc["noise_sd"]); R["E2"].append(r)
    print("E2", scale, flush=True)
dump()

# ---------- E3: resolution of two equal sources ----------
R["E3"] = []
for ratio in ([0.5, 0.75, 1.0, 1.5, 2.0, 3.0] if PART == "C" else []):
    sep = ratio * 1500.0
    for seed in range(301, 309):
        pts = np.array([[12000 - sep / 2 + 130, 10000 + 90], [12000 + sep / 2 + 130, 10000 + 90]])
        sc = S.make_scenario(seed, sources=(pts, np.array([200., 200.])))
        f = S.fit_sparse(sc, params=(1500.,), seed=seed)
        tol = min(1000.0, 0.5 * sep)
        s = S.score(sc, f["sources"], tol=tol)
        R["E3"].append(dict(ratio=ratio, resolved=bool(s["tp"] == 2), n_est=s["n_est"], tot_ratio=s["tot_ratio"]))
    print("E3", ratio, flush=True)
dump()

# ---------- E4: wrong kernel width / wrong kernel family ----------
R["E4"] = []
for seed in (range(101, 109) if PART == "D" else []):
    sc = S.make_scenario(seed)
    for fam, plist in [("k0", [750., 1000., 1250., 1500., 2000., 2500.]), ("gauss", [1000., 1500., 2000.])]:
        for p in plist:
            f = S.fit_sparse(sc, fam=fam, params=(p,), seed=seed)
            r = summarize(sc, f); r.update(fam=fam, assumed=p, seed=seed); R["E4"].append(r)
    print("E4", seed, flush=True)
dump()
print("DONE", flush=True)
