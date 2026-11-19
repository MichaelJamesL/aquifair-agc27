"use client";

import { Clock, Info, MapPin } from "lucide-react";
import { cn } from "@/components/ui";
import { AREAS, runsFor } from "@/data/runs";
import { useStore } from "@/state";

/** Left panel of the Runs screens (03, 03b): study area and period. */
export function AreaPicker() {
  const { area, setArea, role, r8Published } = useStore();
  const current = AREAS.find((a) => a.key === area)!;
  return (
    <aside className="flex w-[300px] flex-none flex-col gap-1.5 overflow-y-auto border-r border-line bg-surface px-4 py-5">
      <h2 className="text-[15px] font-semibold leading-5">Pick area and period</h2>
      <div className="eyebrow text-ink-3">Study area</div>
      {AREAS.map((a) => {
        const on = a.key === area;
        const runs = runsFor(r8Published).filter((r) => r.area === a.key && (role === "analyst" || !r.private));
        const sub = !a.configured ? "Add one config file" : runs.length ? `${runs.length} runs · latest Oct 2026` : "No runs yet";
        return (
          <button
            key={a.key}
            onClick={() => setArea(a.key)}
            className={cn(
              "flex gap-2.5 rounded-lg border px-3 py-2.5 text-left transition-colors",
              on ? "border-primary bg-primary-tint" : "border-line hover:bg-bg",
            )}
          >
            <MapPin size={16} strokeWidth={1.9} className={cn("mt-px flex-none", a.configured ? "text-ink-2" : "text-ink-3")} />
            <span className="flex flex-col gap-0.5">
              <span className={cn("text-[13px] font-medium leading-4", !a.configured && "text-ink-3")}>{a.name}</span>
              <span className="text-[11px] leading-[14px] text-ink-3">{a.config}</span>
              <span className="text-xs leading-4 text-ink-2">{sub}</span>
            </span>
          </button>
        );
      })}

      <div className="h-2.5 flex-none" />
      <div className="eyebrow text-ink-3">Period</div>
      <div className="flex gap-2">
        {current.period.map((p) => (
          <span key={p} className="flex h-8 flex-1 items-center gap-2 rounded-md border border-line-strong bg-surface px-2.5 text-[11px] leading-[14px]">
            <Clock size={14} strokeWidth={1.9} className="text-ink-2" />
            {p}
          </span>
        ))}
      </div>
      <p className="text-xs leading-4 text-ink-3">
        Sentinel-1 covers 2015 to now. New images arrive every 6 days since Sentinel-1C and 1D.
      </p>

      <span className="flex-1" />
      <div className="flex gap-2 rounded-lg bg-subtle p-3 text-xs leading-4 text-ink-2">
        <Info size={15} strokeWidth={1.9} className="mt-px flex-none" />
        <span>
          Changing the study area means changing one config file. The same build runs on Pekalongan, Jakarta, Bangkok
          or the Mekong delta.
        </span>
      </div>
    </aside>
  );
}
