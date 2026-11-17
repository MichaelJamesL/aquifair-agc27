"""Download the ALOS-1 PALSAR L1.0 stack chosen by alos_search.py (path 431, frame 7040,
ascending, FBS + FBD, 2006-12..2010-11, 21 scenes) into realdata/semarang/alos/raw.
Credentials: reads ~/.netrc (machine urs.earthdata.nasa.gov) written by the user; this
script never asks for or stores a password. Run in WSL:
  MAMBA_ROOT_PREFIX=~/mamba ~/bin/micromamba run -n alos python alos_download.py
"""
import json, os, netrc
import asf_search as asf

ROOT = "/mnt/c/Kuliah/hackathon/agc-26/realdata/semarang/alos"
rows = [r for r in json.load(open(f"{ROOT}/scenes.json"))
        if r["path"] == 431 and r["frame"] == 7040 and r["orbit"] == "ASCENDING" and r["beam"] in ("FBS", "FBD")]
os.makedirs(f"{ROOT}/raw", exist_ok=True)
login, _, password = netrc.netrc().authenticators("urs.earthdata.nasa.gov")
session = asf.ASFSession().auth_with_creds(login, password)
todo = [r for r in sorted(rows, key=lambda r: r["date"]) if not os.path.exists(f"{ROOT}/raw/{os.path.basename(r['url'])}")]
print(len(rows), "scenes,", len(todo), "to download")
asf.download_urls(urls=[r["url"] for r in todo], path=f"{ROOT}/raw", session=session, processes=2)
print("done", sorted(os.listdir(f"{ROOT}/raw")))
