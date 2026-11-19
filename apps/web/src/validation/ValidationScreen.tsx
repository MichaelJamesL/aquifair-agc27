"use client";

import { AlertTriangle, Check, Clock, FileText, ShieldCheck, SquareArrowOutUpRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Badge, Button, TraceTag, TraceTags, cn } from "@/components/ui";
import { CHECKS } from "@/data/sheet";
import { useT } from "@/i18n";
import { useStore } from "@/state";

const GATES = [
  { name: "Gate 1", after: "After M2 · radar quality", checks: "V1, V2", status: "Passed 12 Nov, 14:05" },
  { name: "Gate 2", after: "After M7 · inversion", checks: "V3, V4", status: "Passed 12 Nov, 16:40" },
  { name: "Gate 3", after: "Before publishing", checks: "V7, V5–V6 if wells exist, named sign-off", status: "Waiting for sign-off" },
];

const BASELINES = [
  { name: "Bowl integration", found: 28, real: 89 },
  { name: "Smooth inversion", found: 90, real: 35 },
  { name: "Sparse inversion (ours)", found: 89, real: 81 },
];

/** 14 · Validation of R-0008 and the Gate 3 sign-off (V1–V7, S6) */
export function ValidationScreen() {
  const { role, r8Published, setR8Published } = useStore();
  const { pick } = useT();
  const router = useRouter();
  const analyst = role === "analyst";
  const [read, setRead] = useState(true);
  const [note, setNote] = useState("Monthly update with 14 new Sentinel-1C/1D images. Two sources changed, see Compare.");

  return (
    <div className="flex min-h-0 flex-1">
      {/* left: gates and identity */}
      <aside className="flex w-[250px] flex-none flex-col gap-4 overflow-y-auto border-r border-line bg-surface px-5 py-6 min-[1400px]:w-[300px]">
        <h2 className="text-[17px] font-semibold leading-6">Quality gates</h2>
        <ol className="flex flex-col">
          {GATES.map((g, i) => {
            const done = i < 2 || r8Published;
            return (
              <li key={g.name} className="relative flex gap-3 pb-4">
                {i < 2 && <span className="absolute left-[11px] top-7 h-[calc(100%-26px)] w-0.5 bg-pass" />}
                <span
                  className={cn(
                    "z-[1] grid size-6 flex-none place-items-center rounded-full",
                    done ? "bg-pass text-white" : "bg-primary-tint text-primary",
                  )}
                >
                  {done ? <Check size={14} strokeWidth={2.6} /> : <Clock size={15} strokeWidth={2} />}
                </span>
                <span className="flex flex-col gap-0.5">
                  <span className="text-[13px] font-medium leading-5">{g.name}</span>
                  <span className="text-xs text-ink-2">{g.after}</span>
                  <span className="text-[11px] leading-[14px] text-ink-3">{g.checks}</span>
                  <span className={cn("mt-1 text-xs", done ? "text-pass" : "text-primary")}>
                    {i === 2 && r8Published ? "Signed off by A. Wibowo" : g.status}
                  </span>
                </span>
              </li>
            );
          })}
        </ol>

        <div className="flex flex-col gap-1.5 rounded-lg bg-subtle p-3">
          <span className="text-[13px] font-medium">Run identity</span>
          {[
            ["code commit", "a3f9c21"],
            ["config hash", "7e1b42c9"],
            ["input data", "d1:5c0a · d3:0b6e · d4:91be · d5:44a1 · d8:20f7"],
            ["seeds", "fixed · 200 resamples"],
          ].map(([k, v]) => (
            <span key={k} className="flex flex-col text-[11px] leading-[14px]">
              <span className="text-ink-3">{k}</span>
              <span className="text-ink">{v}</span>
            </span>
          ))}
          <p className="mt-1 text-xs leading-4 text-ink-2">Same three hashes always give the same outputs.</p>
        </div>

        <div className="flex flex-col gap-3">
          {["Model card", "Data card", "Tracking record (MLflow)"].map((l) => (
            <a key={l} href={l === "Tracking record (MLflow)" ? "#" : "/sheet?lang=en&version=regulator"} target="_blank" rel="noreferrer" className="flex items-center gap-2.5 text-[13px] hover:text-primary">
              <FileText size={15} strokeWidth={1.8} className="text-ink-2" />
              <span className="flex-1">{l}</span>
              <SquareArrowOutUpRight size={14} strokeWidth={1.8} className="text-ink-3" />
            </a>
          ))}
        </div>
      </aside>

      {/* centre: checks */}
      <section className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-6 py-6">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">{pick("Validation", "Validasi")} · R-0008</h1>
          <TraceTags codes={["V1–V7", "S6"]} />
        </div>
        <div className="flex gap-3 rounded-lg bg-warn-tint px-4 py-3 text-[13px] leading-[19px]">
          <AlertTriangle size={16} strokeWidth={1.9} className="mt-0.5 flex-none text-warn" />
          <span>
            Not yet checked against wells. Well records (D6) have not arrived, so V5 and V6 cannot run. Every view and export of
            this run carries that label until they do.
          </span>
        </div>

        <div className="overflow-hidden rounded-lg border border-line bg-surface">
          <div className="eyebrow grid h-[30px] grid-cols-[minmax(150px,190px)_minmax(130px,170px)_minmax(96px,110px)_minmax(70px,1fr)_auto] items-center gap-x-2 bg-bg px-3.5 text-ink">
            <span>Check</span>
            <span>How it is measured</span>
            <span>Value</span>
            <span>Pass mark</span>
            <span>Result</span>
          </div>
          {CHECKS.map((c) => (
            <div key={c.code} className="grid grid-cols-[minmax(150px,190px)_minmax(130px,170px)_minmax(96px,110px)_minmax(70px,1fr)_auto] items-start gap-x-2 border-t border-line px-3.5 py-2.5">
              <span className="flex items-center gap-2 text-[13px]">
                <TraceTag code={c.code} size={11} />
                {c.name.en === "Synthetic test at this run's noise" ? "Synthetic recovery" : c.name.en}
              </span>
              <span className="text-xs leading-4 text-ink-2">{c.how}</span>
              <span className="text-[11px] leading-[14px]">
                {c.code === "V3" ? "recall 89%, precision 81%, vol. error 9%" : c.code === "V2" ? "2.7% dropped" : c.code === "V4" ? "beats both" : c.value.en}
              </span>
              <span className="text-[11px] leading-[14px] text-ink-3">{c.markLong}</span>
              <span>{c.result === "pass" ? <Badge tone="pass">Passed</Badge> : <Badge tone="warn">Needs D6</Badge>}</span>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-2.5 rounded-lg border border-line bg-surface px-3.5 py-3.5">
          <div className="flex items-center">
            <span className="text-[13px] font-medium">Against the baselines, same data</span>
            <span className="flex-1" />
            <span className="text-xs text-ink-3">synthetic benchmark at this run’s noise</span>
          </div>
          {BASELINES.map((b) => (
            <div key={b.name} className="flex h-6 items-center gap-3 text-[13px]">
              <span className="w-[150px] flex-none min-[1400px]:w-[170px]">{b.name}</span>
              <Bar pct={b.found} tone="bg-primary" />
              <span className="w-[64px] flex-none whitespace-nowrap text-[11px] text-ink-2">{b.found}% found</span>
              <Bar pct={b.real} tone="bg-range" />
              <span className="w-[56px] flex-none whitespace-nowrap text-[11px] text-ink-2">{b.real}% real</span>
            </div>
          ))}
        </div>
      </section>

      {/* right: publish */}
      <aside className="flex w-[340px] flex-none flex-col gap-4 border-l border-line bg-surface px-5 py-6 min-[1400px]:w-[400px]">
        <div className="flex items-center">
          <h2 className="text-lg font-semibold leading-6">Publish R-0008</h2>
          <span className="flex-1" />
          <TraceTag code="Gate 3" />
        </div>
        <p className="text-[13px] leading-[19px] text-ink-2">
          {r8Published
            ? "R-0008 is now the default run for regulators. R-0007 stays available to compare."
            : "Unpublished runs stay private. Publishing makes this run the default for regulators; R-0007 stays available to compare."}
        </p>
        <div className="flex flex-col gap-2.5 rounded-lg bg-bg px-3.5 py-3 text-[13px] leading-[19px]">
          <Item ok>Gates 1 and 2 passed</Item>
          <Item ok>V7: 86% of ranges hold (80–95%)</Item>
          <Item>V5, V6 not run: label “not yet checked against wells” added</Item>
          <Item ok>Model card and data card attached</Item>
        </div>

        <label className="flex flex-col gap-1.5 text-xs">
          <span>Signed off by</span>
          <input
            readOnly
            value={analyst ? "A. Wibowo · geospatial analyst, BIG" : "Only a named analyst can sign off"}
            className="h-10 rounded-md border border-line-strong px-3 text-[13px] text-ink outline-none read-only:bg-surface"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-xs">
          <span>Note for the run record</span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={r8Published}
            rows={3}
            className="resize-none rounded-md border border-line-strong px-3 py-2.5 text-[13px] leading-[19px] text-ink outline-none focus:border-primary"
          />
        </label>
        <label className="flex cursor-pointer gap-3 text-[13px] leading-[19px]">
          <input type="checkbox" checked={read} onChange={(e) => setRead(e.target.checked)} className="peer absolute opacity-0" />
          <span className={cn("mt-0.5 grid size-4 flex-none place-items-center rounded-[3px] text-bg", read ? "bg-primary" : "shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]")}>
            {read && <Check size={12} strokeWidth={2.6} />}
          </span>
          I have read the known limits in the model card, including that volumes depend on cone width B.
        </label>

        <span className="flex-1" />
        <div className="flex items-center">
          {r8Published ? (
            <>
              <Badge tone="pass">Published</Badge>
              <span className="flex-1" />
              <Button variant="primary" size="md" onClick={() => router.push("/compare")}>
                Open Compare
              </Button>
            </>
          ) : (
            <>
              <Button size="md" onClick={() => router.push("/runs")}>
                Keep private
              </Button>
              <span className="flex-1" />
              <Button
                variant="primary"
                size="md"
                disabled={!analyst || !read}
                title={!analyst ? "Only a named analyst can sign off" : !read ? "Confirm you read the known limits" : undefined}
                className="disabled:cursor-not-allowed disabled:opacity-50"
                icon={<ShieldCheck size={16} strokeWidth={2} />}
                onClick={() => setR8Published(true)}
              >
                Sign off and publish
              </Button>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}

function Bar({ pct, tone }: { pct: number; tone: string }) {
  return (
    <span className="relative h-1.5 w-[140px] flex-none rounded-[3px] bg-subtle">
      <span className={cn("absolute inset-y-0 left-0 rounded-[3px]", tone)} style={{ width: `${pct}%` }} />
    </span>
  );
}

function Item({ ok, children }: { ok?: boolean; children: ReactNode }) {
  return (
    <span className="flex gap-2.5">
      {ok ? (
        <Check size={15} strokeWidth={2.2} className="mt-0.5 flex-none text-pass" />
      ) : (
        <AlertTriangle size={15} strokeWidth={1.9} className="mt-0.5 flex-none text-warn" />
      )}
      {children}
    </span>
  );
}
