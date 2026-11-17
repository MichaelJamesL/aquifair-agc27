"""Merge all ADWR pump-data exports in realdata/arizona/pump/ into pump_all.csv (one row per well)."""
import glob, subprocess, sys
import pandas as pd

A = "C:/Kuliah/hackathon/agc-26/realdata/arizona"
files = sorted(f for f in glob.glob(f"{A}/pump/*.xls") if " (" not in f)          # skip browser duplicates
subprocess.run([sys.executable, "az_pump_parse.py", f"{A}/pump_all_raw.csv", *files], check=True)
d = pd.read_csv(f"{A}/pump_all_raw.csv", dtype={"REGISTRY_ID": str}).drop_duplicates("REGISTRY_ID")
d.to_csv(f"{A}/pump_all.csv", index=False)
yrs = [c for c in d.columns if c.isdigit()]
print("files", len(files), "wells", len(d), "years", yrs[0], "-", yrs[-1])
print("acre-ft by year:", d[[y for y in yrs if "2015" <= y <= "2024"]].sum().round(0).to_dict())
print("wells pumping in 2018-2022:", int((d[[y for y in yrs if "2018" <= y <= "2022"]].fillna(0).sum(1) > 0).sum()))
