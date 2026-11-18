// Reads values back from the rendered raster layers so the hover tooltip shows what is under
// the cursor. The rasters are colour-mapped images, so values are inverted from their ramps.
// With a real backend this becomes a point query (GET /audits/{id}/pixel?lon=&lat=).
import { LAYERS, VERTICAL_STOPS } from "@/data/layers";

type Px = [number, number, number, number];

const canvases: Partial<Record<string, CanvasRenderingContext2D>> = {};
let ready: Promise<void> | null = null;

export function loadRasters() {
  if (ready) return ready;
  ready = Promise.all(
    LAYERS.map(
      (l) =>
        new Promise<void>((res) => {
          const img = new Image();
          img.onload = () => {
            const c = document.createElement("canvas");
            c.width = 1200;
            c.height = 900;
            const ctx = c.getContext("2d", { willReadFrequently: true })!;
            ctx.drawImage(img, 0, 0, 1200, 900);
            canvases[l.key] = ctx;
            res();
          };
          img.onerror = () => res();
          img.src = l.src;
        }),
    ),
  ).then(() => undefined);
  return ready;
}

function px(key: string, x: number, y: number): Px | null {
  const ctx = canvases[key];
  if (!ctx || x < 0 || y < 0 || x >= 1200 || y >= 900) return null;
  const d = ctx.getImageData(Math.floor(x), Math.floor(y), 1, 1).data;
  return [d[0], d[1], d[2], d[3]];
}

const hexRgb = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));

// 256-step lookup table of the vertical-velocity ramp
const RAMP = (() => {
  const stops = VERTICAL_STOPS.map((s) => {
    const [c, p] = s.split(" ");
    return { rgb: hexRgb(c), t: parseFloat(p) / 100 };
  });
  const lut: { rgb: number[]; t: number }[] = [];
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    let k = 0;
    while (k < stops.length - 2 && t > stops[k + 1].t) k++;
    const a = stops[k];
    const b = stops[k + 1];
    const f = (t - a.t) / (b.t - a.t);
    lut.push({ rgb: a.rgb.map((v, j) => v + (b.rgb[j] - v) * f), t });
  }
  return lut;
})();

// ramp position → mm/yr, following the tick positions on the legend
const TICKS: [number, number][] = [
  [0.02, 0],
  [0.19, 35],
  [0.37, 60],
  [0.55, 85],
  [0.73, 110],
  [0.95, 140],
  [1.0, 150],
];

function tToValue(t: number) {
  for (let i = 0; i < TICKS.length - 1; i++) {
    const [t0, v0] = TICKS[i];
    const [t1, v1] = TICKS[i + 1];
    if (t <= t1) return Math.max(0, v0 + ((t - t0) / (t1 - t0)) * (v1 - v0));
  }
  return 150;
}

const CHANGE_COLORS: [string, string][] = [
  ["#8f2d56", "2016, sped up"],
  ["#3e1f47", "2017, sped up"],
  ["#5e8c62", "Mar 2018, sped up"],
  ["#e0a558", "Oct 2019, sped up"],
  ["#3d5a80", "Jun 2020, slowed"],
  ["#98b06e", "Apr 2021, sped up"],
  ["#c8553d", "Feb 2022, sped up"],
];

export type PixelInfo =
  | { kind: "sea" }
  | { kind: "gap" }
  | {
      kind: "pixel";
      vertical: number;
      eastwest: number;
      seasonal: number;
      sigma: number;
      change: string;
    };

export function samplePixel(x: number, y: number): PixelInfo | null {
  const u = px("uncertainty", x, y);
  if (!u) return null;
  if (u[3] < 40) return { kind: "sea" };
  if (u[2] - u[0] < 8) return { kind: "gap" };

  const v = px("vertical", x, y)!;
  let best = 0;
  let bd = Infinity;
  RAMP.forEach((e, i) => {
    const d = (e.rgb[0] - v[0]) ** 2 + (e.rgb[1] - v[1]) ** 2 + (e.rgb[2] - v[2]) ** 2;
    if (d < bd) {
      bd = d;
      best = i;
    }
  });
  const vertical = Math.round(tToValue(RAMP[best].t));

  const e = px("eastwest", x, y)!;
  const eastwest = Math.round((e[0] - e[2]) / 6);

  const s = px("seasonal", x, y)!;
  const seasonal = Math.max(1, Math.round(((234 - s[1]) / 83) * 15));

  const sigma = Math.max(1, Math.round(((228 - u[1]) / 85) * 9));

  const c = px("changes", x, y)!;
  let change = "No clear change";
  if (c[3] > 120 && !(c[0] > 235 && c[1] > 235)) {
    let cd = Infinity;
    for (const [hex, label] of CHANGE_COLORS) {
      const rgb = hexRgb(hex);
      const d = (rgb[0] - c[0]) ** 2 + (rgb[1] - c[1]) ** 2 + (rgb[2] - c[2]) ** 2;
      if (d < cd) {
        cd = d;
        change = label;
      }
    }
  }
  return { kind: "pixel", vertical, eastwest, seasonal, sigma, change };
}
