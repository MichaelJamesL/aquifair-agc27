// Demo data for the run pages (Figma screens 03–05b). Replace with GET /runs and
// GET /runs/{id} once the run service (S5) exists.

export type AreaKey = "semarang-demak" | "pekalongan" | "jakarta";

export type Area = {
  key: AreaKey;
  name: string;
  config: string;
  configured: boolean;
  period: [string, string];
};

export const AREAS: Area[] = [
  { key: "semarang-demak", name: "Semarang–Demak", config: "semarang-demak.yaml", configured: true, period: ["Jan 2015", "Oct 2026"] },
  { key: "pekalongan", name: "Pekalongan", config: "pekalongan.yaml", configured: true, period: ["Jan 2018", "Oct 2026"] },
  { key: "jakarta", name: "Jakarta", config: "not configured", configured: false, period: ["Jan 2015", "Oct 2026"] },
];

export type RunStatus = "published" | "superseded" | "running" | "stopped";

export type Run = {
  id: string;
  area: AreaKey;
  period: string;
  images: number;
  hotSpots: number | null;
  signedOff: string | null;
  status: RunStatus;
  /** private and failed runs are visible to analysts only */
  private: boolean;
};

export const RUNS: Run[] = [
  { id: "R-0009", area: "semarang-demak", period: "Jan 2015 – Nov 2026", images: 426, hotSpots: null, signedOff: null, status: "stopped", private: true },
  { id: "R-0008", area: "semarang-demak", period: "Jan 2015 – Nov 2026", images: 426, hotSpots: null, signedOff: null, status: "running", private: true },
  { id: "R-0007", area: "semarang-demak", period: "Jan 2015 – Oct 2026", images: 412, hotSpots: 8, signedOff: "A. Wibowo · 3 Nov", status: "published", private: false },
  { id: "R-0005", area: "semarang-demak", period: "Jan 2015 – Apr 2026", images: 384, hotSpots: 8, signedOff: "A. Wibowo · 6 May", status: "superseded", private: false },
  { id: "R-0003", area: "semarang-demak", period: "Jan 2015 – Dec 2025", images: 368, hotSpots: 7, signedOff: "R. Hartono · 9 Jan", status: "superseded", private: false },
];

export const STATUS_LABEL: Record<RunStatus, string> = {
  published: "Published",
  superseded: "Superseded",
  running: "Running",
  stopped: "Stopped",
};

/** Details shown in the right-hand preview on the Runs screen. */
export const RUN_DETAILS: Record<string, { label: string; value: string; warn?: boolean }[]> = {
  "R-0007": [
    { label: "Period", value: "Jan 2015 – Oct 2026" },
    { label: "Images", value: "412, two directions" },
    { label: "Hot spots", value: "8 · 6 with stability ≥ 0.8" },
    { label: "Signed off", value: "A. Wibowo, BIG · 3 Nov 2026" },
    { label: "Checked against wells", value: "Not yet (V5, V6 waiting for D6)", warn: true },
  ],
  "R-0005": [
    { label: "Period", value: "Jan 2015 – Apr 2026" },
    { label: "Images", value: "384, two directions" },
    { label: "Hot spots", value: "8 · 6 with stability ≥ 0.8" },
    { label: "Signed off", value: "A. Wibowo, BIG · 6 May 2026" },
    { label: "Superseded by", value: "R-0007" },
  ],
  "R-0003": [
    { label: "Period", value: "Jan 2015 – Dec 2025" },
    { label: "Images", value: "368, two directions" },
    { label: "Hot spots", value: "7 · 5 with stability ≥ 0.8" },
    { label: "Signed off", value: "R. Hartono, BIG · 9 Jan 2026" },
    { label: "Superseded by", value: "R-0005" },
  ],
  "R-0008": [
    { label: "Period", value: "Jan 2015 – Nov 2026" },
    { label: "Images", value: "426, two directions" },
    { label: "Stage", value: "M4 of M9 · time-series separation" },
    { label: "Visible to", value: "Analysts only until Gate 3" },
  ],
  "R-0009": [
    { label: "Period", value: "Jan 2015 – Nov 2026" },
    { label: "Images", value: "426, two directions" },
    { label: "Stopped at", value: "Gate 2 · V3 precision 71% < 80%", warn: true },
    { label: "Visible to", value: "Analysts only, kept for comparison" },
  ],
};

/* ---------- pipeline stages (screens 05, 05b) ---------- */

export type StageState = "done" | "running" | "queued" | "waiting" | "failed" | "skipped" | "later";

export type Stage = {
  code: string;
  name: string;
  gate?: boolean;
  /** detail text while queued, and once done */
  queued: string;
  done: string;
  /** time taken, shown once done */
  time: string;
};

export const STAGES: Stage[] = [
  { code: "S1", name: "Ingest", queued: "finds radar pairs, atmosphere, GNSS", done: "426 scenes, 1,246 pairs, hashes recorded", time: "16 min" },
  { code: "M1", name: "Radar time series", queued: "LiCSBAS 076D + MintPy 127", done: "LiCSBAS 076D + MintPy 127", time: "2 h 21 min" },
  { code: "M2", name: "Quality control and referencing", queued: "loop closure, tie to CSEM", done: "34 pairs dropped, tied to CSEM", time: "18 min" },
  { code: "Gate 1", name: "Radar quality", gate: true, queued: "V1, V2", done: "V1 6.1 mm/yr · V2 2.7%", time: "passed" },
  { code: "M3", name: "Vertical and east–west", queued: "two directions combined", done: "two cubes written", time: "4 min" },
  { code: "M4", name: "Time-series separation", queued: "ICA, change points", done: "5 components", time: "23 min" },
  { code: "M5", name: "Background model", queued: "quiet pixels only", done: "quiet pixels only", time: "6 min" },
  { code: "M6", name: "Sparse inversion", queued: "for B = 1.0, 1.5, 2.0 km", done: "3 cone widths", time: "3 min" },
  { code: "M7", name: "Uncertainty", queued: "200 block resamples", done: "200 block resamples", time: "11 min" },
  { code: "Gate 2", name: "Inversion quality", gate: true, queued: "V3, V4", done: "V3 recall 88% · precision 84%", time: "passed" },
  { code: "M8", name: "Volume to extraction", queued: "lower bound", done: "8 hot spots, 3 cone widths", time: "2 min" },
  { code: "M9", name: "Attribution and report", queued: "land use, permits", done: "audit list and sheet written", time: "5 min" },
  { code: "Gate 3", name: "Sign-off", gate: true, queued: "named analyst", done: "named analyst", time: "later" },
];

/** progress (0–100) after each stage index has finished, for the progress bar */
export const STAGE_PROGRESS = [6, 26, 32, 33, 38, 52, 58, 64, 78, 82, 90, 98, 100];

export type LogLine = { t: string; tag: string; msg: string; ok?: boolean };

export const R0008_LOG: LogLine[] = [
  { t: "10:42:03", tag: "ingest", msg: "426 scenes: S1A, S1C, S1D" },
  { t: "10:58:41", tag: "ingest", msg: "hashes written d1:5c0a…" },
  { t: "11:02:10", tag: "insar", msg: "076D frame · 1,246 pairs" },
  { t: "12:47:30", tag: "insar", msg: "S1A to S1C/1D hand-over: one network, no jump" },
  { t: "13:21:55", tag: "qc", msg: "loop closure: 34 of 1,246 dropped" },
  { t: "13:22:02", tag: "gate1", msg: "V1 6.1 ≤ 8 · V2 2.7% < 5% · pass", ok: true },
  { t: "13:26:40", tag: "decomp", msg: "vertical, east–west cubes" },
  { t: "13:31:12", tag: "separate", msg: "ICA 5 components" },
  { t: "13:54:20", tag: "separate", msg: "change points 62%" },
];

/** log lines written when each stage of the demo run finishes */
export const STAGE_LOG: Record<string, LogLine[]> = {
  S1: R0008_LOG.slice(0, 2),
  M1: R0008_LOG.slice(2, 4),
  M2: R0008_LOG.slice(4, 5),
  "Gate 1": R0008_LOG.slice(5, 6),
  M3: R0008_LOG.slice(6, 7),
  M4: [...R0008_LOG.slice(7, 9), { t: "13:57:02", tag: "separate", msg: "change points done · 5 components kept" }],
  M5: [{ t: "14:03:15", tag: "background", msg: "quiet pixels 41% · median 21 mm/yr" }],
  M6: [{ t: "14:06:30", tag: "invert", msg: "B 1.0 / 1.5 / 2.0 km · 8 sources each" }],
  M7: [{ t: "14:17:44", tag: "bootstrap", msg: "200 resamples · 6 of 8 stable ≥ 0.8" }],
  "Gate 2": [{ t: "14:18:01", tag: "gate2", msg: "V3 recall 88% · precision 84% · pass", ok: true }],
  M8: [{ t: "14:20:12", tag: "volume", msg: "total 921k m³/yr at B 1.5 km" }],
  M9: [{ t: "14:25:40", tag: "report", msg: "audit list and sheet written · waiting for sign-off" }],
};

export const RUN_IDENTITY = ["commit a3f9c21", "config 7e1b42c9", "data d1:5c0a · d3:0b6e · d4:91be"];

/* ---------- start-a-run form (screen 04) ---------- */

export const DATA_INPUTS: { code: string; name: string; status: "Open" | "Optional" | "Received" | "Not received" | "Partial" }[] = [
  { code: "D1", name: "Sentinel-1 radar", status: "Open" },
  { code: "D2", name: "NISAR L-band", status: "Optional" },
  { code: "D3", name: "GACOS atmosphere", status: "Open" },
  { code: "D4", name: "InaCORS GNSS (BIG)", status: "Received" },
  { code: "D5", name: "DEMNAS elevation", status: "Open" },
  { code: "D6", name: "Well records and permits", status: "Not received" },
  { code: "D7", name: "Geology, clay thickness", status: "Partial" },
  { code: "D8", name: "Buildings and land use", status: "Open" },
  { code: "D9", name: "Rainfall and tides", status: "Open" },
];

export const PIPELINE_STEPS: { title: string; text: string; gate?: boolean }[] = [
  { title: "S1 Ingest", text: "Finds and downloads radar pairs, atmosphere maps, GNSS series. Records versions and hashes." },
  { title: "S2 Radar processor · M1–M2", text: "Time series, quality control, tie to CSEM." },
  { title: "Gate 1", text: "V1 radar vs GNSS, V2 loop closure. Stops if either fails.", gate: true },
  { title: "S4 Model service · M3–M8", text: "Vertical and east–west, separation, background, inversion for three cone widths, bootstrap." },
  { title: "Gate 2", text: "V3 benchmark at this run’s noise, V4 out-of-sample fit.", gate: true },
  { title: "M9 Attribution, report", text: "Land use, permits, audit list and sheet." },
  { title: "Gate 3", text: "Private until a named analyst signs off.", gate: true },
];

/** Run list after an analyst signs off R-0008 in this session: it becomes the published run. */
export function runsFor(r8Published: boolean): Run[] {
  if (!r8Published) return RUNS;
  return RUNS.map((r) =>
    r.id === "R-0008"
      ? { ...r, status: "published", hotSpots: 8, signedOff: "A. Wibowo · 19 Nov", private: false }
      : r.id === "R-0007"
        ? { ...r, status: "superseded" }
        : r,
  );
}

export function detailsFor(id: string, r8Published: boolean) {
  if (r8Published && id === "R-0008")
    return [
      { label: "Period", value: "Jan 2015 – Nov 2026" },
      { label: "Images", value: "426, two directions" },
      { label: "Hot spots", value: "8 · 2 changed, 1 new, 1 gone" },
      { label: "Signed off", value: "A. Wibowo, BIG · 19 Nov 2026" },
      { label: "Checked against wells", value: "Not yet (V5, V6 waiting for D6)", warn: true },
    ];
  if (r8Published && id === "R-0007")
    return [...RUN_DETAILS["R-0007"].filter((d) => d.label !== "Checked against wells"), { label: "Superseded by", value: "R-0008" }];
  return RUN_DETAILS[id] ?? [];
}
