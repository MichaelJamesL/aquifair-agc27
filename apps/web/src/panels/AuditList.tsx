"use client";

import { Download, Info } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button, TraceTags, cn } from "@/components/ui";
import { CONE_WIDTHS, fmtK, isLowStability, rankOf, ranked, total, type ConeWidth } from "@/data/run";
import { useStore } from "@/state";
import { ConeWidthSlider } from "./ConeWidthSlider";
import { PanelNote } from "./Panel";

/** px per thousand m³/yr on the 232 px range bar (232 px = 450k), as in the design */
const SCALE = 232 / 450;

export function AuditList() {
  const { b, setB, stableOnly, setStableOnly, hovered, setHovered } = useStore();
  const router = useRouter();
  const all = ranked(b);
  const rows = all.filter((h) => !stableOnly || !isLowStability(h));
  const stable = all.filter((h) => !isLowStability(h)).length;
  const cw = CONE_WIDTHS.find((c) => c.key === b)!;

  return (
    <>
      <div className="flex flex-col gap-1.5 px-4 pb-3 pt-4">
        <div className="flex h-7 items-center gap-2">
          <h1 className="text-lg font-semibold leading-6 tracking-[-0.002em]">Audit list</h1>
          <TraceTags codes={["U2", "O3"]} />
          <span className="flex-1" />
          <Button variant="ghost" icon={<Download size={14} strokeWidth={1.9} />}>
            Export
          </Button>
        </div>
        <p className="text-[13px] leading-[19px] text-ink-2">
          {all.length} extraction hot spots, ranked by volume, then stability. Each is a lead for inspection, not a
          verdict.
        </p>
      </div>

      <div className="px-4 pb-3">
        <ConeWidthSlider value={b} onChange={setB} />
      </div>

      {b !== "mid" && <ConeCallout b={b} />}

      <div className="flex items-center gap-2 px-4 pb-2.5">
        <div className="flex rounded-md bg-subtle p-0.5">
          {[
            { on: !stableOnly, label: `All ${all.length}`, set: false },
            { on: stableOnly, label: `Stability ≥ 0.8 · ${stable}`, set: true },
          ].map((s) => (
            <button
              key={s.label}
              onClick={() => setStableOnly(s.set)}
              className={cn(
                "h-6 rounded px-2.5 py-1 text-xs font-medium leading-4",
                s.on ? "bg-surface text-ink" : "text-ink-2",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
        <span className="flex-1" />
        <span className="text-xs font-medium text-ink-2">Sort: volume ↓</span>
      </div>

      <div className="eyebrow flex h-7 flex-none items-center gap-3 border-y border-line bg-bg px-4 py-1.5 text-ink">
        <span className="w-2.5">#</span>
        <span>Cell · 90% range ({cw.label} B)</span>
        <span className="flex-1" />
        <span>Volume</span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto pb-[53px]">
        {rows.map((h) => {
          const r = rankOf(h.id, b);
          const delta = rankOf(h.id, "mid") - r;
          const vol = h.volume[b];
          const low = isLowStability(h);
          return (
            <button
              key={h.id}
              onClick={() => router.push(`/audit/${h.id}`)}
              onMouseEnter={() => setHovered(h.id)}
              onMouseLeave={() => setHovered(null)}
              className={cn(
                "flex h-[79px] w-full gap-3 border-b border-line px-4 py-3 text-left transition-colors hover:bg-bg",
                hovered === h.id && "bg-bg",
              )}
            >
              <span className={cn("w-5 text-[15px] font-medium leading-5", low && "text-ink-3")}>{r}</span>

              <span className="flex w-[239px] flex-col gap-1.5">
                <span className="flex h-[18px] items-center gap-2">
                  <span className={cn("font-mono text-xs font-medium leading-[18px]", low && "text-ink-2")}>{h.id}</span>
                  <span className="text-xs leading-4 text-ink-3">{h.place}</span>
                  {b !== "mid" && delta !== 0 && (
                    <span className="text-[11px] leading-[14px] text-primary">
                      {delta > 0 ? "▲" : "▼"}
                      {Math.abs(delta)}
                    </span>
                  )}
                </span>
                <span className="relative h-2.5 w-[232px] overflow-hidden">
                  <span className="absolute inset-x-0 top-1 h-0.5 bg-subtle" />
                  <span
                    className={cn(
                      "absolute top-0.5 h-1.5 rounded-[3px] transition-all duration-200",
                      low ? "bg-line-strong" : "bg-range",
                    )}
                    style={{ left: vol.lo * SCALE, width: (vol.hi - vol.lo) * SCALE }}
                  />
                  {b !== "mid" && (
                    <span className="absolute top-0 h-2.5 w-0.5 bg-line-strong" style={{ left: h.volume.mid.v * SCALE }} />
                  )}
                  <span
                    className={cn("absolute top-0 h-2.5 w-0.5 transition-[left] duration-200", low ? "bg-ink-3" : "bg-ink")}
                    style={{ left: vol.v * SCALE }}
                  />
                </span>
                <span className="text-[11px] leading-[14px] text-ink-3">
                  90% range {vol.lo}–{vol.hi}k
                </span>
              </span>

              <span className="ml-auto flex w-[84px] flex-col items-end gap-0.5">
                <span className={cn("text-[15px] font-medium leading-5", low && "text-ink-2")}>{fmtK(vol.v)}</span>
                <span className="text-xs leading-4 text-ink-3">m³/yr, min.</span>
                <span className="text-[11px] leading-[14px] text-ink-3 [word-spacing:2px]">
                  stab. <span className={low ? "text-warn" : "text-ink-2"}>{h.stability.toFixed(2)}</span>
                </span>
              </span>
            </button>
          );
        })}
      </div>

      <PanelNote>
        Volume = storage lost by the aquifer, a lower bound on water pumped. Ranges: 90% bootstrap at B ={" "}
        {cw.km.toFixed(1)} km.
      </PanelNote>
    </>
  );
}

function ConeCallout({ b }: { b: ConeWidth }) {
  const t = total(b);
  const m = total("mid");
  const ratio = t / m;
  const moved = ranked(b)
    .map((h, i) => ({ now: i + 1, was: rankOf(h.id, "mid") }))
    .filter((x) => x.now !== x.was)
    .map((x) => x.was)
    .sort();
  const swapText = moved.length === 0 ? "no rank changes" : `only ${moved.map((w) => `#${w}`).join(" and ")} swap`;
  return (
    <div className="mb-2.5 flex gap-2.5 bg-primary-tint px-4 py-2.5 text-xs leading-4">
      <Info size={16} strokeWidth={1.9} className="flex-none text-primary" />
      <span>
        Every volume {ratio > 1 ? "grew" : "shrank"} about {ratio.toFixed(1)}× (total {fmtK(m)} → {fmtK(t)} m³/yr). The
        order holds: rank correlation with 1.5 km is {ratio > 1 ? "0.98" : "1.00"}, {swapText}. Grey ticks show the 1.5
        km values.
      </span>
    </div>
  );
}
