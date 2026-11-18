"use client";

import { ChevronLeft, Copy, FileText, Lock } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Badge, Button, TraceTags, cn } from "@/components/ui";
import { CONE_WIDTHS, HOT_SPOTS, rankOf, toLonLat, type HotSpot } from "@/data/run";
import { useStore } from "@/state";
import { HistoryChart } from "./HistoryChart";
import { PanelFooter } from "./Panel";

function Section({ title, codes, children }: { title: string; codes: string[]; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2 border-t border-line px-4 py-3">
      <div className="flex h-[18px] items-center gap-1.5 text-[13px] font-medium">
        <span>{title}</span>
        <span className="flex-1" />
        <TraceTags codes={codes} />
      </div>
      {children}
    </section>
  );
}

function KeyNumber({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="flex flex-col gap-0.5 whitespace-nowrap px-3 py-2.5 [&+&]:border-l [&+&]:border-line">
      <span className="text-xs leading-4 text-ink-3">{label}</span>
      <span className="text-2xl font-medium leading-7 tracking-[-0.01em]">{value}</span>
      <span className="text-xs leading-4 text-ink-2">{sub}</span>
    </div>
  );
}

export function Evidence() {
  const id = decodeURIComponent(usePathname().split("/")[2] ?? "");
  const h = HOT_SPOTS.find((x) => x.id === id);
  if (!h) {
    return (
      <div className="flex flex-col gap-2 p-4 text-ink-2">
        <span>No hot spot with cell ID {id}.</span>
        <Link href="/audit" className="font-medium text-primary">
          Back to the audit list
        </Link>
      </div>
    );
  }
  return <EvidenceFor key={h.id} h={h} />;
}

function EvidenceFor({ h }: { h: HotSpot }) {
  const { b } = useStore();
  const [copied, setCopied] = useState(false);
  const rank = rankOf(h.id, b);
  const { lon, lat } = toLonLat(h.x, h.y);
  const v = h.volume[b];
  const max = h.volume.high.hi * 1.07;
  const px = (k: number) => (k / max) * 160;

  return (
    <>
      <div className="flex flex-none flex-col gap-2.5 px-4 pb-3 pt-3.5">
        <div className="flex h-[18px] items-center gap-1.5">
          <Link href="/audit" className="flex items-center gap-1.5 text-xs font-medium text-ink-2 hover:text-ink">
            <ChevronLeft size={14} strokeWidth={2} />
            Audit list
          </Link>
          <span className="flex-1" />
          <TraceTags codes={["U3", "O3", "O4"]} />
        </div>

        <div className="flex h-[42px] gap-3">
          <span className="h-9 rounded-md bg-ink px-2.5 py-1 text-2xl font-medium leading-7 tracking-[-0.01em] text-on-primary">
            #{rank}
          </span>
          <span className="flex flex-col gap-0.5">
            <span className="font-mono text-lg font-medium leading-6 tracking-[-0.002em]">{h.id}</span>
            <span className="text-xs leading-4 text-ink-3">
              {h.place} · {lon.toFixed(3)} E, {lat.toFixed(3)} S · 500 m cell
            </span>
          </span>
        </div>

        <div className="grid grid-cols-[122px_122px_1fr] rounded-lg border border-line">
          <KeyNumber label={`Volume, ${CONE_WIDTHS.find((c) => c.key === b)!.label} B`} value={`${v.v}k`} sub="m³/yr, lower bound" />
          <KeyNumber label="Stability" value={h.stability.toFixed(2)} sub={`${Math.round(h.stability * 200)} of 200 reruns`} />
          <KeyNumber label="Background" value={`${h.background}%`} sub="of local sinking" />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto pb-[53px]">
        <Section title="Volume across cone widths" codes={["M6", "M7"]}>
          {CONE_WIDTHS.map((c) => {
            const x = h.volume[c.key];
            const on = c.key === b;
            return (
              <div key={c.key} className={cn("flex h-3.5 items-center gap-2.5 text-[11px] leading-[14px]", on ? "text-ink" : "text-ink-3")}>
                <span className="w-14">B {c.km.toFixed(1)} km</span>
                <span className="relative h-2.5 w-40">
                  <span className="absolute inset-x-0 top-1 h-0.5 bg-subtle" />
                  <span
                    className={cn("absolute top-0.5 h-1.5 rounded-[3.2px]", on ? "bg-pump/60" : "bg-line-strong")}
                    style={{ left: px(x.lo), width: px(x.hi - x.lo) }}
                  />
                  <span className={cn("absolute top-0 h-2.5 w-0.5", on ? "bg-ink" : "bg-ink-3")} style={{ left: px(x.v) }} />
                </span>
                <span className="flex-1" />
                <span className="whitespace-pre">
                  {x.v}k{"  "}
                  {x.lo}–{x.hi}
                </span>
              </div>
            );
          })}
          <p className="text-xs leading-4 text-ink-2">Lost storage per year, 90% ranges. A lower bound on water pumped.</p>
        </Section>

        <Section title="Displacement history · 5 nearest pixels" codes={["M4"]}>
          <HistoryChart h={h} />
        </Section>

        <Section title="What explains the sinking here" codes={["M5", "O4"]}>
          <div className="h-2.5 overflow-hidden rounded-[5px] bg-bg-share">
            <span className="block h-full bg-pump" style={{ width: `${100 - h.background}%` }} />
          </div>
          <div className="flex gap-4 whitespace-nowrap text-xs leading-4 text-ink-2">
            <span className="flex items-center gap-1.5">
              <i className="size-2 rounded-[2px] bg-pump" />
              Pumping {h.pumpingRate} mm/yr · {100 - h.background}%
            </span>
            <span className="flex items-center gap-1.5">
              <i className="size-2 rounded-[2px] bg-bg-share" />
              Background {h.backgroundRate[0]} ± {h.backgroundRate[1]} mm/yr · {h.background}%
            </span>
          </div>
        </Section>

        <Section title="Land use and permits" codes={["D8", "M9"]}>
          <div className="flex items-center gap-2 text-[13px] leading-[19px]">
            <span>{h.landUse}</span>
            <span className="flex-1" />
            <span className="text-[11px] leading-[14px] text-ink-3">{h.buildings} buildings</span>
          </div>
          <div className="flex flex-col gap-1.5 rounded-lg border border-line bg-bg px-3 py-2.5">
            <div className="flex h-[22px] items-center gap-2 text-[13px] font-medium">
              <span>{h.match.title}</span>
              <span className="flex-1" />
              <Badge tone="restricted" icon={<Lock size={13} strokeWidth={2} />}>
                Regulator only
              </Badge>
            </div>
            <p className="text-xs leading-4 text-ink-2">{h.match.text}</p>
          </div>
        </Section>
      </div>

      <PanelFooter>
        <Button
          icon={<Copy size={14} strokeWidth={1.9} />}
          onClick={() => {
            navigator.clipboard?.writeText(h.id);
            setCopied(true);
            setTimeout(() => setCopied(false), 1400);
          }}
        >
          {copied ? "Copied" : "Copy cell ID"}
        </Button>
        <span className="flex-1" />
        <Button variant="primary" icon={<FileText size={14} strokeWidth={1.9} />}>
          Export this hot spot
        </Button>
      </PanelFooter>
    </>
  );
}
