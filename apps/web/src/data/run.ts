// Demo data for run R-0007 (Semarang–Demak). Values match the Groundtrace Figma screens
// 06–09. Low-B (1.0 km) values for hot spots other than #1 are scaled from the mid values,
// the same way the research code rescales volumes with cone width.
// Replace this file with the API response (GET /audits/{id}/sources) once the backend exists.

export type ConeWidth = "low" | "mid" | "high";

export const CONE_WIDTHS: { key: ConeWidth; km: number; label: string }[] = [
  { key: "low", km: 1.0, label: "low" },
  { key: "mid", km: 1.5, label: "mid" },
  { key: "high", km: 2.0, label: "high" },
];

export type Volume = { v: number; lo: number; hi: number }; // thousand m³/yr

export type MatchClass = "no-permit" | "permit-match" | "permit-near";

export type HotSpot = {
  id: string; // cell ID
  place: string;
  /** position on the 1200×900 map canvas */
  x: number;
  y: number;
  stability: number;
  volume: Record<ConeWidth, Volume>;
  /** share of local sinking assigned to background, % */
  background: number;
  pumpingRate: number; // mm/yr
  backgroundRate: [number, number]; // mm/yr ± sd
  landUse: string;
  buildings: number;
  match: { cls: MatchClass; title: string; text: string };
  changes: { year: number; label: string }[];
  /** sinking rates for the displacement history, per segment between change dates (mm/yr) */
  rates: number[];
};

const mk = (v: number, lo: number, hi: number): Volume => ({ v, lo, hi });

export const HOT_SPOTS: HotSpot[] = [
  {
    id: "SMG-2542",
    place: "Terboyo, Genuk",
    x: 640.4,
    y: 386.2,
    stability: 0.97,
    volume: { low: mk(152, 113, 186), mid: mk(286, 212, 351), high: mk(431, 319, 529) },
    background: 22,
    pumpingRate: 104,
    backgroundRate: [29, 6],
    landUse: "Industrial 82% · residential 11% · other 7%",
    buildings: 146,
    match: {
      cls: "no-permit",
      title: "No permit on record nearby",
      text: "Nearest permitted well field: 1.8 km, outside the 1 km match radius. A lead, not a verdict: a permitted field also makes a bowl.",
    },
    changes: [
      { year: 2018.2, label: "Mar 2018 · sped up" },
      { year: 2023.5, label: "Jul 2023 · slowed" },
    ],
    rates: [95, 125, 90],
  },
  {
    id: "SMG-2650",
    place: "Sayung, Demak",
    x: 758.5,
    y: 397.9,
    stability: 0.95,
    volume: { low: mk(108, 82, 135), mid: mk(197, 151, 246), high: mk(301, 231, 376) },
    background: 18,
    pumpingRate: 96,
    backgroundRate: [21, 5],
    landUse: "Industrial 64% · fish ponds 21% · residential 15%",
    buildings: 98,
    match: {
      cls: "permit-near",
      title: "Permitted well field 0.6 km away",
      text: "Inside the 1 km match radius. Check whether the permitted volume covers what the bowl implies.",
    },
    changes: [{ year: 2019.8, label: "Oct 2019 · sped up" }],
    rates: [70, 112],
  },
  {
    id: "SMG-2331",
    place: "Tanjung Emas",
    x: 477.7,
    y: 352.1,
    stability: 0.93,
    volume: { low: mk(63, 47, 83), mid: mk(113, 84, 149), high: mk(168, 125, 222) },
    background: 31,
    pumpingRate: 74,
    backgroundRate: [33, 7],
    landUse: "Industrial 71% · port 20% · other 9%",
    buildings: 64,
    match: {
      cls: "permit-match",
      title: "Matches a permitted well field",
      text: "Permitted field 0.3 km away. The bowl is consistent with the permit; volume looks higher than the permitted amount.",
    },
    changes: [{ year: 2020.4, label: "Jun 2020 · slowed" }],
    rates: [88, 66],
  },
  {
    id: "SMG-2838",
    place: "Kaligawe",
    x: 586.2,
    y: 429.8,
    stability: 0.91,
    volume: { low: mk(47, 33, 62), mid: mk(89, 63, 117), high: mk(139, 98, 183) },
    background: 27,
    pumpingRate: 68,
    backgroundRate: [25, 6],
    landUse: "Residential 48% · industrial 39% · other 13%",
    buildings: 211,
    match: {
      cls: "no-permit",
      title: "No permit on record nearby",
      text: "Nearest permitted well field: 1.4 km. Mixed land use; inspect industrial lots first.",
    },
    changes: [{ year: 2017.6, label: "Aug 2017 · sped up" }],
    rates: [50, 72],
  },
  {
    id: "SMG-2055",
    place: "Sriwulan, Sayung",
    x: 841.5,
    y: 318.1,
    stability: 0.88,
    volume: { low: mk(39, 27, 52), mid: mk(69, 47, 92), high: mk(101, 69, 135) },
    background: 35,
    pumpingRate: 58,
    backgroundRate: [31, 8],
    landUse: "Fish ponds 46% · residential 38% · other 16%",
    buildings: 57,
    match: {
      cls: "no-permit",
      title: "No permit on record nearby",
      text: "Nearest permitted well field: 2.3 km. Part of the cell lost radar signal over ponds.",
    },
    changes: [{ year: 2022.1, label: "Feb 2022 · sped up" }],
    rates: [50, 72],
  },
  {
    id: "SMG-2408",
    place: "Tugu",
    x: 131.9,
    y: 377.7,
    stability: 0.84,
    volume: { low: mk(36, 24, 49), mid: mk(61, 41, 83), high: mk(88, 59, 120) },
    background: 29,
    pumpingRate: 52,
    backgroundRate: [22, 6],
    landUse: "Industrial 58% · residential 30% · other 12%",
    buildings: 73,
    match: {
      cls: "permit-near",
      title: "Permitted well field 0.8 km away",
      text: "Inside the 1 km match radius. Compare the permitted volume with this range.",
    },
    changes: [{ year: 2021.3, label: "Apr 2021 · sped up" }],
    rates: [38, 57],
  },
  {
    id: "SMG-3336",
    place: "Pedurungan",
    x: 559.6,
    y: 506.4,
    stability: 0.79,
    volume: { low: mk(30, 17, 44), mid: mk(58, 33, 84), high: mk(92, 52, 133) },
    background: 41,
    pumpingRate: 44,
    backgroundRate: [30, 9],
    landUse: "Residential 74% · commercial 18% · other 8%",
    buildings: 342,
    match: {
      cls: "no-permit",
      title: "No permit on record nearby",
      text: "Low stability: the source moves between reruns. Treat as a weak lead.",
    },
    changes: [{ year: 2017.4, label: "May 2017 · sped up" }],
    rates: [38, 52],
  },
  {
    id: "SMG-2619",
    place: "Semarang Barat",
    x: 299.8,
    y: 397.9,
    stability: 0.72,
    volume: { low: mk(27, 14, 40), mid: mk(48, 24, 71), high: mk(70, 35, 104) },
    background: 46,
    pumpingRate: 36,
    backgroundRate: [31, 9],
    landUse: "Residential 66% · industrial 21% · other 13%",
    buildings: 268,
    match: {
      cls: "no-permit",
      title: "No permit on record nearby",
      text: "Low stability: appears in 144 of 200 reruns. Treat as a weak lead.",
    },
    changes: [{ year: 2016.6, label: "Aug 2016 · sped up" }],
    rates: [30, 44],
  },
];

export const RUN = {
  id: "R-0007",
  area: "Semarang–Demak",
  period: "Jan 2015 – Oct 2026",
  status: "Published",
  gnssMisfit: 6.1,
  usablePixels: 91,
  footnote:
    "Sentinel-1 · ascending 127 + descending 76 · Jan 2015 – Oct 2026 · tied to GNSS station CSEM",
};

/** Hot spots ranked for a cone width: by volume, then stability. */
export function ranked(b: ConeWidth) {
  return [...HOT_SPOTS].sort(
    (a, c) => c.volume[b].v - a.volume[b].v || c.stability - a.stability,
  );
}

export function rankOf(id: string, b: ConeWidth) {
  return ranked(b).findIndex((h) => h.id === id) + 1;
}

export function total(b: ConeWidth) {
  return HOT_SPOTS.reduce((s, h) => s + h.volume[b].v, 0);
}

export const isLowStability = (h: HotSpot) => h.stability < 0.8;

/** Map canvas (1200×900) to lon/lat. Fitted to the two coordinates shown in the design. */
export function toLonLat(x: number, y: number) {
  const lon = 110.492 + (x - 640.4) * 0.000217;
  const lat = 6.954 + (y - 386.2) * 0.000265;
  return { lon, lat };
}

export const fmtK = (v: number) =>
  v >= 1000 ? `${(v / 1000).toFixed(3).replace(".", ",")}k` : `${Math.round(v)}k`;
