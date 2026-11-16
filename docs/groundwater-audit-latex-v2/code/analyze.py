import json, numpy as np
R = {}
for p in "ABCD":
    r = json.load(open(f"results_{p}.json"))
    for k, v in r.items():
        R.setdefault(k, []).extend(v)
json.dump(R, open("results.json", "w"), indent=1)
E1, E2, E3, E4 = R["E1"], R["E2"], R["E3"], R["E4"]
M = {}   # macros
def pct(x): return f"{100*x:.0f}"

def pool(recs):
    nt = sum(r["n_true"] for r in recs); ne = sum(r["n_est"] for r in recs); tp = sum(r["tp"] for r in recs)
    rel = np.concatenate([r["rel_err"] for r in recs]) if tp else np.array([np.nan])
    loc = np.concatenate([r["loc_err"] for r in recs]) if tp else np.array([np.nan])
    tot = np.array([r["tot_ratio"] for r in recs])
    return dict(nt=nt, ne=ne, tp=tp, recall=tp/nt, precision=tp/ne if ne else float("nan"), rel=float(np.median(rel)),
                loc=float(np.median(loc)), tot_med=float(np.median(tot)), tot_min=float(tot.min()), tot_max=float(tot.max()),
                rel_p90=float(np.percentile(rel, 90)))

P = {m: pool([e[m] for e in E1]) for m in ["cal", "cv", "smooth", "bowls"]}
for m, tag in [("cal", "cal"), ("cv", "cv"), ("smooth", "sm"), ("bowls", "bo")]:
    p = P[m]
    M[tag+"Recall"] = pct(p["recall"]); M[tag+"Precision"] = pct(p["precision"]); M[tag+"MedErr"] = pct(p["rel"])
    M[tag+"Loc"] = f"{p['loc']:.0f}"; M[tag+"Tot"] = f"{p['tot_med']:.2f}"; M[tag+"TotMin"] = f"{p['tot_min']:.2f}"; M[tag+"TotMax"] = f"{p['tot_max']:.2f}"
    M[tag+"Nest"] = str(p["ne"]); M[tag+"Tp"] = str(p["tp"]); M[tag+"ErrNinety"] = pct(p["rel_p90"])
M["nScen"] = str(len(E1)); M["nTrue"] = str(P["cal"]["nt"])
M["noiseSd"] = f"{np.mean([e['noise_sd'] for e in E1]):.1f}"

def coverage(m):
    mm = [x for e in E1 for x in e[m]["matched"]]
    return np.mean([x["lo"] <= x["q_true"] <= x["hi"] for x in mm]), mm
c, mm_cal = coverage("cal"); M["calCover"] = pct(c)
c, mm_cv = coverage("cv"); M["cvCover"] = pct(c)

def stabfilter(m, thr=0.8):
    tp = sum(x["stab"] >= thr for e in E1 for x in e[m]["matched"])
    fp = sum(x["stab"] >= thr for e in E1 for x in e[m]["fp"])
    nt = sum(e[m]["n_true"] for e in E1)
    return tp/nt, tp/(tp+fp), fp
r_, p_, fp_ = stabfilter("cal"); M["calRecallStab"] = pct(r_); M["calPrecisionStab"] = pct(p_)
M["calFp"] = str(P["cal"]["ne"] - P["cal"]["tp"]); M["calFpStab"] = str(fp_)
fpst = [x["stab"] for e in E1 for x in e["cal"]["fp"]]; tpst = [x["stab"] for e in E1 for x in e["cal"]["matched"]]
M["calStabTp"] = f"{np.median(tpst):.2f}"; M["calStabFp"] = f"{np.median(fpst):.2f}" if fpst else "n/a"

Bs = np.array([e["cv"]["param"] for e in E1])
M["cvBexact"] = str(int((Bs == 1500).sum())); M["cvBnear"] = str(int((np.abs(Bs-1500) <= 250).sum()))
M["cvBmin"] = f"{Bs.min()/1000:.2f}"; M["cvBmax"] = f"{Bs.max()/1000:.2f}"
# CV runs split by whether B was right
good = [e["cv"] for e in E1 if e["cv"]["param"] == 1500]; bad = [e["cv"] for e in E1 if e["cv"]["param"] != 1500]
if good: M["cvGoodErr"] = pct(pool(good)["rel"])
if bad: M["cvBadErr"] = pct(pool(bad)["rel"])

# recall by volume bin (calibrated)
bins = [(40, 80), (80, 160), (160, 401)]
for (lo, hi), tag in zip(bins, ["Small", "Mid", "Large"]):
    hit = sum(lo <= x["q_true"] < hi for x in mm_cal); miss = sum(lo <= q < hi for e in E1 for q in e["cal"]["missed_q"])
    M["recall"+tag] = pct(hit/(hit+miss)); M["n"+tag] = str(hit+miss)

# E2 table
rows = []; e2 = {}
for sc in sorted({r["scale"] for r in E2}):
    rr = [r for r in E2 if r["scale"] == sc]; p = pool(rr); sd = np.mean([r["noise_sd"] for r in rr])
    e2[sc] = dict(sd=sd, **p)
    rows.append(f"{sd:.1f} & {pct(p['recall'])} & {pct(p['precision'])} & {pct(p['rel'])} & {p['tot_med']:.2f}\\\\")
open("../tex/tab_e2.tex", "w").write("\n".join(rows))
# E3 table
rows = []; e3 = {}
for ra in sorted({r["ratio"] for r in E3}):
    rr = [r for r in E3 if r["ratio"] == ra]
    e3[ra] = dict(res=np.mean([r["resolved"] for r in rr]), tot=np.median([r["tot_ratio"] for r in rr]), n=len(rr))
    rows.append(f"{ra:g} & {ra*1.5:.2f} & {sum(r['resolved'] for r in rr)} of {len(rr)} & {e3[ra]['tot']:.2f}\\\\")
open("../tex/tab_e3.tex", "w").write("\n".join(rows))
# E4 table
rows = []; e4 = {}
for fam in ["k0", "gauss"]:
    for a in sorted({r["assumed"] for r in E4 if r["fam"] == fam}):
        rr = [r for r in E4 if r["fam"] == fam and r["assumed"] == a]; p = pool(rr)
        e4[(fam, a)] = p
        name = "Bessel (true family)" if fam == "k0" else "Gaussian (wrong family)"
        mark = " (true)" if fam == "k0" and a == 1500 else ""
        rows.append(f"{name} & {a/1000:.2f}{mark} & {pct(p['recall'])} & {pct(p['precision'])} & {pct(p['rel'])} & {p['tot_med']:.2f}\\\\")
    rows.append("\\midrule")
open("../tex/tab_e4.tex", "w").write("\n".join(rows[:-1]))
for a, tag in [(750., "Narrow"), (1000., "OneK"), (2000., "TwoK"), (2500., "Wide")]:
    M["tot"+tag] = f"{e4[('k0', a)]['tot_med']:.2f}"; M["rec"+tag] = pct(e4[('k0', a)]['recall']); M["prec"+tag] = pct(e4[('k0', a)]['precision'])
for a, tag in [(1000., "GaussOne"), (1500., "GaussMid"), (2000., "GaussTwo")]:
    M["tot"+tag] = f"{e4[('gauss', a)]['tot_med']:.2f}"; M["rec"+tag] = pct(e4[('gauss', a)]['recall']); M["prec"+tag] = pct(e4[('gauss', a)]['precision'])
for sc, tag in [(0.5, "Half"), (1.0, "Base"), (2.0, "Two"), (3.0, "Three"), (4.0, "Four")]:
    M["noise"+tag] = f"{e2[sc]['sd']:.1f}"; M["recN"+tag] = pct(e2[sc]["recall"]); M["precN"+tag] = pct(e2[sc]["precision"]); M["errN"+tag] = pct(e2[sc]["rel"])
for ra, tag in [(0.5, "Half"), (0.75, "ThreeQ"), (1.0, "One"), (1.5, "OneHalf"), (2.0, "Two"), (3.0, "Three")]:
    M["res"+tag] = pct(e3[ra]["res"])
open("../tex/results.tex", "w").write("% generated by code/analyze.py -- do not edit\n" + "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()) + "\n")
for k, v in M.items(): print(k, v)
json.dump(dict(P=P, e2={str(k): v for k, v in e2.items()}, e3={str(k): v for k, v in e3.items()},
               e4={f"{k[0]}_{k[1]}": v for k, v in e4.items()}), open("summary.json", "w"), indent=1, default=float)

# ---- ranking robustness (Spearman rank correlation of true vs estimated volume) ----
from scipy.stats import spearmanr
def rank(recs):
    return float(np.median([spearmanr([m["q_true"] for m in r["matched"]], [m["q_est"] for m in r["matched"]])[0]
                            for r in recs if len(r["matched"]) >= 4]))
RK = {"rankCal": rank([e["cal"] for e in E1]), "rankCv": rank([e["cv"] for e in E1])}
for a, tag in [(750., "Narrow"), (1000., "OneK"), (2000., "TwoK"), (2500., "Wide")]:
    RK["rank" + tag] = rank([r for r in E4 if r["fam"] == "k0" and r["assumed"] == a])
open("../tex/results.tex", "a").write("\n".join(f"\\newcommand{{\\{k}}}{{{v:.2f}}}" for k, v in RK.items()) + "\n")
# tables as macros (an \\input inside a tabular breaks booktabs rules)
with open("../tex/results.tex", "a") as f:
    for name, fn in [("tabEtwo", "tab_e2.tex"), ("tabEthree", "tab_e3.tex"), ("tabEfour", "tab_e4.tex")]:
        f.write("\\newcommand{\\%s}{%%\n%s}\n" % (name, open("../tex/" + fn).read()))
