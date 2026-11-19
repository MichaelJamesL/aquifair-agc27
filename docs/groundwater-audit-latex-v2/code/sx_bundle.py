"""Pack the existing Semarang layers on the 200 m model grid into one small file for the subsidence-cause
experiments on the DGX Spark (sx_*.py). Writes realdata/semarang/sx/bundle.npz. Usage: python sx_bundle.py"""
import os
import numpy as np
import synth as S
import real_lib as R
import real_goal_maps as GM

ROOT = GM.ROOT
G = GM.grid
out = {}
D, mask, H, info = GM.load("da", "1822")
out.update(D_da1822=D, mask_da1822=mask, H=H)
# one map per period, descending track only (vertical-only assumption)
for tag, stacks in (("1517", ["t076_1517"]), ("1822", ["t076"]), ("2326", ["t076_2326"])):
    rm = GM.track_map(stacks)
    d, c = G.block_mean(rm["sub"], rm["transform"])
    out[f"D_d{tag}"] = np.where(c >= 1, d, np.nan)
# ascending + descending 2018-22 -> vertical and east components
rms = []
for st in ("t076", "t127"):
    rm = GM.track_map([st])
    g = np.load(f"{ROOT}/{st}/gacos.npz")
    v_los = -rm["sub"] * g["U"][:rm["sub"].shape[0], :rm["sub"].shape[1]]
    rms.append(dict(v_los=v_los, U=g["U"], E=g["E"], transform=rm["transform"]))
    pairs = np.load(f"{ROOT}/{st}/stack.npz")["pairs"]
    out[f"span_{st}"] = np.array([min(pairs)[:8], max(p[9:] for p in pairs)])
up, east, ok = R.vertical_from_two(rms, G)
out.update(D_vert2=up, east2=east)
# per-epoch cumulative displacement (descending SBAS time series) on the model grid
ts = np.load(f"{ROOT}/t076/ts.npz")
tr = np.load(f"{ROOT}/t076/stack.npz")["transform"]
out["ts_epochs"] = ts["epochs"]
out["ts_cum"] = np.stack([G.block_mean(np.where(c != 0, c, np.nan), tr)[0] for c in ts["cum"]]).astype(np.float32)
out["ts_U"] = G.block_mean(np.load(f"{ROOT}/t076/gacos.npz")["U"], tr)[0]
a = np.load(f"{ROOT}/alos/alos_rate_grid.npz")
out.update(D_alos=np.where(a["mask"], a["D"], np.nan))
wc = np.load(f"{ROOT}/worldcover_grid.npz")
out.update({f"wc_{k}": wc[k] for k in wc.files})
out["clay_m"] = np.load(f"{ROOT}/clay_200m.npz")["clay_m"]
ind, _ = R.osm_layers(f"{ROOT}/osm.json", G)
out["osm_industrial"] = ind
w = np.genfromtxt(f"{ROOT}/registry_wells/fig12_wells.csv", delimiter=",", names=True)
out["reg_wells_EN"] = np.c_[w["E"], w["N"]]
out["pangaea_xy"], _ = R.pangaea_wells(f"{ROOT}/pangaea.tab", G)
out.update(E0=G.E0, N0=G.N0, PIX=S.PIX, NX=S.NX, NY=S.NY, epsg=G.epsg)
os.makedirs(f"{ROOT}/sx", exist_ok=True)
np.savez_compressed(f"{ROOT}/sx/bundle.npz", **out)
print({k: (np.shape(v)) for k, v in out.items()})
print("stable noise da1822", info["stable"])
