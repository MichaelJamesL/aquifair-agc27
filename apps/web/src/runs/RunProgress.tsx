"use client";

import { Check, FileText, Info, Map as MapIcon, RefreshCw, SquareArrowOutUpRight, TriangleAlert, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Badge, Button, TraceTag, TraceTags, cn } from "@/components/ui";
import { R0008_LOG, RUN_IDENTITY, STAGE_LOG, STAGE_PROGRESS, STAGES, type LogLine, type StageState } from "@/data/runs";
import { useStore } from "@/state";

const M4 = STAGES.findIndex((s) => s.code === "M4");
const GATE2 = STAGES.findIndex((s) => s.code === "Gate 2");
const LAST = STAGES.length - 1; // Gate 3, sign-off

/** 05 · Run in progress, and 05b · Run stopped at Gate 2 */
export function RunProgress({ id }: { id: string }) {
  return id === "R-0009" ? <Stopped /> : <Running />;
}

/* ---------- shared pieces ---------- */

function StatusIcon({ state }: { state: StageState }) {
  if (state === "done")
    return (
      <span className="grid size-[22px] flex-none place-items-center rounded-full bg-pass text-white">
        <Check size={13} strokeWidth={2.6} />
      </span>
    );
  if (state === "failed")
    return (
      <span className="grid size-[22px] flex-none place-items-center rounded-full bg-fail text-white">
        <X size={13} strokeWidth={2.6} />
      </span>
    );
  if (state === "running")
    return (
      <span className="grid size-[22px] flex-none place-items-center rounded-full border-2 border-primary bg-primary-tint">
        <span className="size-2 animate-pulse rounded-full bg-primary" />
      </span>
    );
  return (
    <span
      className={cn(
        "size-[22px] flex-none rounded-full border-[1.5px] border-line-strong",
        state === "skipped" && "border-dashed",
      )}
    />
  );
}

function StageTable({ states, detail, time }: { states: StageState[]; detail: (i: number) => string; time: (i: number) => string }) {
  return (
    <div className="overflow-hidden rounded-[10px] border border-line bg-surface">
      {STAGES.map((s, i) => {
        const st = states[i];
        const muted = st === "queued" || st === "waiting" || st === "skipped" || st === "later";
        return (
          <div
            key={s.code}
            className={cn(
              "flex items-center gap-3 px-4 transition-colors duration-500",
              i > 0 && "border-t border-line",
              s.gate ? "h-[39px] bg-bg" : "h-[43px]",
              st === "running" && "bg-primary-tint/40",
            )}
          >
            <StatusIcon state={st} />
            <TraceTag code={s.code} />
            <span className={cn("w-60 font-medium", s.gate ? "text-xs leading-4" : "text-[13px] leading-4", muted ? "text-ink-3" : "text-ink")}>
              {s.name}
            </span>
            <span
              className={cn(
                "text-xs leading-4",
                st === "running" ? "text-primary" : st === "failed" ? "text-fail" : "text-ink-2",
              )}
            >
              {detail(i)}
            </span>
            <span className="flex-1" />
            <span className="text-[11px] leading-[14px] text-ink-3">{time(i)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Header({
  title,
  badge,
  sub,
  stage,
  pct,
  bar,
}: {
  title: string;
  badge: React.ReactNode;
  sub: string;
  stage: string;
  pct: number;
  bar: string;
}) {
  return (
    <>
      <div className="flex h-[30px] items-center gap-2.5">
        <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">{title}</h1>
        {badge}
        <span className="flex-1" />
        <TraceTags codes={["U6", "S5"]} />
      </div>
      <p className="text-[11px] leading-[14px] text-ink-3">{sub}</p>
      <div className="flex flex-col gap-1.5">
        <div className="flex h-4 items-center">
          <span className="text-xs font-medium leading-4">{stage}</span>
          <span className="flex-1" />
          <span className="text-[11px] leading-[14px] text-ink-2">{pct}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-[3px] bg-subtle">
          <span className={cn("block h-full rounded-[3px] transition-[width] duration-700", bar)} style={{ width: `${pct}%` }} />
        </div>
      </div>
    </>
  );
}

/* ---------- 05 · running (live demo) ---------- */

function fmtElapsed(min: number) {
  return `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")} min`;
}

function Running() {
  const { role, setR8Published } = useStore();
  const router = useRouter();
  const analyst = role === "analyst";
  const logRef = useRef<HTMLDivElement>(null);

  // Opened as in the design: mid-way through M4. A run opened straight from "Start run"
  // (?fresh=1) restarts from S1 once the page is on screen.
  const [fresh, setFresh] = useState(false);
  const [idx, setIdx] = useState(M4); // stage now running
  const [signed, setSigned] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [log, setLog] = useState<LogLine[]>(R0008_LOG);
  const [elapsed, setElapsed] = useState(192);

  useEffect(() => {
    if (!window.location.search.includes("fresh")) return;
    setFresh(true);
    setIdx(0);
    setElapsed(0);
    setLog([{ t: "10:42:03", tag: "ingest", msg: "run started · config 7e1b42c9" }]);
  }, []);

  const finished = idx >= LAST; // everything up to M9 done, waiting for sign-off

  useEffect(() => {
    if (finished || cancelled) return;
    const t = setTimeout(
      () => {
        const done = STAGES[idx];
        setLog((l) => {
          const seen = new Set(l.map((x) => x.t + x.msg));
          return [...l, ...(STAGE_LOG[done.code] ?? []).filter((x) => !seen.has(x.t + x.msg))];
        });
        setElapsed((e) => e + (done.gate ? 1 : 7));
        setIdx((i) => i + 1);
      },
      fresh ? 2200 : 3200,
    );
    return () => clearTimeout(t);
  }, [idx, finished, cancelled, fresh]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [log]);

  const states: StageState[] = STAGES.map((s, i) => {
    if (i === LAST) return signed ? "done" : finished ? "running" : "later";
    if (i < idx) return "done";
    if (i === idx) return cancelled ? "queued" : "running";
    return s.gate ? "waiting" : "queued";
  });

  const pct = signed ? 100 : finished ? 98 : idx === M4 && !fresh ? 46 : Math.round(((STAGE_PROGRESS[idx - 1] ?? 0) + STAGE_PROGRESS[idx]) / 2);
  const cur = STAGES[Math.min(idx, LAST)];
  const stageText = signed
    ? "Signed off · published"
    : finished
      ? "All stages done · waiting for sign-off"
      : `Stage ${cur.code} of M9 · ${cur.name.toLowerCase()}`;

  return (
    <div className="flex min-h-0 flex-1">
      <section className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-7 py-6">
        <div className="flex flex-col gap-4">
          <Header
            title={signed ? "R-0008 is published" : cancelled ? "R-0008 was cancelled" : finished ? "R-0008 is ready for sign-off" : "R-0008 is running"}
            badge={
              signed ? (
                <Badge tone="pass">Published</Badge>
              ) : cancelled ? (
                <Badge tone="neutral">Cancelled</Badge>
              ) : finished ? (
                <Badge tone="warn">Needs sign-off</Badge>
              ) : (
                <Badge tone="running">Running</Badge>
              )
            }
            sub={`Started 12 Nov 2026, 10:42 · elapsed ${fmtElapsed(elapsed)} · this page checks progress every 10 s`}
            stage={stageText}
            pct={pct}
            bar={signed ? "bg-pass" : "bg-primary"}
          />
        </div>
        <StageTable
          states={states}
          detail={(i) => {
            const s = STAGES[i];
            if (i === idx && !finished && s.code === "M4") return "ICA, 5 components · change points 62%";
            if (i === LAST) return signed ? "A. Wibowo, BIG · today" : s.queued;
            return states[i] === "done" ? s.done : s.queued;
          }}
          time={(i) => {
            const st = states[i];
            if (i === LAST) return signed ? "signed" : finished ? "waiting" : "later";
            if (st === "done") return STAGES[i].time;
            if (st === "running") return "running";
            return st;
          }}
        />
        <p className="flex items-center gap-2 text-xs leading-4 text-ink-2">
          <Info size={15} strokeWidth={1.9} />
          You can close this page. The run keeps going and you will see it under Runs when it finishes. Nothing is
          published until Gate 3.
        </p>
      </section>

      <aside className="flex w-[400px] flex-none flex-col gap-3 border-l border-line bg-surface p-5">
        <div className="flex h-[22px] items-center gap-2">
          <h2 className="text-[15px] font-semibold leading-5">Run log</h2>
          <span className="flex-1" />
          {!finished && !cancelled && <Badge tone="running">live</Badge>}
        </div>
        <div
          ref={logRef}
          className="flex max-h-[360px] flex-col gap-1.5 overflow-y-auto rounded-lg bg-ink p-3.5 font-mono text-[10.5px] leading-[14px] text-bg"
        >
          {log.map((l) => (
            <div key={l.t + l.msg} className={cn("grid grid-cols-[64px_70px_1fr] whitespace-nowrap", l.ok && "text-[#8cd9a6]")}>
              <span>{l.t}</span>
              <span>{l.tag}</span>
              <span className="truncate">{l.msg}</span>
            </div>
          ))}
        </div>
        <div className="flex flex-col gap-1 rounded-lg bg-subtle p-3 text-[11px] leading-[14px] text-ink-2">
          <span className="text-xs font-medium leading-4 text-ink">Run identity</span>
          {RUN_IDENTITY.map((r) => (
            <span key={r}>{r}</span>
          ))}
        </div>
        <span className="flex-1" />
        <div className="flex items-center gap-2">
          {signed ? (
            <>
              <span className="flex-1" />
              <Button variant="primary" size="md" icon={<MapIcon size={16} strokeWidth={2} />} onClick={() => router.push("/")}>
                Open map
              </Button>
            </>
          ) : finished ? (
            <>
              <Button size="md" icon={<FileText size={16} strokeWidth={2} />} onClick={() => router.push("/validation")}>
                Review report
              </Button>
              <span className="flex-1" />
              <Button
                variant="primary"
                size="md"
                disabled={!analyst}
                title={analyst ? undefined : "Only a named analyst can sign off"}
                className="disabled:cursor-not-allowed disabled:opacity-50"
                icon={<Check size={16} strokeWidth={2} />}
                onClick={() => {
                  setSigned(true);
                  setR8Published(true);
                }}
              >
                Sign off and publish
              </Button>
            </>
          ) : (
            <>
              <Button size="md" disabled={cancelled || !analyst} className="disabled:opacity-50" onClick={() => setCancelled(true)}>
                {cancelled ? "Cancelled" : "Cancel run"}
              </Button>
              <span className="flex-1" />
              <Button size="md" icon={<SquareArrowOutUpRight size={16} strokeWidth={2} />}>
                Open run record
              </Button>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}

/* ---------- 05b · stopped at Gate 2 ---------- */

const CHECKS = [
  { name: "Recall", value: "88%", limit: "≥ 80%", ok: true },
  { name: "Precision", value: "71%", limit: "≥ 80%", ok: false },
  { name: "Median volume error", value: "12%", limit: "≤ 25%", ok: true },
];

function Stopped() {
  const router = useRouter();
  const states: StageState[] = STAGES.map((_, i) => (i < GATE2 ? "done" : i === GATE2 ? "failed" : "skipped"));
  return (
    <div className="flex min-h-0 flex-1">
      <section className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-7 py-6">
        <Header
          title="R-0009 stopped at Gate 2"
          badge={<Badge tone="fail">Stopped</Badge>}
          sub="Started 13 Nov 2026, 08:15 · stopped after 4 h 02 min · run stays private"
          stage="Stopped after M7 · uncertainty"
          pct={78}
          bar="bg-fail"
        />
        <StageTable
          states={states}
          detail={(i) => {
            if (i === GATE2) return "V3 precision 71% < 80%";
            if (i === LAST) return "not reached";
            return states[i] === "done" ? STAGES[i].done : "not run";
          }}
          time={(i) => (i === GATE2 ? "failed" : states[i] === "done" ? STAGES[i].time : "–")}
        />
      </section>

      <aside className="flex w-[400px] flex-none flex-col gap-3.5 border-l border-line bg-surface p-5">
        <div className="flex h-5 items-center gap-2">
          <TriangleAlert size={18} strokeWidth={1.9} className="text-fail" />
          <h2 className="text-[15px] font-semibold leading-5">Which check failed</h2>
          <span className="flex-1" />
          <TraceTag code="V3" />
        </div>
        <div className="overflow-hidden rounded-lg border border-line">
          {CHECKS.map((c, i) => (
            <div key={c.name} className={cn("flex h-10 items-center gap-2 px-3", i > 0 && "border-t border-line", !c.ok && "bg-fail-tint")}>
              {c.ok ? <Check size={14} strokeWidth={2} className="text-pass" /> : <X size={14} strokeWidth={2} className="text-fail" />}
              <span className="text-[13px] leading-[19px]">{c.name}</span>
              <span className="flex-1" />
              <span className={cn("text-[13px] leading-[18px]", !c.ok && "text-fail")}>{c.value}</span>
              <span className="w-[35px] text-right text-[11px] leading-[14px] text-ink-3">{c.limit}</span>
            </div>
          ))}
        </div>
        <h3 className="text-[13px] font-medium leading-4">Why</h3>
        <p className="text-[13px] leading-[19px] text-ink-2">
          This run’s noise is 4.6 mm/yr, about twice the usual. Precision falls as noise grows: the benchmark expects
          65–71% at this level. Gate 2 reruns the benchmark with each run’s own noise and gaps, so the expectation is
          honest.
        </p>
        <h3 className="text-[13px] font-medium leading-4">What to try</h3>
        <ul className="flex flex-col gap-3.5 text-[13px] leading-[19px]">
          {[
            "Tighten quality control in M2: shorter pair network, stricter coherence mask.",
            "Check the 12-day period 2022–2024 for unwrapping errors.",
            "Rerun. The failed run is kept for comparison, never overwritten.",
          ].map((t) => (
            <li key={t} className="flex gap-2">
              <span className="mt-[7px] size-1 flex-none bg-ink-2" />
              {t}
            </li>
          ))}
        </ul>
        <span className="flex-1" />
        <div className="flex items-center gap-2">
          <Button size="md" icon={<FileText size={16} strokeWidth={2} />}>
            Diagnostics
          </Button>
          <span className="flex-1" />
          <Button variant="primary" size="md" icon={<RefreshCw size={16} strokeWidth={2} />} onClick={() => router.push("/runs/new")}>
            Rerun with new settings
          </Button>
        </div>
      </aside>
    </div>
  );
}
