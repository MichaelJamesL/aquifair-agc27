"""English display text for the curated files.

The seed files keep the official Indonesian names (they are matched against the raw sources when rebuilt);
the API serves English. Agency and survey acronyms (BPS, ESDM, PDAM, SPAM, NPA, APBD) stay as they are.
"""

from __future__ import annotations

import re
from typing import Any

# Codes and keys the frontend or other files match on, never prose.
KEEP_KEYS = frozenset({"id", "region_id", "source_id", "source_ids", "url", "type", "gid", "step", "wilayah"})

# Longest phrases first: titles and agency names, then legal forms, then single words.
PHRASES: list[tuple[str, str]] = [
    (
        "Peta Zona Konservasi Air Tanah Akuifer Tertekan CAT Semarang-Demak 2022",
        "Groundwater conservation zones of the confined aquifer, Semarang-Demak groundwater basin, 2022",
    ),
    (
        "Wilayah A = Kota Semarang, Tegal, Pekalongan, Surakarta and "
        "Kab. Kudus, Rembang, Blora, Pemalang, Brebes, Demak",
        "Price area A = the cities of Semarang, Tegal, Pekalongan and Surakarta and the regencies of Kudus, "
        "Rembang, Blora, Pemalang, Brebes and Demak",
    ),
    ("SPAM Semarang Barat, penopang kebutuhan air Kota Atlas", "West Semarang SPAM, supplying Semarang's water needs"),
    ("Kota Semarang Dalam Angka", "Semarang City in Figures"),
    (
        "Dinas Perumahan, Kawasan Permukiman dan Pertanahan Kab. Demak",
        "Demak Regency housing, settlement and land office",
    ),
    ("Dinas Kependudukan dan Pencatatan Sipil Kab. Demak", "Demak Regency population and civil registry office"),
    ("Portal Data Demak", "Demak open-data portal"),
    ("Badan Pusat Statistik Provinsi Jawa Tengah", "Statistics Indonesia (BPS), Central Java"),
    ("Badan Pusat Statistik", "Statistics Indonesia (BPS)"),
    ("Pemerintah Provinsi Jawa Tengah", "Central Java provincial government"),
    ("Pemerintah Kota Semarang", "Semarang city government"),
    ("Perumda Air Minum Tirta Moedal Kota Semarang", "Tirta Moedal, the Semarang city water utility"),
    ("Perumda Air Minum Tirta Moedal", "Tirta Moedal water utility"),
    ("Hasina Jurnal Akuntansi dan Bisnis Syariah", "Hasina, journal of Islamic accounting and business"),
    (
        "Bapenda Kota Semarang / APBD / LKPJ",
        "Semarang city revenue agency (Bapenda), budget (APBD) and accountability report (LKPJ)",
    ),
    ("Bapenda Kota Semarang", "Semarang city revenue agency (Bapenda)"),
    ("Bappeda Kota Semarang", "Semarang city planning agency (Bappeda)"),
    ("Dinas ESDM Provinsi Jawa Tengah", "Central Java ESDM office"),
    ("Dinas ESDM Jawa Tengah", "Central Java ESDM office"),
    ("Dinas ESDM Jateng", "Central Java ESDM office"),
    ("from Dinas ESDM", "from the ESDM office"),
    ("Dinas ESDM", "ESDM office"),
    ("Kepgub Jawa Tengah", "Central Java Governor Decree"),
    ("Pergub Jawa Tengah", "Central Java Governor Regulation"),
    ("Pergub Jateng", "Central Java Governor Regulation"),
    ("Pergub", "Governor Regulation"),
    ("Perda Kota Semarang", "Semarang City Bylaw"),
    ("Perda", "Bylaw"),
    ("Permen ESDM", "ESDM Ministerial Regulation"),
    ("Penetapan Nilai Perolehan Air Tanah", "setting the groundwater acquisition value"),
    ("Nilai Perolehan Air Tanah", "groundwater acquisition value"),
    ("CaLK, Pajak Air Tanah:", "Notes to the financial statements, groundwater tax:"),
    ("CaLK, Pajak Air Tanah", "notes to the financial statements, groundwater tax"),
    ("Pajak Air Tanah", "Groundwater tax"),
    ("harga dasar air", "base water price"),
    ("'Sumur Bor' markers", "drilled-well markers"),
    ("Sumur Bor", "drilled wells"),
    ("per wilayah", "per price area"),
    ("Jawa Tengah", "Central Java"),
    ("Jateng", "Central Java"),
    ("SPAM Semarang Barat", "West Semarang SPAM"),
    ("by kabupaten/kota", "by regency and city"),
    ("kabupaten/kota", "regencies and cities"),
    ("kab/kota", "regencies and cities"),
    ("Served kecamatan", "Served districts"),
    ("three kecamatan", "three districts"),
    ("to kecamatan", "to districts"),
    ("kecamatan", "district"),
    ("kelurahan", "village"),
    ("NERACA", "AquiFair"),  # the app's former name, also Indonesian for "balance"
]

COMPASS = {"Barat": "West", "Timur": "East", "Utara": "North", "Selatan": "South", "Tengah": "Central"}
NOT_COMPASS = {"Karang"}  # Karang Tengah is one name (Karangtengah), not "central Karang"
PATTERNS: list[tuple[re.Pattern[str], Any]] = [
    (re.compile(r"\bWilayah ([ABC])\b"), r"price area \1"),
    (re.compile(r"\bKab\.? ([A-Z][a-z]+)\b"), r"\1 Regency"),
    (re.compile(r"\bKota ([A-Z][a-z]+)\b"), r"\1 City"),
    (
        re.compile(r"\b([A-Z][a-z]+) (Barat|Timur|Utara|Selatan|Tengah)\b"),
        lambda m: m.group(0) if m.group(1) in NOT_COMPASS else f"{COMPASS[m.group(2)]} {m.group(1)}",
    ),
]


def english_text(text: str) -> str:
    for old, new in PHRASES:
        text = text.replace(old, new)
    for pattern, repl in PATTERNS:
        text = pattern.sub(repl, text)
    return text


def english(value: Any, key: str = "") -> Any:
    """Translate every prose string in a parsed JSON value; codes under KEEP_KEYS pass through."""
    if key in KEEP_KEYS:
        return value
    if isinstance(value, str):
        return english_text(value)
    if isinstance(value, list):
        return [english(item, key) for item in value]
    if isinstance(value, dict):
        return {k: english(v, k) for k, v in value.items()}
    return value
