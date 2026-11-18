import type { HotSpot } from "@/data/run";

// Plot geometry from the Figma chart: 368×134 box, plot area x 34–368, y 2–104.
const X0 = 34;
const X1 = 368;
const Y0 = 2; // 0 mm
const PX_PER_MM = 87 / 1200;
const T0 = 2015;
const T1 = 2026.8;
const xOf = (t: number) => X0 + ((t - T0) / (T1 - T0)) * (X1 - X0);
const yOf = (mm: number) => Y0 + -mm * PX_PER_MM;

/** Cumulative displacement (mm, negative = down) for a piecewise-constant rate. */
function series(h: HotSpot, scale: number, seed: number) {
  const breaks = [T0, ...h.changes.map((c) => c.year), T1];
  let rnd = seed;
  const noise = () => {
    rnd = (rnd * 16807) % 2147483647;
    return rnd / 2147483647 - 0.5;
  };
  const pts: string[] = [];
  let z = 0;
  const step = 1 / 12;
  for (let t = T0, i = 0; t <= T1 + 1e-6; t += step, i++) {
    const seg = Math.max(0, breaks.findIndex((b, k) => t >= b && t < (breaks[k + 1] ?? Infinity)));
    const rate = (h.rates[Math.min(seg, h.rates.length - 1)] ?? h.rates[0]) * scale;
    const season = Math.sin((t - T0) * 2 * Math.PI) * 6;
    pts.push(`${i ? "L" : "M"}${xOf(t).toFixed(1)} ${yOf(z + season + noise() * 14).toFixed(1)}`);
    z -= rate * step;
  }
  return pts.join("");
}

const TICK = "fill-ink-3 font-mono text-[10px]";

export function HistoryChart({ h }: { h: HotSpot }) {
  const last = h.changes[h.changes.length - 1];
  return (
    <svg width="368" height="134" viewBox="0 0 368 134" role="img" aria-label={`Displacement history for ${h.id}`} className="block overflow-visible">
      {h.changes.length > 1 && (
        <rect x={xOf(last.year - 1.5)} y={0} width={xOf(last.year + 0.9) - xOf(last.year - 1.5)} height={104} fill="#edeae3" />
      )}
      {[0, -400, -800, -1200].map((v) => (
        <g key={v}>
          <line x1={X0} x2={X1} y1={yOf(v)} y2={yOf(v)} stroke="#e4e0d6" />
          <text x={0} y={yOf(v) + 4} className={TICK}>
            {v === 0 ? "0" : `−${-v}`}
          </text>
        </g>
      ))}
      {[0.9, 0.94, 1.06, 1.1].map((k, i) => (
        <path key={i} d={series(h, k, 11 + i * 7)} fill="none" stroke="rgba(195,76,48,0.28)" strokeWidth="1" />
      ))}
      <path d={series(h, 1, 3)} fill="none" stroke="#17191c" strokeWidth="1.4" />
      {h.changes.map((c, i) => (
        <g key={c.label}>
          <line x1={xOf(c.year)} x2={xOf(c.year)} y1={0} y2={104} stroke="#0f4c5c" strokeWidth="1.2" strokeDasharray="3 3" />
          <foreignObject x={xOf(c.year) + (i % 2 === 0 ? 4 : -114)} y={i % 2 === 0 ? 82 : 2} width="116" height="16">
            <span className="inline-block whitespace-nowrap rounded-sm bg-white px-1 py-px font-mono text-[10px] leading-[14px] text-primary">
              {c.label}
            </span>
          </foreignObject>
        </g>
      ))}
      {[2015, 2018, 2021, 2024].map((t) => (
        <text key={t} x={xOf(t)} y={127} textAnchor="middle" className={TICK}>
          {t}
        </text>
      ))}
    </svg>
  );
}
