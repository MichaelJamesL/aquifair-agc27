"""Piped-water coverage per kecamatan, the proxy for lead filter 4 ("outside the PDAM network").

Kota Semarang: PDAM Tirta Moedal customers per kecamatan 2023 (Kota Semarang Dalam Angka 2024, table 6.3)
divided by population 2023 (table 3.1.1), scaled so that the city as a whole equals the official PDAM
service level of 65.17 % (Perda Kota Semarang 4/2024 background text). BPS publishes no households per
kecamatan, so connections per resident is the comparable quantity.
Kabupaten Demak: households with piped drinking water 2025 (Dinputaru, Portal Data Demak) divided by
family cards (Kartu Keluarga) per kecamatan, semester II 2025 (Dukcapil, Portal Data Demak).
Writes data/pdam_coverage.json. Usage: python scripts/build_pdam_coverage.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REAL = ROOT / "realdata" / "semarang"
DATA = Path(__file__).resolve().parents[1] / "data"
CITY_SERVICE_LEVEL = 0.6517  # Perda Kota Semarang 4/2024: "persentase layanannya baru mencapai 65,17%"
KOTA = ["Mijen", "Gunungpati", "Banyumanik", "Gajah Mungkur", "Semarang Selatan", "Candisari", "Tembalang",
        "Pedurungan", "Genuk", "Gayamsari", "Semarang Timur", "Semarang Utara", "Semarang Tengah",
        "Semarang Barat", "Tugu", "Ngaliyan"]


def _num(text: str) -> float:
    return float(text.replace(".", "").replace(",", "."))


def kota_semarang() -> list[dict]:
    doc = fitz.open(REAL / "bps" / "smg_da2024.pdf")
    pdam = doc[266].get_text()  # Lanjutan Tabel 6.3, 2023 columns
    pop = doc[94].get_text()  # Tabel 3.1.1, population (thousand)
    assert "2023" in pdam and "Pelanggan" in pdam and "3.1.1" in pop
    customers, population = {}, {}
    for name in KOTA:
        m = re.search(re.escape(name) + r"\s*\n\s*([\d.]+)\s*\n", pdam)
        p = re.search(re.escape(name) + r"\s*\n\s*([\d.,]+)\s*\n", pop)
        assert m and p, name
        customers[name] = _num(m.group(1))
        population[name] = _num(p.group(1)) * 1000
    city_ratio = 187_471 / 1_694_740  # table totals: customers 2023, population 2023
    assert abs(sum(customers.values()) - 187_471) < 400  # the rest is Ungaran Barat, Boja, "not filled"
    rows = []
    for name in KOTA:
        share = min(1.0, CITY_SERVICE_LEVEL * (customers[name] / population[name]) / city_ratio)
        rows.append({
            "regency": "Kota Semarang", "kecamatan": name, "year": 2023,
            "coverage": round(share, 3),
            "customers": int(customers[name]), "population": int(population[name]),
            "method": "PDAM customers per resident, scaled to the city service level of 65.17 %",
            "source_ids": ["BPS-SMG-DA-2024", "PERDA-SMG-2024"],
        })
    return rows


def _table(path: Path, value_col: int) -> dict[str, float]:
    df = pd.read_excel(path, header=None)
    out = {}
    for _, row in df.iterrows():
        cells = [c for c in row.tolist() if isinstance(c, str)]
        nums = [c for c in row.tolist() if isinstance(c, (int, float)) and not pd.isna(c)]
        names = [c.strip().upper().replace("KARANGTENGAH", "KARANG TENGAH") for c in cells
                 if c.strip().isupper() and len(c.strip()) > 3]
        if names and nums:
            out[names[0]] = float(nums[value_col])
    return out


def demak() -> list[dict]:
    piped = _table(REAL / "demak" / "jumlah-rumah-tangga-dengan-akses-air-minum-jaringan-perpipaan.xlsx", -1)
    kk = _table(REAL / "demak" / "kk_2025s2.xlsx", -1)
    assert len(piped) == 14 and len(kk) >= 14, (piped, kk)
    rows = []
    for name, households in sorted(piped.items()):
        rows.append({
            "regency": "Kab. Demak", "kecamatan": name.title(), "year": 2025,
            "coverage": round(min(1.0, households / kk[name]), 3),
            "customers": int(households), "population": None, "families": int(kk[name]),
            "method": "Households with piped drinking water / family cards (all piped systems, not PDAM only)",
            "source_ids": ["DEMAK-DINPUTARU-2025", "DEMAK-KK-2025"],
        })
    return rows


def outlines(rows: list[dict]) -> dict:
    """GADM 4.1 kecamatan outlines carrying the coverage value for the map. They are not simplified here:
    fit_coastline.py simplifies all of them together so neighbours keep one shared border."""
    regency = {"KotaSemarang": "Kota Semarang", "Demak": "Kab. Demak", "Kendal": "Kab. Kendal",
               "Semarang": "Kab. Semarang", "Grobogan": "Kab. Grobogan"}
    by_key = {(r["regency"], r["kecamatan"].replace(" ", "").lower()): r for r in rows}
    gadm = json.loads((REAL / "admin/gadm41_adm3_semarang_demak.geojson").read_text(encoding="utf-8"))
    features = []
    for f in gadm["features"]:
        p = f["properties"]
        name = regency.get(p["NAME_2"], p["NAME_2"])
        row = by_key.get((name, p["NAME_3"].lower()))
        features.append({
            "type": "Feature",
            "properties": {
                "gid": p["GID_3"],
                "regency": name,
                "kecamatan": row["kecamatan"] if row else re.sub(r"(?<=[a-z])(?=[A-Z])", " ", p["NAME_3"]),
                "coverage": row["coverage"] if row else None,
                "year": row["year"] if row else None,
            },
            "geometry": f["geometry"],
        })
    assert sum(f["properties"]["coverage"] is not None for f in features) == len(rows)
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    rows = kota_semarang() + demak()
    out = {
        "note": "Proxy for filter 4 until PDAM coverage per kelurahan is released (PPID request).",
        "items": rows,
        "geojson": outlines(rows),
    }
    (DATA / "pdam_coverage.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for r in rows:
        print(r["regency"], r["kecamatan"], r["coverage"])


if __name__ == "__main__":
    main()
