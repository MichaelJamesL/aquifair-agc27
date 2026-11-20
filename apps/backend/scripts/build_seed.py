"""Build the NERACA seed files from real public data.

Inputs:
  scripts/raw/esdm_2020.json ... esdm_2023.json  (CKAN datastore responses)
  ../realdata/semarang/admin/idn_adm2.geojson     (local, git-ignored)

Outputs:
  data/*.json, data/regions.geojson
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "scripts" / "raw"
DATA = ROOT / "data"
REPO = ROOT.parents[1]
ADM2 = REPO / "realdata" / "semarang" / "admin" / "idn_adm2.geojson"

# BPS code, canonical name, type, NPA wilayah, ESDM spelling, geoBoundaries shapeName.
REGIONS: list[tuple[str, str, str, str, str, str]] = [
    ("3301", "Kab. Cilacap", "kabupaten", "B", "Kab. Cilacap", "Cilacap"),
    ("3302", "Kab. Banyumas", "kabupaten", "B", "Kab. Banyumas", "Banyumas"),
    ("3303", "Kab. Purbalingga", "kabupaten", "A", "Kab. Purbalingga", "Purbalingga"),
    ("3304", "Kab. Banjarnegara", "kabupaten", "A", "Kab. Banjarnegara", "Banjarnegara"),
    ("3305", "Kab. Kebumen", "kabupaten", "A", "Kab. Kebumen", "Kebumen"),
    ("3306", "Kab. Purworejo", "kabupaten", "A", "Kab. Purworejo", "Purworejo"),
    ("3307", "Kab. Wonosobo", "kabupaten", "A", "Kab. Wonosobo", "Wonosobo"),
    ("3308", "Kab. Magelang", "kabupaten", "A", "Kab. Magelang", "Magelang"),
    ("3309", "Kab. Boyolali", "kabupaten", "B", "Kab. Boyolali", "Boyolali"),
    ("3310", "Kab. Klaten", "kabupaten", "B", "Kab. Klaten", "Klaten"),
    ("3311", "Kab. Sukoharjo", "kabupaten", "B", "Kab. Sukoharjo", "Sukoharjo"),
    ("3312", "Kab. Wonogiri", "kabupaten", "A", "Kab. Wonogiri", "Wonogiri"),
    ("3313", "Kab. Karanganyar", "kabupaten", "B", "Kab Karanganyar", "Karanganyar"),
    ("3314", "Kab. Sragen", "kabupaten", "A", "Kab Sragen", "Sragen"),
    ("3315", "Kab. Grobogan", "kabupaten", "A", "Kab. Grobogan", "Grobogan"),
    ("3316", "Kab. Blora", "kabupaten", "A", "Kab. Blora", "Blora"),
    ("3317", "Kab. Rembang", "kabupaten", "A", "Kab. Rembang", "Rembang"),
    ("3318", "Kab. Pati", "kabupaten", "B", "Kab. Pati", "Pati"),
    ("3319", "Kab. Kudus", "kabupaten", "C", "Kab. Kudus", "Kudus"),
    ("3320", "Kab. Jepara", "kabupaten", "B", "Kab. Jepara", "Jepara"),
    ("3321", "Kab. Demak", "kabupaten", "C", "Kab. Demak", "Demak"),
    ("3322", "Kab. Semarang", "kabupaten", "B", "Kab. Semarang", "Semarang"),
    ("3323", "Kab. Temanggung", "kabupaten", "A", "Kab. Temanggung", "Temanggung"),
    ("3324", "Kab. Kendal", "kabupaten", "B", "Kab. Kendal", "Kendal"),
    ("3325", "Kab. Batang", "kabupaten", "B", "Kab. Batang", "Batang"),
    ("3326", "Kab. Pekalongan", "kabupaten", "C", "Kab. Pekalongan", "Pekalongan"),
    ("3327", "Kab. Pemalang", "kabupaten", "A", "Kab. Pemalang", "Pemalang"),
    ("3328", "Kab. Tegal", "kabupaten", "A", "Kab. Tegal", "Tegal"),
    ("3329", "Kab. Brebes", "kabupaten", "B", "Kab. Brebes", "Brebes"),
    ("3371", "Kota Magelang", "kota", "A", "Kota Magelang", "Kota Magelang"),
    ("3372", "Kota Surakarta", "kota", "C", "Kota Surakarta", "Kota Surakarta"),
    ("3373", "Kota Salatiga", "kota", "B", "Kota Salatiga", "Kota Salatiga"),
    ("3374", "Kota Semarang", "kota", "C", "Kota Semarang", "Kota Semarang"),
    ("3375", "Kota Pekalongan", "kota", "B", "Kota Pekalongan", "Kota Pekalongan"),
    ("3376", "Kota Tegal", "kota", "B", "Kota Tegal", "Kota Tegal"),
]

SOURCES: list[dict[str, Any]] = [
    {
        "id": "PERGUB-7-2025",
        "name": "Pergub Jawa Tengah 7/2025: Penetapan Nilai Perolehan Air Tanah",
        "publisher": "Pemerintah Provinsi Jawa Tengah",
        "url": "https://peraturan.bpk.go.id/Details/314690/pergub-prov-jawa-tengah-no-7-tahun-2025",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "In force 18 February 2025. HAB and BAT tables in the annex.",
    },
    {
        "id": "ESDM-NPA-2020",
        "name": "NPA and groundwater abstraction volume 2020",
        "publisher": "Dinas ESDM Provinsi Jawa Tengah",
        "url": "https://data.jatengprov.go.id/dataset/fcc-nilai-perolehan-air-tanah-npa-dan-volume-pengambilan-pengusahaan-air-tanah-di-provinsi-jawa-teng",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "CC-BY. CKAN resource 6e4abb61-78ab-40dd-a21c-1242d4b677f9.",
    },
    {
        "id": "ESDM-NPA-2021",
        "name": "NPA and groundwater abstraction volume 2021",
        "publisher": "Dinas ESDM Provinsi Jawa Tengah",
        "url": "https://data.jatengprov.go.id/dataset/fcc-nilai-perolehan-air-tanah-npa-dan-volume-pengambilan-pengusahaan-air-tanah-di-provinsi-jawa-teng",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "CC-BY. CKAN resource 8af351c3-f1b4-425e-b59b-681696e3a542.",
    },
    {
        "id": "ESDM-NPA-2022",
        "name": "NPA and groundwater abstraction volume 2022",
        "publisher": "Dinas ESDM Provinsi Jawa Tengah",
        "url": "https://data.jatengprov.go.id/dataset/fcc-nilai-perolehan-air-tanah-npa-dan-volume-pengambilan-pengusahaan-air-tanah-di-provinsi-jawa-teng",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "CC-BY. CKAN resource 1bb2a757-b231-4716-9009-a55c8c5b1fdd.",
    },
    {
        "id": "ESDM-NPA-2023",
        "name": "NPA and groundwater abstraction volume 2023",
        "publisher": "Dinas ESDM Provinsi Jawa Tengah",
        "url": "https://data.jatengprov.go.id/dataset/fcc-nilai-perolehan-air-tanah-npa-dan-volume-pengambilan-pengusahaan-air-tanah-di-provinsi-jawa-teng",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "CC-BY. CKAN resource 276bcab2-ab5d-45c4-b2d6-c3daa637f3b8. Kota Semarang 2023: 10,069,814 m3.",
    },
    {
        "id": "BPS-JATENG",
        "name": "BPS province and regency codes, Central Java",
        "publisher": "Badan Pusat Statistik",
        "url": "https://jateng.bps.go.id/",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Used only to key the 35 kabupaten/kota.",
    },
    {
        "id": "PERDA-SMG-2024",
        "name": "Perda Kota Semarang 4/2024: environmental protection and management plan, 2024-2054",
        "publisher": "Pemerintah Kota Semarang",
        "url": None,
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Local copy realdata/semarang/perda/p.txt. Gives PDAM sales and registered abstraction.",
    },
    {
        "id": "PERDA-10-2023",
        "name": "Perda Kota Semarang 10/2023: regional taxes and levies",
        "publisher": "Pemerintah Kota Semarang",
        "url": "https://pasal.id/peraturan/perda/perda-kota-semarang-no-10-tahun-2023",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Amended by Perda 4/2025. The 20 % PAT rate is reported by a tax news service.",
    },
    {
        "id": "TERC-2024",
        "name": "TERC LPEM FEB UI policy brief: surface and groundwater tax",
        "publisher": "Universitas Indonesia",
        "url": "https://terc.lpem.org/wp-content/uploads/2024/04/PAP_dan_PAT-TERC_Brief.pdf",
        "label": "WEAK",
        "accessed": "2026-11-19",
        "note": "Secondary source for the 20 % maximum under UU 1/2022.",
    },
    {
        "id": "DDTC-SMG",
        "name": "DDTC News: latest local tax rates in Kota Semarang",
        "publisher": "DDTC News",
        "url": "https://news.ddtc.co.id/berita/daerah/1800913/ketentuan-terbaru-tarif-pajak-daerah-di-kota-semarang-cek-di-sini",
        "label": "WEAK",
        "accessed": "2026-11-19",
        "note": "Secondary source for the 20 % PAT rate.",
    },
    {
        "id": "PDAM-COVERAGE",
        "name": "Perumda Air Minum Tirta Moedal: service coverage",
        "publisher": "Perumda Air Minum Tirta Moedal Kota Semarang",
        "url": "https://pdamkotasmg.co.id/index.php/page/cakupan_pelayanan",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "52 % service coverage, 200k+ customers, 3,600 L/s production.",
    },
    {
        "id": "SPAM-SETKAB",
        "name": "Presiden resmikan SPAM Semarang Barat",
        "publisher": "Sekretariat Kabinet Republik Indonesia",
        "url": "https://setkab.go.id/resmikan-spam-semarang-barat-presiden-bantu-masyarakat-peroleh-air-bersih-terjangkau/",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Opening 23 January 2024; Jatibarang reservoir.",
    },
    {
        "id": "SPAM-EKON",
        "name": "Operational SPAM Semarang Barat",
        "publisher": "Kemenko Perekonomian",
        "url": "https://ekon.go.id/unduh/publikasi/4380/pemerintah-dorong-peningkatan-ketersediaan-air-minum-dengan-operasional-psn-spam-semarang-barat",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Design capacity 1,000 L/s; 605 L/s uptake in January 2024.",
    },
    {
        "id": "SPAM-ANTARA",
        "name": "SPAM Semarang Barat, penopang kebutuhan air Kota Atlas",
        "publisher": "ANTARA News",
        "url": "https://www.antaranews.com/berita/4014417/spam-semarang-barat-penopang-kebutuhan-air-kota-atlas",
        "label": "WEAK",
        "accessed": "2026-11-19",
        "note": "70,000 household connections; Semarang Barat, Ngaliyan, Tugu; PDAM coverage rises to 80 %.",
    },
    {
        "id": "SPAM-HASINA",
        "name": "Evaluation of the SPAM Semarang Barat PPP project 2024",
        "publisher": "Hasina Jurnal Akuntansi dan Bisnis Syariah",
        "url": "https://doi.org/10.35897/hasina.v2i2.2032",
        "label": "WEAK",
        "accessed": "2026-11-19",
        "note": "COD 22 May 2021; 47,261 customers in the west area by September 2024.",
    },
    {
        "id": "LICSAR",
        "name": "LiCSAR Sentinel-1 ground motion, Semarang 2014-2026",
        "publisher": "COMET / University of Leeds",
        "url": "https://comet.nerc.ac.uk/comet-lics-portal/",
        "label": "MEASURED",
        "accessed": "2026-11-19",
        "note": "Frames 076D descending and 127A ascending, processed locally.",
    },
    {
        "id": "GEOBOUNDARIES",
        "name": "geoBoundaries ADM2 boundaries, Indonesia",
        "publisher": "geoBoundaries",
        "url": "https://www.geoboundaries.org/",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Filtered to the 35 Central Java kabupaten/kota.",
    },
    {
        "id": "EXP04",
        "name": "Experiment 4: blind test and repeatability",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-19",
        "note": "Sinking signals repeat across periods and tracks.",
    },
    {
        "id": "EXP07",
        "name": "Experiment 7: Semarang water-demand model at 4 km",
        "publisher": "NERACA research log",
        "url": None,
        "label": "CALCULATED",
        "accessed": "2026-11-19",
        "note": "Unvalidated 4 km demand model. Kota Semarang 25-48 Mm3/yr, median 36.5.",
    },
    {
        "id": "EXP09",
        "name": "Experiment 9: validated 16 km regional volume split",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-19",
        "note": (
            "Passed pre-registered confirmation in two unseen regions. Semarang west+central: "
            "27.9/43.8/54.7 Mm3/yr (P10/P50/P90)."
        ),
    },
    {
        "id": "EXP13",
        "name": "Experiment 13: registered wells against sinking",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-19",
        "note": "Registered deep wells do not sit on faster-sinking ground.",
    },
    {
        "id": "EXP14",
        "name": "Experiment 14: what explains the sinking",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-19",
        "note": "Soft-clay thickness explains about 80 % of the pattern; fast areas slowed from 113 to 89 mm/yr.",
    },
    {
        "id": "X08",
        "name": "Real-data period medians, Semarang",
        "publisher": "NERACA analysis on Sentinel-1 LiCSAR",
        "url": None,
        "label": "MEASURED",
        "accessed": "2026-11-19",
        "note": "Fast-area medians: 112.8 (2014-17), 103.1 (2018-22), 88.7 mm/yr (2023-26).",
    },
    {
        "id": "X05",
        "name": "Real-data cause tests: soft-clay thickness",
        "publisher": "NERACA analysis on Sentinel-1 LiCSAR",
        "url": None,
        "label": "MEASURED",
        "accessed": "2026-11-19",
        "note": "Clay thickness vs sinking, rho 0.81, p 0.003.",
    },
    {
        "id": "LO-2022",
        "name": "Lo et al. 2022: InSAR and MODFLOW in Semarang",
        "publisher": "Water 14(2), 201",
        "url": "https://doi.org/10.3390/w14020201",
        "label": "MEASURED",
        "accessed": "2026-11-19",
        "note": "Registered wells and heads; permits on request from Dinas ESDM.",
    },
    {
        "id": "ZONE-2022",
        "name": "CAT Semarang-Demak conservation zones, 2022",
        "publisher": "Dinas ESDM Provinsi Jawa Tengah",
        "url": "https://eprints2.undip.ac.id/55333/3/Bab%20I.pdf",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Map not yet digitised. In critical and damaged zones no new abstraction permit can be issued.",
    },
    {
        "id": "ADWR",
        "name": "Arizona Department of Water Resources Wells 55 and pump data",
        "publisher": "ADWR",
        "url": "https://gisweb.azwater.gov/",
        "label": "OFFICIAL",
        "accessed": "2026-11-19",
        "note": "Used for V4 and V8 only; not part of the Central Java accounts.",
    },
    {
        "id": "EXP05",
        "name": "Experiment 5: Arizona metered-pumping validation",
        "publisher": "NERACA research log",
        "url": None,
        "label": "TESTED",
        "accessed": "2026-11-19",
        "note": "T4 warned that a pumping cut may not show in sinking.",
    },
    {
        "id": "PDAM-NETWORK",
        "name": "PDAM coverage per kelurahan",
        "publisher": "Perumda Air Minum Tirta Moedal Kota Semarang",
        "url": None,
        "label": "MISSING",
        "accessed": None,
        "note": "Not public. A PPID request is needed; until then filter 4 is a proxy.",
    },
    {
        "id": "SPAM-SERVICE-AREA",
        "name": "SPAM Semarang Barat service-area map",
        "publisher": "PDAM / Kementerian PUPR",
        "url": None,
        "label": "MISSING",
        "accessed": None,
        "note": "Not obtained. The three named districts are used meanwhile.",
    },
    {
        "id": "APBD-SMG",
        "name": "Realised groundwater tax, Kota Semarang 2020-2025",
        "publisher": "Bapenda Kota Semarang / APBD / LKPJ",
        "url": None,
        "label": "MISSING",
        "accessed": None,
        "note": "Needed for V1. Not in the open dataset.",
    },
]


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"\s+", "", text)
    # The 2022 CKAN resource stores numbers as strings ending in ".0". Treat that
    # as a decimal artefact, not as a thousands separator; the other dots are
    # Indonesian thousands separators (one row is even "14.418.370.56").
    if text.endswith(".0"):
        text = text[:-2]
    elif text.endswith(".00"):
        text = text[:-3]
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def normalise_region_name(name: str) -> str:
    text = name.lower().replace(".", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^kab\b", "kabupaten", text)
    return text


def load_esdm() -> dict[int, dict[str, dict[str, Any]]]:
    by_year: dict[int, dict[str, dict[str, Any]]] = {}
    for year in (2020, 2021, 2022, 2023):
        path = RAW / f"esdm_{year}.json"
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        records = payload["result"]["records"]
        by_year[year] = {normalise_region_name(record["kabupatenkota_data"]): record for record in records}
    return by_year


def build_accounts() -> list[dict[str, Any]]:
    by_year = load_esdm()
    records: list[dict[str, Any]] = []
    for code, _name, _kind, _wilayah, esdm_name, _shape in REGIONS:
        for year in (2020, 2021, 2022, 2023):
            raw = by_year[year].get(normalise_region_name(esdm_name))
            if raw is None:
                raise RuntimeError(f"missing ESDM row {esdm_name!r} in {year}")
            volume = parse_number(raw.get("volume_pengusahaan_air_tanah"))
            npa = parse_number(raw.get("nilai_perolehan_air_data"))
            declared = int(volume) if volume not in (None, 0) else None
            npa_value = int(npa) if npa not in (None, 0) else None
            if declared is None:
                npa_value = None
            records.append(
                {
                    "region_id": code,
                    "year": year,
                    "declared_m3": declared,
                    "npa_value_idr": npa_value,
                    "source_ids": [f"ESDM-NPA-{year}"],
                }
            )
    return records


def build_regions_geojson() -> dict[str, Any]:
    payload = json.loads(ADM2.read_text(encoding="utf-8"))
    shape_to_code = {shape: code for code, _n, _k, _w, _e, shape in REGIONS}
    features = [feature for feature in payload["features"] if feature["properties"].get("shapeName") in shape_to_code]
    if len(features) != len(REGIONS):
        found = sorted(f["properties"]["shapeName"] for f in features)
        raise RuntimeError(f"expected {len(REGIONS)} features, found {len(features)}: {found}")
    for feature in features:
        shape = feature["properties"]["shapeName"]
        feature["properties"]["region_id"] = shape_to_code[shape]
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    regions = [
        {
            "id": code,
            "name": name,
            "type": kind,
            "wilayah": wilayah,
            "source_ids": ["PERGUB-7-2025", "BPS-JATENG"],
        }
        for code, name, kind, wilayah, _esdm, _shape in REGIONS
    ]
    (DATA / "regions.json").write_text(json.dumps(regions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (DATA / "sources.json").write_text(json.dumps(SOURCES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (DATA / "accounts.json").write_text(
        json.dumps(build_accounts(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # The 38-61 Mm3/yr city total behind the split is from 2000-2010 studies, so it is not year-specific.
    estimates = [
        {
            "region_id": "3374",
            "year": year,
            "method": "validated_16km_split",
            "low_m3": 27_900_000,
            "central_m3": 43_800_000,
            "high_m3": 54_700_000,
            "label": "TESTED",
            "source_ids": ["EXP09"],
            "note": (
                "Semarang west and central 16 km cell, P10/P50/P90. Validated in two unseen regions. "
                "The city total it splits is from 2000-2010 studies, so every year gets the same range."
            ),
        }
        for year in (2020, 2021, 2022, 2023)
    ] + [
        {
            "region_id": "3374",
            "year": 2023,
            "method": "demand_4km",
            "low_m3": 25_000_000,
            "central_m3": 36_500_000,
            "high_m3": 48_000_000,
            "label": "CALCULATED",
            "source_ids": ["EXP07"],
            "note": "4 km demand model, not validated at this scale.",
        },
    ]
    (DATA / "estimates.json").write_text(json.dumps(estimates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    terms = [
        {
            "region_id": "3374",
            "year": year,
            "household_wells_low_m3": 0,
            "household_wells_high_m3": 25_000_000,
            "public_supply_low_m3": 0,
            "public_supply_high_m3": 10_000_000,
            "source_ids": ["PERDA-SMG-2024", "EXP09"],
            "note": (
                "Household wells outside PDAM: PDAM households 41.63 x 38/62, an upper bound that "
                "includes shallow wells and springs. Public supply wells: about 19 % of PDAM "
                "supply, if not already in the declared volume. The range is the point."
            ),
        }
        for year in (2020, 2021, 2022, 2023)
    ]
    (DATA / "account_terms.json").write_text(json.dumps(terms, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    leads = {
        "status": "unavailable",
        "reason": (
            "The 2022 conservation-zone map has not been digitised and PDAM coverage per "
            "kelurahan is not public. Building-change data exists, but filters 3 and 4 cannot "
            "yet be applied, so no lead is asserted."
        ),
        "items": [],
    }
    (DATA / "leads.json").write_text(json.dumps(leads, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pipe_cells = {
        "status": "unavailable",
        "reason": (
            "The 4 km demand layer and the SPAM service-area layer are not in a common grid. "
            "The validated 16 km volume split is available in module A; ranking within the city "
            "failed validation, so no pipe-priority cell is asserted."
        ),
        "items": [],
    }
    (DATA / "pipe_cells.json").write_text(json.dumps(pipe_cells, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pipes = {
        "periods": [
            {
                "key": "2014_17",
                "label": "2014-2017",
                "fast_mm_yr": 112.77708029635772,
                "land_mm_yr": 57.505556576238654,
                "source_ids": ["X08", "EXP14"],
            },
            {
                "key": "2018_22",
                "label": "2018-2022",
                "fast_mm_yr": 103.1020995420402,
                "land_mm_yr": 48.84299423491922,
                "source_ids": ["X08", "EXP14"],
            },
            {
                "key": "2023_26",
                "label": "2023-2026",
                "fast_mm_yr": 88.66651297710663,
                "land_mm_yr": 37.729386593961415,
                "source_ids": ["X08", "EXP14"],
            },
        ],
        "spam": {
            "name": "SPAM Semarang Barat",
            "status": "not_run",
            "design_capacity_lps": 1000,
            "uptake_lps_2024_01": 605,
            "uptake_m3_yr_2024": 19_000_000,
            "connections_target": 70_000,
            "connections_actual_2024_09": 47_261,
            "commercial_operation_date": "2021-05-22",
            "districts": ["Semarang Barat", "Ngaliyan", "Tugu"],
            "delta_mm_yr": None,
            "shift_null_p05": None,
            "placebo_year_clean": None,
            "placebo_area_clean": None,
            "positive_control_passed": None,
            "outcome_code": "not_run",
            "outcome_wording": (
                "The SPAM Semarang Barat before/after test has not been run. The app shows "
                "the design and the data on disk, but makes no claim."
            ),
            "source_ids": [
                "SPAM-SETKAB",
                "SPAM-EKON",
                "SPAM-ANTARA",
                "SPAM-HASINA",
                "EXP14",
                "LICSAR",
            ],
        },
    }
    (DATA / "pipes.json").write_text(json.dumps(pipes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    npa = {
        "regulation": "Pergub Jawa Tengah 7/2025",
        "in_force": "2025-02-18",
        "tax_rate": 0.20,
        "source_ids": ["PERGUB-7-2025", "PERDA-10-2023", "TERC-2024"],
        "hab_idr_per_m3": {"A": 2561, "B": 2795, "C": 2824},
        "resource_component": {
            "good_alternative": 16,
            "good_no_alternative": 9,
            "poor_alternative": 4,
            "poor_no_alternative": 1,
        },
        "use_component": {
            "1": [9.00, 13.50, 20.25, 30.38, 45.56],
            "2": [7.00, 10.50, 15.75, 23.63, 35.44],
            "3": [5.00, 7.50, 11.25, 16.88, 25.31],
            "4": [3.00, 4.50, 6.75, 10.13, 15.19],
            "5": [1.00, 1.50, 2.25, 3.38, 5.06],
        },
        "tiers": [
            {"key": "0_50", "label": "0-50", "min_m3": 0, "max_m3": 50},
            {"key": "51_500", "label": "51-500", "min_m3": 51, "max_m3": 500},
            {"key": "501_1000", "label": "501-1,000", "min_m3": 501, "max_m3": 1000},
            {"key": "1001_2500", "label": "1,001-2,500", "min_m3": 1001, "max_m3": 2500},
            {"key": "over_2500", "label": ">2,500", "min_m3": 2501, "max_m3": None},
        ],
        "groups": [
            {"key": 1, "name": "K1", "description": "Water as a product"},
            {"key": 2, "name": "K2", "description": "High-risk business"},
            {"key": 3, "name": "K3", "description": "Medium-risk business"},
            {"key": 4, "name": "K4", "description": "Low-risk business"},
            {"key": 5, "name": "K5", "description": "Social, government, public supply"},
        ],
        "note": (
            "NPA = HAB x BAT, BAT = 0.6 S + 0.4 P. The service computes NPA from these official "
            "inputs instead of transcribing 300 printed cells. A printed Wilayah C table check: "
            "K1 tier 0-50 = 37,277 Rp/m3."
        ),
    }
    (DATA / "npa.json").write_text(json.dumps(npa, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    validation = [
        {
            "code": "V1",
            "name": "Billing",
            "module": "A",
            "pass_mark": (
                "Realised tax / declared volume lies within 0.20 x the NPA range of groups 2-4 "
                "for that year. Below the range is a billing leak."
            ),
            "status": "planned",
            "result": "waiting",
            "source_ids": ["APBD-SMG", "PERGUB-7-2025"],
        },
        {
            "code": "V2",
            "name": "Volume split",
            "module": "A",
            "pass_mark": "Error within 1.5x on unseen regions at 16 km.",
            "status": "done",
            "result": "pass",
            "source_ids": ["EXP09"],
        },
        {
            "code": "V3",
            "name": "Sinking maps",
            "module": "C",
            "pass_mark": "Signals repeat across periods and tracks above a random null.",
            "status": "done",
            "result": "pass",
            "source_ids": ["EXP04", "LICSAR"],
        },
        {
            "code": "V4",
            "name": "Arizona leads",
            "module": "B",
            "pass_mark": (
                "New large buildings with a new registered well within 500 m in t to t+2 are at "
                "least 1.5x the built-matched null; one-sided permutation p < 0.05."
            ),
            "status": "planned",
            "result": "waiting",
            "source_ids": ["EXP05", "ADWR"],
        },
        {
            "code": "V5",
            "name": "Semarang permits",
            "module": "B",
            "pass_mark": (
                "Leads fall on permitted wells more often than random new buildings of the same size, p < 0.05."
            ),
            "status": "planned",
            "result": "waiting",
            "source_ids": ["LO-2022", "ZONE-2022"],
        },
        {
            "code": "V6",
            "name": "Field hit rate",
            "module": "B",
            "pass_mark": "No pass mark; reported per lead class with a 90 % interval.",
            "status": "waiting",
            "result": "waiting",
            "source_ids": [],
        },
        {
            "code": "V7",
            "name": "SPAM test",
            "module": "C",
            "pass_mark": (
                "Delta below the 5th percentile of the shift null, and both placebos between "
                "the 5th and 95th percentiles."
            ),
            "status": "planned",
            "result": "waiting",
            "source_ids": ["LICSAR", "EXP14", "SPAM-SETKAB"],
        },
        {
            "code": "V8",
            "name": "Positive control in Arizona",
            "module": "C",
            "pass_mark": "The same test detects a known, metered pumping cut.",
            "status": "planned",
            "result": "waiting",
            "source_ids": ["EXP05", "ADWR"],
        },
    ]
    (DATA / "validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    geometry = build_regions_geojson()
    (DATA / "regions.geojson").write_text(
        json.dumps(geometry, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    print(f"wrote {len(regions)} regions, {len(SOURCES)} sources, {len(build_accounts())} account rows")
    print(f"wrote {len(geometry['features'])} boundary features")


if __name__ == "__main__":
    main()
