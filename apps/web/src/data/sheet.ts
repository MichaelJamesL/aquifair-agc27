// Text for the audit sheet (screen 12) and the validation checks shared with the Validation
// screen. Indonesian is the design's source text; English mirrors it.

export type SheetLang = "id" | "en";

/** short land-use class and permit read-out per cell, as printed on the sheet */
export const SHEET_ROWS: Record<string, { land: Record<SheetLang, string>; permit: Record<SheetLang, string> }> = {
  "SMG-2542": { land: { id: "Industri", en: "Industrial" }, permit: { id: "Tidak ada izin dekat", en: "No permit nearby" } },
  "SMG-2650": { land: { id: "Industri", en: "Industrial" }, permit: { id: "Cocok dengan izin", en: "Matches a permit" } },
  "SMG-2331": { land: { id: "Pelabuhan, gudang", en: "Port, warehouses" }, permit: { id: "Tidak ada izin dekat", en: "No permit nearby" } },
  "SMG-2838": { land: { id: "Industri campuran", en: "Mixed industrial" }, permit: { id: "Belum jelas", en: "Unclear" } },
  "SMG-2055": { land: { id: "Industri, tambak", en: "Industrial, fish ponds" }, permit: { id: "Cocok dengan izin", en: "Matches a permit" } },
  "SMG-2408": { land: { id: "Kawasan industri", en: "Industrial estate" }, permit: { id: "Cocok dengan izin", en: "Matches a permit" } },
  "SMG-3336": { land: { id: "Permukiman", en: "Residential" }, permit: { id: "Belum jelas", en: "Unclear" } },
  "SMG-2619": { land: { id: "Permukiman, hotel", en: "Residential, hotel" }, permit: { id: "Tidak ada izin dekat", en: "No permit nearby" } },
};

export type CheckResult = "pass" | "waiting";

export type Check = {
  code: string;
  name: Record<SheetLang, string>;
  how: string;
  value: Record<SheetLang, string>;
  mark: Record<SheetLang, string>;
  markLong: string;
  result: CheckResult;
};

export const CHECKS: Check[] = [
  {
    code: "V1",
    name: { id: "Radar dibanding GNSS", en: "Radar against GNSS" },
    how: "RMS vertical rate at InaCORS stations",
    value: { id: "6,1 mm/thn", en: "6.1 mm/yr" },
    mark: { id: "≤ 8 mm/thn", en: "≤ 8 mm/yr" },
    markLong: "≤ 8 mm/yr",
    result: "pass",
  },
  {
    code: "V2",
    name: { id: "Konsistensi internal", en: "Internal consistency" },
    how: "Loop-closure failures; asc vs desc agreement",
    value: { id: "2,7% pasangan dibuang", en: "2.7% of pairs dropped" },
    mark: { id: "< 5%", en: "< 5%" },
    markLong: "< 5% of pairs",
    result: "pass",
  },
  {
    code: "V3",
    name: { id: "Uji data sintetis, noise run ini", en: "Synthetic test at this run's noise" },
    how: "Benchmark rerun at this run's noise (2.3 mm/yr) and gaps",
    value: { id: "temu 89%, tepat 81%", en: "recall 89%, precision 81%" },
    mark: { id: "≥ 80%", en: "≥ 80%" },
    markLong: "≥ 80%, ≤ 25%",
    result: "pass",
  },
  {
    code: "V4",
    name: { id: "Uji di luar sampel", en: "Out-of-sample fit" },
    how: "Block CV; hold-out 2024–2026 vs trend extension",
    value: { id: "lebih baik dari 2 pembanding", en: "beats both baselines" },
    mark: { id: "kalahkan keduanya", en: "beat both" },
    markLong: "beats both baselines",
    result: "pass",
  },
  {
    code: "V5",
    name: { id: "Sumur: muka air", en: "Wells: heads" },
    how: "Rank correlation, compaction vs head decline",
    value: { id: "belum diuji", en: "not run" },
    mark: { id: "≥ 0,6", en: "≥ 0.6" },
    markLong: "≥ 0.6",
    result: "waiting",
  },
  {
    code: "V6",
    name: { id: "Sumur: lokasi", en: "Wells: locations" },
    how: "High-capacity clusters within 1 km of a source",
    value: { id: "belum diuji", en: "not run" },
    mark: { id: "≥ 70%", en: "≥ 70%" },
    markLong: "≥ 70%",
    result: "waiting",
  },
  {
    code: "V7",
    name: { id: "Rentang yang jujur", en: "Honest ranges" },
    how: "True volumes inside stated 90% range (synthetic)",
    value: { id: "86%", en: "86%" },
    mark: { id: "80–95%", en: "80–95%" },
    markLong: "80–95%",
    result: "pass",
  },
];

export const SOURCES: { code: string; name: Record<SheetLang, string>; status: Record<SheetLang, string>; warn?: boolean }[] = [
  { code: "D1", name: { id: "Sentinel-1, jalur 76 turun dan 127 naik", en: "Sentinel-1, tracks 76 descending and 127 ascending" }, status: { id: "Terbuka", en: "Open" } },
  { code: "D3", name: { id: "GACOS, koreksi atmosfer", en: "GACOS, atmospheric correction" }, status: { id: "Terbuka", en: "Open" } },
  { code: "D4", name: { id: "InaCORS BIG, stasiun CSEM", en: "BIG InaCORS, station CSEM" }, status: { id: "Diterima dari BIG", en: "Received from BIG" } },
  { code: "D5", name: { id: "DEMNAS", en: "DEMNAS" }, status: { id: "Terbuka", en: "Open" } },
  { code: "D7", name: { id: "Geologi, ketebalan lempung", en: "Geology, clay thickness" }, status: { id: "Sebagian", en: "Partial" } },
  { code: "D8", name: { id: "Bangunan dan tata guna lahan", en: "Buildings and land use" }, status: { id: "Terbuka", en: "Open" } },
  { code: "D9", name: { id: "Curah hujan CHIRPS, pasang surut", en: "CHIRPS rainfall, tides" }, status: { id: "Terbuka", en: "Open" } },
  { code: "D6", name: { id: "Catatan sumur dan izin", en: "Well and permit records" }, status: { id: "Belum diterima", en: "Not received" }, warn: true },
];
