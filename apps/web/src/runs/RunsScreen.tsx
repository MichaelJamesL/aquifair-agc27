"use client";

import { FileText, Lock, Map as MapIcon, Play, SquareArrowOutUpRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Badge, Button, cn } from "@/components/ui";
import { AREAS, STATUS_LABEL, detailsFor, runsFor, type Run, type RunStatus } from "@/data/runs";
import { MapThumb } from "@/map/MapThumb";
import { useStore } from "@/state";
import { AreaPicker } from "./AreaPicker";

const TONE: Record<RunStatus, "pass" | "neutral" | "running" | "fail"> = {
  published: "pass",
  superseded: "neutral",
  running: "running",
  stopped: "fail",
};

const COLS = "grid grid-cols-[110px_150px_70px_80px_1fr_auto] items-center";

/** 03 · Open a run, and 03b · No run for this area yet */
export function RunsScreen() {
  const { area, role, r8Published } = useStore();
  const router = useRouter();
  const a = AREAS.find((x) => x.key === area)!;
  const runs = runsFor(r8Published).filter((r) => r.area === area && (role === "analyst" || !r.private));
  const [picked, setPicked] = useState("R-0007");
  const selected = runs.find((r) => r.id === picked) ?? runs.find((r) => r.status === "published") ?? runs[0];

  return (
    <div className="flex min-h-0 flex-1">
      <AreaPicker />
      {runs.length === 0 ? (
        <EmptyArea />
      ) : (
        <>
          <section className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-7 py-6">
            <div className="flex h-[30px] items-center gap-2">
              <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">Runs · {a.name}</h1>
              <span className="flex-1" />
              <span className="text-xs text-ink-3">{role === "analyst" ? "All runs, private ones included" : "Published runs only"}</span>
              {role === "analyst" && (
                <Button variant="primary" icon={<Play size={14} strokeWidth={2} />} onClick={() => router.push("/runs/new")}>
                  Start a run
                </Button>
              )}
            </div>
            <p className="text-[13px] leading-[19px] text-ink-2">
              Pick a finished run to open its map and audit list. Regulators never start runs; analysts do.
            </p>

            <div className="overflow-hidden rounded-[10px] border border-line bg-surface">
              <div className={cn(COLS, "eyebrow h-[30px] bg-bg px-4 py-2 text-ink")}>
                <span>Run</span>
                <span>Period</span>
                <span>Images</span>
                <span>Hot spots</span>
                <span>Signed off</span>
                <span>Status</span>
              </div>
              {runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setPicked(r.id)}
                  onDoubleClick={() => openRun(r)}
                  className={cn(
                    COLS,
                    "h-[51px] w-full border-t border-line px-4 text-left transition-colors",
                    selected?.id === r.id ? "bg-primary-tint" : "hover:bg-bg",
                  )}
                >
                  <span className="text-[13px] font-bold leading-[18px]">{r.id}</span>
                  <span className="text-[11px] leading-[14px] text-ink-2">{r.period}</span>
                  <span className="text-[11px] leading-[14px] text-ink-2">{r.images}</span>
                  <span className="text-[11px] leading-[14px] text-ink-2">{r.hotSpots ?? "–"}</span>
                  <span className="text-[13px] leading-[19px] text-ink-2">{r.signedOff ?? (r.private ? "private" : "–")}</span>
                  <Badge tone={TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 text-xs leading-4 text-ink-3">
              <Lock size={14} strokeWidth={1.9} />
              Private and failed runs are visible to analysts only. Old runs are never overwritten, so any two can be
              compared.
            </div>
          </section>

          {selected && <RunPreview run={selected} />}
        </>
      )}
    </div>
  );

  function openRun(r: Run) {
    if (r.status === "running" || r.status === "stopped") router.push(`/runs/${r.id}`);
    else router.push("/");
  }
}

function RunPreview({ run }: { run: Run }) {
  const router = useRouter();
  const { r8Published } = useStore();
  const live = run.status === "running" || run.status === "stopped";
  return (
    <aside className="flex w-[400px] flex-none flex-col gap-3.5 border-l border-line bg-surface p-5">
      <div className="flex h-6 items-center gap-2">
        <h2 className="text-lg font-semibold leading-6 tracking-[-0.01em]">{run.id}</h2>
        <span className="flex-1" />
        <Badge tone={TONE[run.status]}>{STATUS_LABEL[run.status]}</Badge>
      </div>
      <div className={cn(run.status !== "published" && "opacity-80 grayscale-[0.6]")}>
        <MapThumb dots={run.status === "published" || run.status === "superseded"} />
      </div>
      <div className="flex flex-col">
        {detailsFor(run.id, r8Published).map((d) => (
          <div key={d.label} className="flex h-9 items-center gap-3 border-b border-line text-[13px] leading-[19px]">
            <span className="text-ink-2">{d.label}</span>
            <span className="flex-1" />
            <span className={d.warn ? "text-warn" : "text-ink"}>{d.value}</span>
          </div>
        ))}
      </div>
      <span className="flex-1" />
      {live ? (
        <Button
          variant="primary"
          size="md"
          icon={<SquareArrowOutUpRight size={16} strokeWidth={2} />}
          onClick={() => router.push(`/runs/${run.id}`)}
        >
          Open run record
        </Button>
      ) : run.status === "published" ? (
        <Button variant="primary" size="md" icon={<MapIcon size={16} strokeWidth={2} />} onClick={() => router.push("/")}>
          Open map
        </Button>
      ) : (
        <Button variant="secondary" size="md" icon={<FileText size={16} strokeWidth={2} />} onClick={() => router.push("/compare")}>
          Compare with R-0007
        </Button>
      )}
    </aside>
  );
}

function EmptyArea() {
  const { area, role, r8Published } = useStore();
  const router = useRouter();
  const a = AREAS.find((x) => x.key === area)!;
  return (
    <section className="flex flex-1 flex-col items-center justify-center gap-3.5 p-10 text-center">
      <svg width="96" height="72" viewBox="0 0 96 72" fill="none" aria-hidden>
        <path d="M4 22a44 30 0 0 0 88 0" stroke="#bdb6a8" strokeWidth="2" />
        <path d="M18 22a30 20 0 0 0 60 0" stroke="#bdb6a8" strokeWidth="2" />
        <path d="M32 22a16 10 0 0 0 32 0" stroke="#bdb6a8" strokeWidth="2" />
        <path d="M4 22h88" stroke="#ddd8ce" strokeWidth="2" />
        <path d="M48 2v28" stroke="#0f4c5c" strokeWidth="3" />
      </svg>
      <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">
        {a.configured ? `No run for ${a.name}, ${a.period[0]} – ${a.period[1]}` : `${a.name} is not configured yet`}
      </h1>
      <p className="max-w-[560px] text-sm leading-[21px] text-ink-2">
        {a.configured
          ? "The config file is ready, but nobody has processed this area yet. Starting a run downloads radar pairs, builds the maps and runs the inversion. It stays private until an analyst signs it off."
          : `Add ${a.key}.yaml with the area outline, the radar tracks and a reference GNSS station. The same build then runs here without code changes.`}
      </p>
      {role === "analyst" ? (
        <div className="flex gap-2.5">
          <Button size="md" icon={<FileText size={16} strokeWidth={2} />}>
            {a.configured ? `Edit ${a.config}` : `Create ${a.key}.yaml`}
          </Button>
          {a.configured && (
            <Button variant="primary" size="md" icon={<Play size={16} strokeWidth={2} />} onClick={() => router.push("/runs/new")}>
              Start a run
            </Button>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2 rounded-lg bg-subtle px-3.5 py-2.5 text-xs leading-4 text-ink-2">
          <Lock size={14} strokeWidth={1.9} />
          Ask a BIG analyst to start a run.
        </div>
      )}
      {role === "analyst" && (
        <div className="flex items-center gap-2 rounded-lg bg-subtle px-3.5 py-2.5 text-xs leading-4 text-ink-2">
          <Lock size={14} strokeWidth={1.9} />
          Regulators see this message without the buttons: “Ask a BIG analyst to start a run.”
        </div>
      )}
    </section>
  );
}
