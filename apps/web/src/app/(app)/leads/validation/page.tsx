"use client";

import Link from "next/link";
import {
  ArrowRight,
  ClipboardCheck,
  Download,
  FileSearch,
  FlaskConical,
  Info,
} from "lucide-react";
import type { HitRate } from "@/lib/api";
import { api } from "@/lib/api";
import { percent } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import {
  Badge,
  Button,
  Card,
  CodeTag,
  ErrorBlock,
  InfoNote,
  SectionTitle,
  Stat,
} from "@/components/neraca/ui";

const CLASS_ROWS = [
  { key: "factory", label: "Factory" },
  { key: "hotel", label: "Hotel" },
  { key: "mall", label: "Mall" },
  { key: "hospital", label: "Hospital" },
] as const;

const VISIT_LEGEND = [
  { label: "Unregistered well", colour: "#ee9b2f" },
  { label: "Registered", colour: "#155a96" },
  { label: "No well", colour: "#c9c5bb" },
  { label: "On PDAM", colour: "#5d9bcc" },
  { label: "Not visited", colour: "#eceae4" },
];

const ARIZONA_ROWS = [
  { label: "Truth", value: "ADWR Wells 55: install (else approval) date and location" },
  { label: "Signal", value: "IO land cover turns to built in year t (2018–2021), 1,000 m² to 25 ha" },
  { label: "Null", value: "Existing built sites, matched on built share within 1 km" },
  { label: "Pass", value: "At least 1.5× the null share, p < 0.05" },
];

const TABLE_GRID =
  "grid grid-cols-[1.15fr_repeat(6,minmax(0,0.78fr))_0.95fr] items-center gap-2 px-5";

type StatusTone = "green" | "amber" | "red" | "gray" | "blue";

function toneFor(value: string): StatusTone {
  if (value === "done" || value === "pass") return "green";
  if (value === "planned") return "gray";
  if (value === "waiting") return "amber";
  if (value === "fail") return "red";
  return "blue";
}

function classRow(label: string, key: string, hits: HitRate[], leads: number) {
  const hit = hits.find((item) => item.lead_class.toLowerCase() === key);
  const visits = hit?.visits ?? 0;
  const unregistered = hit?.unregistered ?? 0;
  const confirmed = hit?.confirmed_water_user ?? 0;
  return {
    label,
    leads,
    visits,
    unregistered,
    confirmed,
    noWell: visits - unregistered - confirmed,
    rate: hit?.unregistered_rate == null ? null : hit.unregistered_rate * 100,
    interval:
      hit?.interval_90_low == null || hit.interval_90_high == null
        ? "—"
        : `${Math.round(hit.interval_90_low * 100)}–${Math.round(hit.interval_90_high * 100)}%`,
  };
}

export default function LeadsValidationPage() {
  const { role, setRole } = useRole();
  const isInspector = role === "inspector";

  const validationState = useApi(`validation-${role}`, (signal) =>
    api.validation(role, signal),
  );
  const hitRateState = useApi(`hit-rate-${role}`, (signal) =>
    isInspector ? api.hitRate(role, signal) : Promise.resolve([]),
  );
  const summaryState = useApi("leads-public-summary", (signal) => api.leadSummary(signal));

  const checks = validationState.data ?? [];
  const byCode = Object.fromEntries(checks.map((check) => [check.code, check]));
  const hits = isInspector ? (hitRateState.data ?? []) : [];
  const leadCounts: Record<string, number> = {};
  for (const row of summaryState.data?.items ?? []) {
    for (const [key, value] of Object.entries(row.by_use_class)) leadCounts[key] = (leadCounts[key] ?? 0) + value;
  }
  const totalLeads = Object.values(leadCounts).reduce((sum, value) => sum + value, 0);
  const rows = CLASS_ROWS.map((item) => classRow(item.label, item.key, hits, leadCounts[item.key] ?? 0));
  const totalVisits = rows.reduce((sum, row) => sum + row.visits, 0);
  const totalUnregistered = rows.reduce((sum, row) => sum + row.unregistered, 0);
  const totalConfirmed = rows.reduce((sum, row) => sum + row.confirmed, 0);
  const totalRate = totalVisits > 0 ? (100 * totalUnregistered) / totalVisits : null;

  return (
    <div className="mx-auto w-full max-w-[1440px] px-10 pb-14 pt-8">
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="font-display text-[30px] font-medium leading-9 tracking-[-0.5px] text-ink">
            How good are the leads?
          </h1>
          <p className="mt-2 max-w-[800px] text-[13px] leading-[19px] text-ink-2">
            Every visit is recorded. Site by site this builds the registry no open source has, and
            the hit rate shows which lead classes deserve a visit first.
          </p>
        </div>
        <Button
          variant="secondary"
          size="md"
          icon={<Download size={15} />}
          disabled
          title="No visit has been recorded, so there is no registry to export."
        >
          Export registry
        </Button>
      </div>

      {!isInspector && (
        <InfoNote tone="amber" className="mt-4 max-w-[820px]" icon={<Info size={14} />}>
          Field visits and hit rates are inspector-only, so this page shows the public counts and
          stays empty.{" "}
          <button
            type="button"
            className="font-medium underline"
            onClick={() => setRole("inspector")}
          >
            Switch to inspector
          </button>{" "}
          to load them.
        </InfoNote>
      )}

      <div className="mt-5 grid grid-cols-4 gap-4">
        <Stat label="Leads issued" value={String(totalLeads)} sub="Passed all four filters" />
        <Stat label="Visited" value={isInspector ? String(totalVisits) : "—"} sub={isInspector ? "Field visits recorded" : "Inspector only"} />
        <Stat label="Unregistered wells" value={isInspector ? String(totalUnregistered) : "—"} sub="Found on a visit" />
        <Stat label="Hit rate" value={percent(totalRate)} sub="Unregistered ÷ visited" />
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_440px] items-start gap-5">
        <div className="space-y-5">
          <Card padded={false} className="overflow-hidden">
          <div className="px-5 pb-2 pt-5">
            <SectionTitle>Hit rate per lead class</SectionTitle>
            <p className="mt-2 text-[12px] leading-[18px] text-ink-2">
              A hit is an unregistered well found on a visit. Rates stay as a dash until a class
              has at least one visit; they are never filled with a guess.
            </p>
          </div>

          <div className={`${TABLE_GRID} mt-2 bg-bg py-2 font-mono text-[9px] uppercase tracking-[0.4px] text-ink-3`}>
            <span>Class</span>
            <span>Leads</span>
            <span>Visited</span>
            <span>Unregistered</span>
            <span>Reg. / PDAM</span>
            <span>No well</span>
            <span>90% interval</span>
            <span>Hit rate</span>
          </div>

          {rows.map((row) => (
            <div
              key={row.label}
              className={`${TABLE_GRID} border-t border-line py-[11px] text-[12px]`}
            >
              <span className="font-medium text-ink">{row.label}</span>
              <span className="text-ink">{row.leads}</span>
              <span className="text-ink">{row.visits}</span>
              <span className="text-ink">{row.unregistered}</span>
              <span className="text-ink">{row.confirmed}</span>
              <span className="text-ink">{row.noWell}</span>
              <span className="text-ink-3">{row.interval}</span>
              <span
                className={
                  row.rate == null ? "font-medium text-ink-3" : "font-medium text-blue-700"
                }
              >
                {percent(row.rate)}
              </span>
            </div>
          ))}

          <div
            className={`${TABLE_GRID} border-t border-line bg-bg py-[11px] text-[12px] font-medium`}
          >
            <span className="text-ink">All</span>
            <span className="text-ink">{totalLeads}</span>
            <span className="text-ink">{totalVisits}</span>
            <span className="text-ink">{totalUnregistered}</span>
            <span className="text-ink">{totalConfirmed}</span>
            <span className="text-ink">{totalVisits - totalUnregistered - totalConfirmed}</span>
            <span className="text-ink-3">—</span>
            <span className={totalRate == null ? "text-ink-3" : "text-blue-700"}>
              {percent(totalRate)}
            </span>
          </div>

          <div className="border-t border-line px-5 py-4">
            <p className="text-[12px] font-medium leading-4 text-ink">Visits so far</p>
            <div className="mt-3 space-y-2">
              {rows.map((row) => {
                const unregisteredShare =
                  row.visits > 0 ? Math.min(100, (row.unregistered / row.visits) * 100) : 0;
                return (
                  <div key={row.label} className="flex items-center gap-3">
                    <span className="w-[62px] text-[11px] leading-4 text-ink-2">{row.label}</span>
                    <div className="flex h-4 flex-1 gap-[2px] overflow-hidden rounded-[2px]">
                      {row.visits === 0 ? (
                        <div className="h-full flex-1 bg-subtle" />
                      ) : (
                        <>
                          <div
                            className="h-full bg-amber-500"
                            style={{ width: `${unregisteredShare}%` }}
                          />
                          <div className="h-full flex-1 bg-blue-700" />
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-[10px] text-ink-3">
              {VISIT_LEGEND.map((item) => (
                <span key={item.label} className="inline-flex items-center gap-1.5">
                  <span
                    className="size-2 rounded-[2px]"
                    style={{ backgroundColor: item.colour }}
                  />
                  {item.label}
                </span>
              ))}
            </div>

            {isInspector && hitRateState.error && (
              <div className="mt-3">
                <ErrorBlock message={hitRateState.error} retry={hitRateState.reload} />
              </div>
            )}

            <InfoNote tone="gray" className="mt-3">
              Visits start with the first field feedback. Until then every segment is “not
              visited” and the hit rate stays a dash.
            </InfoNote>
          </div>
        </Card>

          <Card>
            <div className="flex items-center gap-2">
              <Info size={15} className="text-blue-700" />
              <p className="text-[12px] font-medium text-ink">How to read a hit rate</p>
            </div>
            <div className="mt-2.5 grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-bg px-3 py-2.5">
                <p className="font-mono text-[9px] uppercase tracking-[0.5px] text-ink-3">
                  Hit rate
                </p>
                <p className="mt-1 font-mono text-[11px] leading-4 text-blue-700">
                  unregistered ÷ visited
                </p>
                <p className="mt-1 text-[11px] leading-[16px] text-ink-2">
                  A class with no visit has no rate. It stays a dash, never 0%.
                </p>
              </div>
              <div className="rounded-lg bg-bg px-3 py-2.5">
                <p className="font-mono text-[9px] uppercase tracking-[0.5px] text-ink-3">
                  Interval
                </p>
                <p className="mt-1 font-mono text-[11px] leading-4 text-ink">90% Wilson</p>
                <p className="mt-1 text-[11px] leading-[16px] text-ink-2">
                  Reported per lead class; wide while the sample is small.
                </p>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <div className="flex items-start gap-2">
              <FlaskConical size={16} className="mt-0.5 shrink-0 text-blue-700" />
              <h2 className="text-[15px] font-semibold leading-5 text-ink">
                Retro test where truth exists: Arizona
              </h2>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5">
              <Badge tone="blue" dot>
                Pre-registered
              </Badge>
              <Badge tone={toneFor(byCode.V4?.result ?? "waiting")} dot className="capitalize">
                V4 {byCode.V4?.status === "done" ? byCode.V4.result : (byCode.V4?.status ?? "planned")}
              </Badge>
            </div>
            <p className="mt-3 text-[12px] leading-[18px] text-ink-2">
              Do new large buildings outside water-provider service areas get a new registered well
              within 500 m in the same or next two years, more often than built-matched buildings?
            </p>
            {byCode.V4?.detail && <p className="mt-2 text-[11px] leading-[16px] text-ink-3">{byCode.V4.detail}</p>}
            <div className="mt-3">
              {ARIZONA_ROWS.map((row) => (
                <div
                  key={row.label}
                  className="grid grid-cols-[60px_minmax(0,1fr)] gap-3 border-t border-line py-2 text-[12px] first:border-t-0"
                >
                  <span className="font-mono text-[10px] leading-4 text-ink-3">{row.label}</span>
                  <span className="leading-4 text-ink-2">{row.value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="flex items-start gap-2">
              <ClipboardCheck size={16} className="mt-0.5 shrink-0 text-blue-700" />
              <h2 className="text-[15px] font-semibold leading-5 text-ink">
                Validation in Semarang
              </h2>
            </div>
            <div className="mt-2.5 flex items-center gap-1.5">
              <Badge tone={toneFor(byCode.V5?.result ?? "waiting")} dot className="capitalize">
                V5 {byCode.V5?.result ?? "waiting"}
              </Badge>
            </div>
            <p className="mt-2 text-[12px] leading-[18px] text-ink-2">
              V5 asks whether leads sit on the official map&apos;s permitted wells (and Lo et al. 2022) more
              often than size-matched new buildings. V6 is the field hit rate per class.
            </p>
            {byCode.V5?.detail && <p className="mt-2 text-[11px] leading-[16px] text-ink-3">{byCode.V5.detail}</p>}
            <div className="mt-4 flex items-center gap-3">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-subtle">
                <div
                  className="h-full rounded-full bg-blue-700"
                  style={{ width: `${totalLeads ? Math.min(100, (100 * totalVisits) / totalLeads) : 0}%` }}
                />
              </div>
              <span className="whitespace-nowrap font-mono text-[10px] text-ink-3">
                {isInspector ? `${totalVisits} visits for ${totalLeads} leads` : `${totalLeads} leads`}
              </span>
            </div>
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              icon={<FileSearch size={14} />}
              title="Registry requests go through PPID outside this app; this build does not send them."
            >
              Request registry via PPID
            </Button>
          </Card>

          <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
            <p className="text-[13px] font-semibold leading-[18px] text-ink">What is not a lead</p>
            <div className="mt-3 space-y-2.5">
              <div className="flex gap-2">
                <Info size={14} className="mt-0.5 shrink-0 text-blue-700" />
                <p className="text-[11px] leading-[17px] text-ink-2">
                  Sites already self-supplied before 2022 are not new. Groundwater accounts
                  already cover them as declared volume.
                </p>
              </div>
              <div className="flex gap-2">
                <Info size={14} className="mt-0.5 shrink-0 text-blue-700" />
                <p className="text-[11px] leading-[17px] text-ink-2">
                  The PDAM network map is not public. Until PDAM shares coverage per village,
                  filter 4 uses piped coverage per district (BPS 2024, Demak open-data portal 2025).
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Card padded={false} className="mt-5 overflow-hidden">
        <div className="flex items-start justify-between gap-4 px-5 py-4">
          <div>
            <h2 className="text-[18px] font-semibold leading-6 text-ink">
              Validation checks V1–V8
            </h2>
            <p className="mt-1 text-[12px] leading-[17px] text-ink-3">
              The pre-registered checks that decide whether the method holds. Pass marks are fixed
              before the test runs.
            </p>
          </div>
          <Link
            href="/methods"
            className="mt-0.5 inline-flex shrink-0 items-center gap-1 text-[12px] font-medium text-blue-700"
          >
            Full methods <ArrowRight size={13} />
          </Link>
        </div>

        <div className="grid grid-cols-[44px_180px_48px_minmax(0,1fr)_84px_84px] items-center gap-3 border-y border-line bg-bg px-5 py-2 font-mono text-[9px] uppercase tracking-[0.5px] text-ink-3">
          <span>Code</span>
          <span>Check</span>
          <span>Mod</span>
          <span>Pass mark</span>
          <span>Status</span>
          <span>Result</span>
        </div>

        {validationState.loading && !checks.length && (
          <p className="px-5 py-8 text-[12px] text-ink-3">Loading validation checks…</p>
        )}

        {validationState.error && (
          <div className="px-5 py-4">
            <ErrorBlock message={validationState.error} retry={validationState.reload} />
          </div>
        )}

        {checks.map((check) => (
          <div
            key={check.code}
            className="grid grid-cols-[44px_180px_48px_minmax(0,1fr)_84px_84px] items-start gap-3 border-t border-line px-5 py-[11px] first:border-t-0"
          >
            <CodeTag>{check.code}</CodeTag>
            <p className="text-[12px] font-medium leading-4 text-ink">{check.name}</p>
            <CodeTag>{check.module}</CodeTag>
            <p className="text-[11px] leading-[16px] text-ink-2">
              {check.pass_mark}
              {check.detail && <span className="mt-1 block text-ink">{check.detail}</span>}
            </p>
            <Badge tone={toneFor(check.status)} dot className="capitalize">
              {check.status}
            </Badge>
            <Badge tone={toneFor(check.result)} dot className="capitalize">
              {check.result}
            </Badge>
          </div>
        ))}

        {!validationState.loading && !validationState.error && checks.length === 0 && (
          <p className="px-5 py-8 text-[12px] text-ink-3">
            The backend returned no validation checks.
          </p>
        )}
      </Card>
    </div>
  );
}
