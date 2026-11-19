"use client";

import { Check, ChevronDown, ShieldCheck, Satellite, ArrowRight, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge, Button, TraceTags, cn } from "@/components/ui";
import { HOT_SPOTS, rankOf } from "@/data/run";
import { useT } from "@/i18n";
import { MapThumb } from "@/map/MapThumb";
import { Marker } from "@/map/Marker";
import { useStore } from "@/state";

// framing of the compare map card (760 × 667), from the Figma frame
const S = 0.914;
const TX = -57.5;
const TY = -158;
const at = (x: number, y: number) => ({ x: x * S + TX, y: y * S + TY });

type Kind = "changed" | "appeared" | "vanished";

const CHANGES: {
  id: string;
  kind: Kind;
  rank: string;
  place: string;
  text: string;
  before: [number, number] | null;
  after: [number, number] | null;
  dir?: "up" | "down";
  /** canvas position for a source that only exists in R-0008 */
  x?: number;
  y?: number;
}[] = [
  { id: "SMG-2838", kind: "changed", rank: "#4", place: "Kaligawe", text: "Ranges no longer overlap. Sinking sped up from Aug 2026.", before: [63, 117], after: [128, 171], dir: "up" },
  { id: "SMG-2055", kind: "changed", rank: "#5", place: "Sriwulan, Sayung", text: "Ranges no longer overlap. Slowed from Mar 2026.", before: [47, 92], after: [12, 38], dir: "down" },
  { id: "SMG-3047", kind: "appeared", rank: "new", place: "Muktiharjo", text: "Stability 0.83 in the new run.", before: null, after: [41, 79], x: 691, y: 477 },
  { id: "SMG-2619", kind: "vanished", rank: "#8", place: "Semarang Barat", text: "Now below the 20k reporting floor. Was low stability (0.72).", before: [24, 71], after: null },
];

const LABEL: Record<string, { text: string; dx: number; dy: number; tone: string }> = {
  "SMG-2838": { text: "changed ↑", dx: 16, dy: -28, tone: "bg-warn-tint text-warn" },
  "SMG-2055": { text: "changed ↓", dx: -92, dy: -26, tone: "bg-warn-tint text-warn" },
  "SMG-2619": { text: "gone", dx: 16, dy: -28, tone: "bg-subtle text-ink-2" },
  "SMG-3047": { text: "new", dx: 14, dy: -28, tone: "bg-pass-tint text-pass" },
};

/** the range bar spans 0 to 192k m³/yr (212 px in the design) */
const MAXK = 192;

/** 13 · Compare runs (U6, S6) */
export function CompareScreen() {
  const { r8Published } = useStore();
  const { pick } = useT();
  const router = useRouter();
  const [hot, setHot] = useState<string | null>(null);
  const counts = { changed: 2, appeared: 1, vanished: 1, unchanged: 5 };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-6 pb-6 pt-6">
      <div className="flex items-start gap-6">
        <div className="flex flex-1 flex-col gap-2">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">{pick("Compare runs", "Bandingkan run")}</h1>
            <TraceTags codes={["U6", "S6"]} />
          </div>
          <p className="text-[13px] leading-[19px] text-ink-2">
            Runs are never overwritten. A rerun with new images is a new run, so the two can be read side by side.
          </p>
        </div>
        <div className="flex items-start gap-[20px]">
        <RunPick id="R-0007" meta="Jan 2015 – Oct 2026 · 412 images" badge={<Badge tone="pass">Published</Badge>} />
        <ArrowRight size={16} strokeWidth={1.8} className="-mr-1.5 mt-4 text-ink-3" />
        <RunPick
          id="R-0008"
          meta="Jan 2015 – Nov 2026 · 426 images"
          badge={r8Published ? <Badge tone="pass">Published</Badge> : <Badge tone="neutral">Private</Badge>}
        />
        </div>
      </div>

      <div className="flex h-[42px] items-center gap-3 rounded-lg bg-primary-tint pl-4 pr-2">
        <Satellite size={16} strokeWidth={1.8} className="text-primary" />
        <span className="flex-1 text-[13px] leading-[19px]">
          14 new Sentinel-1C and 1D images since R-0007. The pipeline checks for images every week and proposes a rerun
          every month.
        </span>
        <Button icon={<ShieldCheck size={14} strokeWidth={1.9} />} onClick={() => router.push("/validation")}>
          Open R-0008 validation
        </Button>
      </div>

      <div className="flex min-h-[667px] gap-5">
        {/* map */}
        <div className="relative h-[667px] max-w-[1000px] flex-[760_1_0] overflow-hidden rounded-[10px] border border-line">
          <MapThumb width="100%" height={667} dots={false} s={S} tx={TX} ty={TY} rounded={false} className="absolute inset-0" />
          {HOT_SPOTS.map((h) => {
            const p = at(h.x, h.y);
            const r = rankOf(h.id, "mid");
            const gone = h.id === "SMG-2619";
            return (
              <div key={h.id}>
                <Marker
                  rank={r}
                  x={p.x}
                  y={p.y}
                  animate={false}
                  state={hot === h.id ? "selected" : gone ? "muted" : h.stability < 0.8 ? "low" : "default"}
                  label={`#${r} ${h.id} · ${h.place}`}
                  onHover={(on) => setHot(on ? h.id : null)}
                  onClick={() => router.push(`/audit/${h.id}`)}
                />
                {LABEL[h.id] && <Tag id={h.id} x={p.x} y={p.y} />}
              </div>
            );
          })}
          {(() => {
            const n = CHANGES.find((c) => c.kind === "appeared")!;
            const p = at(n.x!, n.y!);
            return (
              <>
                <span
                  onMouseEnter={() => setHot(n.id)}
                  onMouseLeave={() => setHot(null)}
                  title={`${n.id} · ${n.place}`}
                  className={cn(
                    "absolute grid size-[26px] place-items-center rounded-full text-pass shadow-[inset_0_0_0_2px_var(--color-pass)]",
                    hot === n.id ? "bg-pass text-white" : "bg-pass-tint",
                  )}
                  style={{ left: p.x - 13, top: p.y - 13 }}
                >
                  <Plus size={15} strokeWidth={2.2} />
                </span>
                <Tag id={n.id} x={p.x} y={p.y} />
              </>
            );
          })()}
          <div className="absolute bottom-4 left-4 flex h-8 items-center gap-4 rounded-md border border-line bg-white px-3 text-[13px] text-ink-2">
            <span className="flex items-center gap-1.5">
              <i className="size-2 rounded-full bg-warn" />
              Changed: ranges no longer overlap
            </span>
            <span className="flex items-center gap-1.5">
              <i className="size-2 rounded-full bg-pass" />
              Appeared
            </span>
            <span className="flex items-center gap-1.5">
              <i className="size-2 rounded-full bg-ink-3" />
              Vanished
            </span>
          </div>
        </div>

        {/* summary */}
        <div className="flex min-w-[520px] flex-[612_1_0] flex-col gap-4">
          <div className="grid grid-cols-4 gap-2.5">
            {(
              [
                [counts.changed, "Changed", "text-warn"],
                [counts.appeared, "Appeared", "text-pass"],
                [counts.vanished, "Vanished", "text-ink"],
                [counts.unchanged, "Unchanged", "text-ink"],
              ] as const
            ).map(([n, l, c]) => (
              <div key={l} className="flex h-[67px] flex-col justify-center gap-0.5 rounded-lg border border-line bg-surface px-3">
                <span className={cn("text-2xl font-medium leading-7", c)}>{n}</span>
                <span className="text-[13px] text-ink-2">{l}</span>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-lg border border-line bg-surface">
            {CHANGES.map((c) => (
              <button
                key={c.id}
                onMouseEnter={() => setHot(c.id)}
                onMouseLeave={() => setHot(null)}
                onClick={() => c.kind !== "appeared" && router.push(`/audit/${c.id}`)}
                className={cn(
                  "flex w-full items-start gap-3 border-b border-line px-3.5 py-3.5 text-left last:border-b-0",
                  hot === c.id && "bg-bg",
                )}
              >
                <span className="flex w-[245px] flex-none flex-col gap-1">
                  <span className="flex items-center gap-1.5 text-xs">
                    <span className="font-mono font-medium">
                      {c.rank} · {c.id}
                    </span>
                    <span className="text-ink-3">{c.place}</span>
                  </span>
                  <span className="text-[13px] leading-4 text-ink-2">{c.text}</span>
                </span>
                <span className="flex flex-1 flex-col gap-1.5 pt-0.5">
                  <RangeRow run="R-0007" r={c.before} tone="bg-[#c9bfae]" />
                  <RangeRow run="R-0008" r={c.after} tone={c.kind === "appeared" ? "bg-pass" : "bg-warn"} />
                </span>
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-3 rounded-lg border border-line bg-surface px-3.5 py-3.5">
            <div className="flex items-center">
              <span className="text-[13px] font-medium">Drift checks</span>
              <span className="flex-1" />
              <Badge tone="pass">No alert</Badge>
            </div>
            {[
              ["Residual spread", "3.9 mm/yr", "usual band 3.2–4.6"],
              ["Difference from GNSS", "6.4 mm/yr", "usual band 4–8"],
            ].map(([k, v, band]) => (
              <div key={k} className="flex items-center gap-2 text-[13px]">
                <Check size={15} strokeWidth={2.2} className="text-pass" />
                <span>{k}</span>
                <span className="flex-1" />
                <span className="text-[11px]">{v}</span>
                <span className="w-[100px] text-right text-[11px] text-ink-3">{band}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Tag({ id, x, y }: { id: string; x: number; y: number }) {
  const l = LABEL[id];
  return (
    <span
      className={cn("pointer-events-none absolute h-5 whitespace-nowrap rounded px-1.5 text-xs leading-5", l.tone)}
      style={{ left: x + l.dx, top: y + l.dy }}
    >
      {l.text}
    </span>
  );
}

function RangeRow({ run, r, tone }: { run: string; r: [number, number] | null; tone: string }) {
  return (
    <span className="flex h-3.5 items-center gap-2.5 text-[11px] leading-[14px] text-ink-3">
      <span className="w-11">{run}</span>
      <span className="relative h-2 flex-1">
        <span className="absolute inset-x-0 top-[3.5px] h-px bg-line" />
        {r && (
          <span
            className={cn("absolute top-0.5 h-1.5 rounded-[3px]", tone)}
            style={{ left: `${(r[0] / MAXK) * 100}%`, width: `${((r[1] - r[0]) / MAXK) * 100}%` }}
          />
        )}
      </span>
      <span className="w-14 text-right text-ink-2">{r ? `${r[0]}–${r[1]}k` : "not found"}</span>
    </span>
  );
}

function RunPick({ id, meta, badge }: { id: string; meta: string; badge: React.ReactNode }) {
  return (
    <div className="flex h-12 w-[316px] flex-none items-center gap-2 rounded-md border border-line-strong bg-surface px-3">
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="text-[13px] font-medium leading-4">{id}</span>
        <span className="whitespace-nowrap text-[11px] leading-[14px] text-ink-3">{meta}</span>
      </span>
      {badge}
      <ChevronDown size={16} strokeWidth={1.75} className="text-ink-2" />
    </div>
  );
}
