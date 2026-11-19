"use client";

import { useStore } from "@/state";

/**
 * ID / EN switch. Text is written in English in the components and looked up here when the
 * language is Indonesian (screen 07-ID). Strings without an entry stay in English.
 */
const ID: Record<string, string> = {
  // top bar
  Map: "Peta",
  Runs: "Run",
  Compare: "Bandingkan",
  Validation: "Validasi",
  Export: "Ekspor",
  Published: "Terbit",
  Private: "Privat",
  Superseded: "Diganti",
  Running: "Berjalan",
  Stopped: "Berhenti",
  Draft: "Draf",
  Empty: "Kosong",
  "Switch run": "Ganti run",
  "Public view": "Tampilan publik",
  "Not signed in · Sign in": "Belum masuk · Masuk",

  // layers panel
  Layers: "Lapisan",
  "Research outputs": "Hasil riset",
  "Vertical velocity": "Kecepatan vertikal",
  "mm/yr, sinking positive. 100 m pixels.": "mm/thn, turun bernilai positif. Piksel 100 m.",
  "East–west velocity": "Kecepatan timur–barat",
  "mm/yr. Ground moves inward around a bowl.": "mm/thn. Tanah bergeser ke arah cekungan.",
  "Seasonal amplitude": "Amplitudo musiman",
  "mm. Elastic, recoverable yearly motion.": "mm. Gerak tahunan yang bisa pulih.",
  "Change dates": "Tanggal perubahan",
  "When sinking sped up or slowed down.": "Kapan penurunan makin cepat atau melambat.",
  "Background subsidence": "Penurunan latar",
  "Sinking expected without deep pumping.": "Penurunan yang tetap ada tanpa sumur dalam.",
  Uncertainty: "Ketidakpastian",
  "± mm/yr per pixel, from resampling.": "± mm/thn per piksel, dari resampling.",
  Context: "Konteks",
  "Hot-spot markers (500 m cells)": "Penanda titik panas (sel 500 m)",
  "GNSS stations (InaCORS)": "Stasiun GNSS (InaCORS)",
  "Industrial land": "Lahan industri",
  "Building footprints": "Jejak bangunan",
  "Permit register": "Daftar izin",
  "Regulator only": "Hanya regulator",
  "Usable pixels": "Piksel terpakai",
  "of built-up and industrial land (64% of the whole area). Hatched areas lost radar signal and stay empty.":
    "dari lahan terbangun dan industri (64% dari seluruh area). Area berarsir kehilangan sinyal radar dan dibiarkan kosong.",
  "Sentinel-1 · ascending 127 + descending 76 · Jan 2015 – Oct 2026 · tied to GNSS station CSEM":
    "Sentinel-1 · naik 127 + turun 76 · Jan 2015 – Okt 2026 · terikat ke stasiun GNSS CSEM",

  // map
  "Search cell ID or place": "Cari ID sel atau tempat",
  "No match": "Tidak ditemukan",
  "Where and how fast the ground sinks": "Di mana dan seberapa cepat tanah turun",
  "Open audit list": "Buka daftar audit",
  "Vertical velocity · mm/yr, sinking +": "Kecepatan vertikal · mm/thn, turun +",
  "East–west velocity · mm/yr, east +": "Kecepatan timur–barat · mm/thn, timur +",
  "Seasonal amplitude · mm": "Amplitudo musiman · mm",
  "Change dates · year of the main change": "Tanggal perubahan · tahun perubahan utama",
  "Background subsidence · mm/yr": "Penurunan latar · mm/thn",
  "Background (non-pumping) · mm/yr": "Latar (bukan pemompaan) · mm/thn",
  "Uncertainty · ± mm/yr": "Ketidakpastian · ± mm/thn",
  "No data: radar signal lost over fish ponds and rice fields. Drawn as gaps, never interpolated.":
    "Tanpa data: sinyal radar hilang di tambak dan sawah. Dibiarkan kosong, tidak diisi tebakan.",
  "No data. Radar lost signal over fish ponds. Not interpolated.":
    "Tanpa data. Sinyal radar hilang di tambak. Tidak diisi tebakan.",
  Vertical: "Vertikal",
  "East–west": "Timur–barat",
  "Last change": "Perubahan terakhir",
  "412 images, Jan 2015 – Oct 2026. Seasons removed from the rate.":
    "412 citra, Jan 2015 – Okt 2026. Musim dikeluarkan dari laju.",
  "Zoom in": "Perbesar",
  E: "BT",
  S: "LS",
  "Zoom out": "Perkecil",

  // audit list
  "Audit list": "Daftar audit",
  "Cone width B": "Lebar kerucut B",
  "Radar alone cannot fix B. Volumes are stored for three widths; moving B rescales every volume while the order barely moves.":
    "Radar saja tidak bisa memastikan B. Volume disimpan untuk tiga lebar; mengubah B menggeser semua volume, urutannya hampir tetap.",
  "Sort: volume ↓": "Urutkan: volume ↓",
  low: "rendah",
  mid: "tengah",
  high: "tinggi",
  Volume: "Volume",
  "m³/yr, min.": "m³/thn, min.",

  // evidence
  Stability: "Stabilitas",
  Background: "Latar",
  "of local sinking": "dari penurunan lokal",
  "m³/yr, lower bound": "m³/thn, batas bawah",
  "Volume across cone widths": "Volume untuk tiap lebar kerucut",
  "Lost storage per year, 90% ranges. A lower bound on water pumped.":
    "Simpanan yang hilang per tahun, rentang 90%. Batas bawah air yang dipompa.",
  "Displacement history · 5 nearest pixels": "Riwayat pergeseran · 5 piksel terdekat",
  "What explains the sinking here": "Apa yang menjelaskan penurunan di sini",
  "Land use and permits": "Tata guna lahan dan izin",
  "Copy cell ID": "Salin ID sel",
  Copied: "Tersalin",
  "Export this hot spot": "Ekspor titik panas ini",
  "Permit match hidden": "Kecocokan izin disembunyikan",
  "Sign in as a regulator to see whether this cell matches a permitted well field. The public view shows the 500 m cell and land-use class only.":
    "Masuk sebagai regulator untuk melihat apakah sel ini cocok dengan lapangan sumur berizin. Tampilan publik hanya menunjukkan sel 500 m dan kelas lahan.",
  "Back to the audit list": "Kembali ke daftar audit",

  // planner
  "Sinking that would remain": "Penurunan yang akan tersisa",
  "For planners: how much the ground keeps sinking even if deep pumping stops.":
    "Untuk perencana: seberapa banyak tanah tetap turun walau sumur dalam berhenti.",
  District: "Kecamatan",
  "Sinking now": "Turun sekarang",
  "From pumping": "Dari pemompaan",
  "mm/yr, median": "mm/thn, median",
  "mm/yr": "mm/thn",
  "What drives the background here": "Apa yang mendorong penurunan latar di sini",
  "Soft-clay thickness": "Tebal lempung lunak",
  "Distance to coast": "Jarak ke pantai",
  "Built-up volume": "Volume bangunan",
  "Reclaimed land": "Lahan reklamasi",
  Elevation: "Ketinggian",
  "mm/yr each driver adds (Shapley values). Boosted trees trained on quiet pixels only, more than 2B from industry and known wells. Never sees coordinates.":
    "mm/thn yang ditambahkan tiap faktor (nilai Shapley). Boosted trees dilatih hanya pada piksel tenang, lebih dari 2B dari industri dan sumur yang diketahui. Tidak pernah melihat koordinat.",
  Now: "Sekarang",
  Share: "Porsi",
  "mm/yr, 2015–2026": "mm/thn, 2015–2026",
  "Export background map": "Ekspor peta latar",
  "would remain": "akan tersisa",
};

export type Lang = "ID" | "EN";

export function tr(lang: Lang, s: string) {
  return lang === "ID" ? (ID[s] ?? s) : s;
}

/** Number with the decimal mark of the language: 6.1 in English, 6,1 in Indonesian. */
export function num(lang: Lang, v: number, digits = 1) {
  const s = v.toFixed(digits);
  return lang === "ID" ? s.replace(".", ",") : s;
}

export function useT() {
  const { lang } = useStore();
  return {
    lang,
    t: (s: string) => tr(lang, s),
    n: (v: number, digits = 1) => num(lang, v, digits),
    /** English or Indonesian text inline, for sentences built from values */
    pick: (en: string, id: string) => (lang === "ID" ? id : en),
  };
}
