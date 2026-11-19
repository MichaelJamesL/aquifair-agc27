"use client";

import { Check, ChevronDown, ChevronRight, Clock, Lock, Play } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { Badge, Button, TraceTag, TraceTags, cn } from "@/components/ui";
import { AREAS, DATA_INPUTS, PIPELINE_STEPS } from "@/data/runs";
import { useStore } from "@/state";

const CONTROL = "flex h-[34px] items-center gap-2 rounded-md border border-line-strong bg-surface px-2.5 text-[13px] leading-[18px]";

function Field({ label, width, children }: { label: string; width: number; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-[5px]" style={{ width }}>
      <span className="text-xs font-medium leading-4 text-ink-2">{label}</span>
      {children}
    </label>
  );
}

function Select({ value, options, onChange }: { value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <span className={cn(CONTROL, "relative pr-8")}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="absolute inset-0 w-full cursor-pointer appearance-none bg-transparent px-2.5 outline-none"
      >
        {options.map((o) => (
          <option key={o}>{o}</option>
        ))}
      </select>
      <ChevronDown size={14} strokeWidth={1.9} className="pointer-events-none absolute right-2.5 text-ink-2" />
    </span>
  );
}

function NumberInput({ value, unit, onChange }: { value: string; unit?: string; onChange: (v: string) => void }) {
  return (
    <span className={CONTROL}>
      <input value={value} onChange={(e) => onChange(e.target.value)} className="w-full min-w-0 bg-transparent outline-none" />
      {unit && <span className="whitespace-nowrap text-[11px] leading-[14px] text-ink-3">{unit}</span>}
    </span>
  );
}

function Card({ title, sub, code, children }: { title: string; sub?: string; code?: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2.5 rounded-[10px] border border-line bg-surface px-4 py-[13px]">
      <div className="flex h-5 items-center gap-2">
        <h2 className="text-[15px] font-semibold leading-5">{title}</h2>
        {sub && <span className="text-xs leading-4 text-ink-3">{sub}</span>}
        <span className="flex-1" />
        {code && <TraceTag code={code} />}
      </div>
      {children}
    </section>
  );
}

const MONTHS = ["Jan 2015", "Jan 2016", "Jan 2018", "Jan 2020", "Jan 2022"];
const ENDS = ["Nov 2026", "Oct 2026", "Apr 2026", "Dec 2025"];

const INPUT_TONE = {
  Open: "pass",
  Received: "pass",
  Optional: "neutral",
  Partial: "neutral",
  "Not received": "warn",
} as const;

/** 04 · Start a run (analysts only) */
export function StartRun() {
  const { role, area } = useStore();
  const router = useRouter();
  const analyst = role === "analyst";
  const configured = AREAS.filter((a) => a.configured);
  const [form, setForm] = useState({
    area: (AREAS.find((a) => a.key === area && a.configured) ?? AREAS[0]).config,
    start: "Jan 2015",
    end: "Nov 2026",
    desc: true,
    asc: true,
    gnss: "CSEM",
    coherence: "0.30",
    network: "next 4 images",
    atmosphere: "GACOS",
    widths: { low: true, mid: true, high: true },
    spacing: "500",
    bootstrap: "200",
    block: "2",
    floor: "20k",
    mode: "blind" as "blind" | "informed",
  });
  const set = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) => setForm((f) => ({ ...f, [k]: v }));
  const areaName = AREAS.find((a) => a.config === form.area)?.name ?? "Semarang–Demak";
  const canStart = analyst && (form.desc || form.asc) && Object.values(form.widths).some(Boolean);

  return (
    <div className="flex min-h-0 flex-1">
      <section className="flex min-w-0 flex-1 flex-col gap-2.5 overflow-y-auto px-7 pb-6 pt-4">
        <nav className="flex h-4 items-center gap-1.5 text-xs font-medium leading-4 text-ink-2">
          <Link href="/runs" className="hover:text-ink">
            Runs
          </Link>
          <ChevronRight size={13} strokeWidth={2} />
          <Link href="/runs" className="hover:text-ink">
            {areaName}
          </Link>
          <ChevronRight size={13} strokeWidth={2} />
          <span className="text-ink">Start a run</span>
        </nav>
        <div className="flex h-[30px] items-center gap-2">
          <h1 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">Start a run</h1>
          <TraceTags codes={["U6", "S1", "S5"]} />
          <span className="flex-1" />
          <span className={cn("flex items-center gap-1.5 text-xs", analyst ? "text-ink-3" : "font-medium text-warn")}>
            {!analyst && <Lock size={13} strokeWidth={2} />}
            {analyst ? "Analysts only" : "Analysts only. Switch role to start a run."}
          </span>
        </div>

        <fieldset disabled={!analyst} className={cn("flex flex-col gap-2.5", !analyst && "opacity-60")}>
          <Card title="Area and period">
            <div className="flex gap-4">
              <Field label="Study area" width={300}>
                <Select value={form.area} options={configured.map((a) => a.config)} onChange={(v) => set("area", v)} />
              </Field>
              <Field label="Start" width={140}>
                <Select value={form.start} options={MONTHS} onChange={(v) => set("start", v)} />
              </Field>
              <Field label="End" width={140}>
                <Select value={form.end} options={ENDS} onChange={(v) => set("end", v)} />
              </Field>
            </div>
          </Card>

          <Card title="Radar" sub="Sentinel-1, two viewing directions" code="M1–M3">
            {[
              { k: "desc" as const, name: "Descending track 76", text: "Ready-made LiCSAR pairs, frame 076D_09725_121107 · LiCSBAS" },
              { k: "asc" as const, name: "Ascending track 127", text: "Pairs ordered from ASF on-demand · MintPy" },
            ].map((t) => (
              <label key={t.k} className="flex cursor-pointer gap-2.5">
                <input type="checkbox" checked={form[t.k]} onChange={() => set(t.k, !form[t.k])} className="peer sr-only" />
                <span
                  className={cn(
                    "grid size-4 flex-none place-items-center rounded text-bg peer-focus-visible:outline-2 peer-focus-visible:outline-primary",
                    form[t.k] ? "bg-primary" : "bg-surface shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
                  )}
                >
                  {form[t.k] && <Check size={12} strokeWidth={2.4} />}
                </span>
                <span className="flex flex-col gap-px">
                  <span className="text-[13px] font-medium leading-4">{t.name}</span>
                  <span className="text-xs leading-4 text-ink-3">{t.text}</span>
                </span>
              </label>
            ))}
            <div className="flex gap-4">
              <Field label="Reference GNSS station" width={160}>
                <Select value={form.gnss} options={["CSEM", "CSEM + CDMK", "CPKL"]} onChange={(v) => set("gnss", v)} />
              </Field>
              <Field label="Coherence threshold" width={130}>
                <NumberInput value={form.coherence} onChange={(v) => set("coherence", v)} />
              </Field>
              <Field label="Pair network" width={170}>
                <Select value={form.network} options={["next 4 images", "next 3 images", "next 6 images", "annual pairs added"]} onChange={(v) => set("network", v)} />
              </Field>
              <Field label="Atmosphere" width={130}>
                <Select value={form.atmosphere} options={["GACOS", "ERA5", "none"]} onChange={(v) => set("atmosphere", v)} />
              </Field>
            </div>
          </Card>

          <Card title="Model" code="M4–M8">
            <div className="flex gap-4">
              <div className="flex w-[260px] flex-col gap-[5px]">
                <span className="text-xs font-medium leading-4 text-ink-2">Cone widths B (precomputed)</span>
                <div className="flex gap-1.5">
                  {(
                    [
                      ["low", "1.0 km"],
                      ["mid", "1.5 km"],
                      ["high", "2.0 km"],
                    ] as const
                  ).map(([k, km]) => (
                    <button
                      type="button"
                      key={k}
                      onClick={() => set("widths", { ...form.widths, [k]: !form.widths[k] })}
                      aria-pressed={form.widths[k]}
                      className={cn(
                        "flex h-8 items-center gap-1 rounded-md border border-line-strong px-2.5 transition-colors",
                        form.widths[k] ? (k === "mid" ? "bg-primary-tint" : "bg-surface") : "bg-subtle opacity-60",
                      )}
                    >
                      <span className="text-[11px] leading-[14px]">{km}</span>
                      <span className="text-xs leading-4 text-ink-3">{k}</span>
                    </button>
                  ))}
                </div>
              </div>
              <Field label="Candidate spacing" width={110}>
                <NumberInput value={form.spacing} unit="m" onChange={(v) => set("spacing", v)} />
              </Field>
              <Field label="Bootstrap" width={110}>
                <NumberInput value={form.bootstrap} unit="runs" onChange={(v) => set("bootstrap", v)} />
              </Field>
              <Field label="Block size" width={100}>
                <NumberInput value={form.block} unit="km" onChange={(v) => set("block", v)} />
              </Field>
              <Field label="Report floor" width={110}>
                <NumberInput value={form.floor} unit="m³/yr" onChange={(v) => set("floor", v)} />
              </Field>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-xs font-medium leading-4 text-ink-2">Mode</span>
              <div className="flex rounded-md bg-subtle p-0.5">
                {(
                  [
                    ["blind", "Blind · default"],
                    ["informed", "Informed"],
                  ] as const
                ).map(([k, label]) => (
                  <button
                    type="button"
                    key={k}
                    onClick={() => set("mode", k)}
                    className={cn("h-[26px] rounded px-3 text-xs font-medium leading-4", form.mode === k ? "bg-surface text-ink" : "text-ink-2")}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <p className="w-[420px] text-xs leading-4 text-ink-3">
                Informed lowers the penalty for candidates on industrial land. Blind uses no such prior.
              </p>
            </div>
          </Card>

          <Card title="Data inputs" sub="Only D1, D3, D5 and D8 are needed, all open" code="D1–D9">
            <div className="grid w-[660px] grid-cols-2">
              {DATA_INPUTS.map((d) => (
                <div key={d.code} className="flex h-[30px] items-center gap-2 whitespace-nowrap pr-4">
                  <TraceTag code={d.code} />
                  <span className="text-[13px] leading-[19px]">{d.name}</span>
                  <span className="flex-1" />
                  <Badge tone={INPUT_TONE[d.status]}>{d.status}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </fieldset>
      </section>

      <aside className="flex w-[400px] flex-none flex-col gap-3.5 border-l border-line bg-surface p-5">
        <h2 className="text-lg font-semibold leading-6">What happens next</h2>
        <ol className="flex flex-col">
          {PIPELINE_STEPS.map((s, i) => (
            <li key={s.title} className="flex gap-2.5">
              <span className="flex w-2.5 flex-none flex-col items-center">
                <span className={cn("size-2.5 rounded-full border-2 border-primary", s.gate ? "bg-white" : "bg-primary")} />
                {i < PIPELINE_STEPS.length - 1 && <span className="w-0.5 flex-1 bg-line" />}
              </span>
              <span className="flex flex-col gap-px pb-2">
                <span className={cn("leading-4", s.gate ? "text-xs font-medium text-primary" : "text-[13px] font-medium")}>{s.title}</span>
                <span className="text-xs leading-4 text-ink-2">{s.text}</span>
              </span>
            </li>
          ))}
        </ol>
        <div className="flex gap-2.5 rounded-lg bg-bg p-3 text-xs leading-4 text-ink-2">
          <Clock size={16} strokeWidth={1.9} className="flex-none" />
          Radar step: hours on a 16 GB laptop. Inversion and bootstrap: minutes. You can close this page; the run keeps
          going.
        </div>
        <span className="flex-1" />
        <div className="flex items-center gap-2">
          <Button size="md" onClick={() => router.push("/runs")}>
            Cancel
          </Button>
          <span className="flex-1" />
          <Button
            variant="primary"
            size="md"
            disabled={!canStart}
            className="disabled:cursor-not-allowed disabled:opacity-50"
            icon={<Play size={16} strokeWidth={2} />}
            onClick={() => router.push("/runs/R-0008?fresh=1")}
          >
            Start run
          </Button>
        </div>
      </aside>
    </div>
  );
}
