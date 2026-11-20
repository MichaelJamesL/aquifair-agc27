"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowRight,
  ChevronDown,
  CircleHelp,
  Download,
  Info,
  MapPin,
} from "lucide-react";
import type { Account, RegionFeatureCollection, TariffTable } from "@/lib/api";
import { api } from "@/lib/api";
import { billionRupiah, mm3, num, percent, rangeMm3, rangeText } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import { RegionMap } from "@/components/neraca/region-map";
import {
  Badge,
  Button,
  CodeTag,
  ErrorBlock,
  InfoNote,
  LabelBadge,
  RangeBar,
  cn,
} from "@/components/neraca/ui";

type Metric = "tax_gap" | "declared" | "estimated" | "share";
type UseGroup = 2 | 3 | 4;

const YEARS = [2020, 2021, 2022, 2023];
const METRICS: { key: Metric; label: string; sub: string }[] = [
  { key: "tax_gap", label: "Tax gap", sub: "Rupiah per year, range" },
  { key: "declared", label: "Declared volume", sub: "m³ from ESDM records" },
  { key: "estimated", label: "Estimated use", sub: "m³, business and household" },
  { key: "share", label: "Declared ÷ estimated", sub: "Share of use that is reported" },
];
const GROUPS: { key: UseGroup; label: string }[] = [
  { key: 4, label: "K4 low" },
  { key: 3, label: "K3 medium" },
  { key: 2, label: "K2 high" },
];

const AMBER_RAMP = ["#fdf0d2", "#f9d48f", "#f2ae52", "#e0812a", "#b5591a"];
const BLUE_RAMP = ["#eef5fb", "#cfe2f3", "#9cc4e4", "#5d9bcc", "#155a96"];

function taxFor(account: Account, group: UseGroup, tariffs: TariffTable[]) {
  const table = tariffs.find((item) => item.wilayah === account.region.wilayah);
  const row = table?.rows.find((item) => item.group === group && item.tier_key === "over_2500");
  if (row?.tax_idr.value != null) return row.tax_idr.value;
  const low = account.tax_per_m3.low ?? 0;
  const high = account.tax_per_m3.high ?? low;
  if (group === 4) return low;
  if (group === 2) return high;
  return (low + high) / 2;
}

function metricValue(account: Account, metric: Metric, group: UseGroup, tariffs: TariffTable[]) {
  if (metric === "declared") return account.declared.value;
  if (metric === "estimated") return account.estimate.central;
  if (metric === "share") {
    const declared = account.declared.value;
    const estimated = account.estimate.central;
    if (declared == null || estimated == null || estimated <= 0) return null;
    return (declared / estimated) * 100;
  }
  const gap = account.gap;
  if (gap.central == null) return null;
  return gap.central * taxFor(account, group, tariffs);
}

function metricRange(account: Account, metric: Metric, group: UseGroup, tariffs: TariffTable[]) {
  if (metric === "tax_gap") {
    const gapMid = account.gap.central;
    const tax = account.tax_per_m3;
    if (gapMid == null || tax.low == null || tax.high == null) return null;
    return {
      low: Math.max(0, gapMid * tax.low),
      high: Math.max(0, gapMid * tax.high),
    };
  }
  if (metric === "declared") {
    if (account.declared.value == null) return null;
    return { low: account.declared.value, high: account.declared.value };
  }
  if (metric === "estimated") {
    if (account.estimate.low == null || account.estimate.high == null) {
      return null;
    }
    return {
      low: account.estimate.low,
      high: account.estimate.high,
    };
  }
  return null;
}

function metricLabel(metric: Metric) {
  if (metric === "tax_gap") return "Tax gap";
  if (metric === "declared") return "Declared volume";
  if (metric === "estimated") return "Estimated use";
  return "Reported share";
}

function metricUnit(metric: Metric) {
  if (metric === "tax_gap") return "bn Rp/yr";
  if (metric === "share") return "%";
  return "Mm³";
}

function valueText(account: Account, metric: Metric, group: UseGroup, tariffs: TariffTable[]) {
  const value = metricValue(account, metric, group, tariffs);
  if (value == null) return "—";
  if (metric === "tax_gap") return billionRupiah(value);
  if (metric === "declared" || metric === "estimated") return mm3(value, 1);
  return percent(value);
}

function exportCsv(accounts: Account[], metric: Metric, group: UseGroup, tariffs: TariffTable[]) {
  const rows = [
    ["region_id", "name", "wilayah", "metric", "value", "low", "high", "label", "estimate_method"],
    ...accounts.map((account) => {
      const value = metricValue(account, metric, group, tariffs);
      const range = metricRange(account, metric, group, tariffs);
      return [
        account.region.id,
        account.region.name,
        account.region.wilayah,
        metricLabel(metric),
        value ?? "",
        range?.low ?? "",
        range?.high ?? "",
        metric === "declared" ? account.declared.label : account.estimate.label,
        metric === "declared" ? "" : (account.estimate_method ?? ""),
      ];
    }),
  ];
  const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `neraca-accounts-${metric}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function AccountsPage() {
  const { role } = useRole();
  const [year, setYear] = useState(2023);
  const [metric, setMetric] = useState<Metric>("declared");
  const [group, setGroup] = useState<UseGroup>(3);
  const [selectedId, setSelectedId] = useState("3374");
  const [showAll, setShowAll] = useState(false);

  const accountsState = useApi(`accounts-${year}-${role}`, (signal) => api.accounts(year, role, signal));
  const geoState = useApi(`geojson-${role}`, (signal) => api.regionGeoJson(role, signal));
  const tariffsState = useApi(`tariffs-${role}`, (signal) =>
    Promise.all(["A", "B", "C"].map((wilayah) => api.tariffs(wilayah, role, signal))),
  );

  const accounts = accountsState.data ?? [];
  const tariffs = tariffsState.data ?? [];
  const geo = geoState.data as RegionFeatureCollection | null;

  const values = useMemo(
    () =>
      accounts
        .map((account) => metricValue(account, metric, group, tariffs))
        .filter((value): value is number => value != null && Number.isFinite(value)),
    [accounts, metric, group, tariffs],
  );
  const maxValue = Math.max(...values, 1);
  // legend ticks in the metric's unit: bn Rp, %, or Mm³
  const legendScale = metric === "tax_gap" ? 1e9 : metric === "share" ? 1 : 1e6;

  const fills = useMemo(() => {
    const ramp = metric === "tax_gap" ? AMBER_RAMP : BLUE_RAMP;
    const result: Record<string, string> = {};
    for (const account of accounts) {
      const value = metricValue(account, metric, group, tariffs);
      if (value == null) {
        result[account.region.id] = "#e8e5dd";
        continue;
      }
      const ratio = maxValue > 0 ? value / maxValue : 0;
      const index = Math.min(ramp.length - 1, Math.max(0, Math.floor(ratio * ramp.length)));
      result[account.region.id] = ramp[index];
    }
    return result;
  }, [accounts, metric, group, tariffs, maxValue]);

  const ranked = useMemo(
    () =>
      [...accounts].sort((a, b) => {
        const av = metricValue(a, metric, group, tariffs);
        const bv = metricValue(b, metric, group, tariffs);
        if (av == null && bv == null) return a.region.name.localeCompare(b.region.name);
        if (av == null) return 1;
        if (bv == null) return -1;
        return bv - av;
      }),
    [accounts, metric, group, tariffs],
  );

  const withValue = ranked.filter((account) => metricValue(account, metric, group, tariffs) != null);
  const total = withValue.reduce(
    (sum, account) => sum + (metricValue(account, metric, group, tariffs) ?? 0),
    0,
  );
  const average = withValue.length ? total / withValue.length : null;
  const selected = accounts.find((account) => account.region.id === selectedId) ?? accounts[0];
  const visible = showAll ? ranked : ranked.slice(0, 10);

  const loading = accountsState.loading && !accounts.length;
  const error = accountsState.error;

  return (
    <div className="grid h-[calc(100vh-56px)] grid-cols-[320px_minmax(0,1fr)_400px] overflow-hidden">
      <aside className="flex min-h-0 flex-col gap-[18px] overflow-y-auto border-r border-line bg-surface px-5 pb-4 pt-5">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[18px] font-semibold leading-6 text-ink">Groundwater accounts</h1>
          <p className="text-[13px] leading-[19px] text-ink-2">
            Declared abstraction vs estimated use per kab/kota, priced with the official
            groundwater price.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <p className="text-[12px] font-medium leading-4 text-ink-2">Year</p>
          <div className="flex rounded-md bg-subtle p-0.5">
            {YEARS.map((item) => (
              <button
                key={item}
                onClick={() => setYear(item)}
                className={cn(
                  "flex h-7 flex-1 items-center justify-center rounded text-[12px]",
                  item === year ? "bg-surface font-medium text-ink" : "text-ink-2",
                )}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <p className="text-[12px] font-medium leading-4 text-ink-2">Map shows</p>
          {METRICS.map((item) => {
            const active = metric === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setMetric(item.key)}
                className={cn(
                  "flex items-start gap-2.5 rounded-md px-2.5 py-2 text-left",
                  active ? "bg-blue-50" : "hover:bg-bg",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 flex size-3.5 shrink-0 items-center justify-center rounded-full border",
                    active ? "border-blue-700" : "border-line-strong",
                  )}
                >
                  {active && <span className="size-1.5 rounded-full bg-blue-700" />}
                </span>
                <span className="flex flex-col">
                  <span className="text-[13px] font-medium leading-[18px] text-ink">
                    {item.label}
                  </span>
                  <span className="text-[12px] leading-4 text-ink-3">{item.sub}</span>
                </span>
              </button>
            );
          })}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-1.5">
            <p className="text-[12px] font-medium leading-4 text-ink-2">Priced as use group</p>
            <CodeTag>NPA</CodeTag>
          </div>
          <div className="flex rounded-md bg-subtle p-0.5">
            {GROUPS.map((item) => (
              <button
                key={item.key}
                onClick={() => setGroup(item.key)}
                className={cn(
                  "flex h-7 flex-1 items-center justify-center rounded px-2 text-[12px]",
                  item.key === group ? "bg-surface font-medium text-ink" : "text-ink-2",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
          <p className="text-[12px] leading-4 text-ink-3">
            Wilayah C, top volume tier, tax 20% of NPA. Rp 11,140 per m³ for K3.
          </p>
        </div>

        <div className="rounded-lg bg-bg p-3">
          <p className="text-[12px] font-medium leading-4 text-ink">
            {metricLabel(metric)} · {metricUnit(metric)}
          </p>
          <div className="mt-2 flex gap-0.5 overflow-hidden rounded-sm">
            {(metric === "tax_gap" ? AMBER_RAMP : BLUE_RAMP).map((colour) => (
              <div key={colour} className="h-2.5 flex-1" style={{ backgroundColor: colour }} />
            ))}
          </div>
          <div className="mt-1.5 flex justify-between font-mono text-[10px] leading-3 text-ink-3">
            <span>0</span>
            <span>{num((maxValue * 0.25) / legendScale, 1)}</span>
            <span>{num((maxValue * 0.5) / legendScale, 1)}</span>
            <span>{num((maxValue * 0.75) / legendScale, 1)}</span>
            <span>{num(maxValue / legendScale, 1)}+</span>
          </div>
        </div>

        <InfoNote icon={<Info size={15} />} tone="gray">
          Every figure is a range. Rows marked “model” use the regency model, which is not
          validated: treat its gap as a reason to look, not a finding. Open a kab/kota to see
          how each number is built.
        </InfoNote>

        <div className="flex-1" />

        <p className="text-[11px] leading-[15px] text-ink-3">
          Declared: Dinas ESDM Jateng open data 2020–23 (CC-BY). Price: Pergub Jateng 7/2025.
          Tax rate: Perda Kota Semarang 10/2023.
        </p>
      </aside>

      <section className="relative min-h-0 overflow-hidden bg-sea">
        <div className="absolute inset-0">
          <RegionMap
            data={geo}
            fills={fills}
            selectedId={selected?.region.id}
            onSelect={setSelectedId}
            className="h-full"
          />
        </div>

        <div className="pointer-events-none absolute left-4 top-4 flex max-w-[510px] items-center gap-2 rounded-lg bg-surface px-3 py-2 shadow-card">
          <Badge tone={metric === "declared" ? "green" : "amber"} dot>
            {metric === "declared" ? "Data" : "Lead"}
          </Badge>
          <p className="text-[12px] leading-4 text-ink-2">
            {metric === "declared"
              ? "Declared volumes are official for all 35 kab/kota."
              : "Kota Semarang uses the validated 16 km estimate. The other 34 use a regency model (BPS population, OSM industrial land) that is not validated."}
          </p>
        </div>

        {selected && (
          <div className="absolute left-4 top-[76px] w-[250px] rounded-xl bg-surface p-3.5 shadow-pop">
            <div className="flex items-center gap-2">
              <p className="text-[14px] font-semibold leading-5 text-ink">{selected.region.name}</p>
              <CodeTag>Wil. {selected.region.wilayah}</CodeTag>
            </div>
            <div className="mt-2.5 space-y-1.5 text-[12px]">
              <div className="flex items-center gap-3">
                <span className="text-ink-3">Declared {selected.year}</span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-ink">
                  {selected.declared.value == null ? "—" : `${mm3(selected.declared.value, 2)} Mm³`}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-ink-3">
                  Estimated use{selected.estimate_method === "regency_model" ? " (model)" : ""}
                </span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-ink">
                  {rangeMm3(selected.estimate, 1)} Mm³
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-ink-3">Tax gap</span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-amber-800">
                  {selected.gap.central == null
                    ? "not estimated"
                    : `${billionRupiah(selected.gap.central * taxFor(selected, group, tariffs))} /yr`}
                </span>
              </div>
            </div>
            <Link
              href={`/accounts/${selected.region.id}`}
              className="mt-2.5 inline-flex items-center gap-1 text-[12px] font-medium text-blue-700"
            >
              Open account <ArrowRight size={14} />
            </Link>
          </div>
        )}

        <div className="pointer-events-none absolute bottom-4 left-4 rounded-md bg-surface px-2.5 py-1.5 font-mono text-[10px] text-ink-3">
          Kab/kota boundaries: geoBoundaries, coast OpenStreetMap · 0&nbsp;&nbsp;50 km
        </div>

        <div className="pointer-events-none absolute bottom-4 right-4 flex items-center gap-1 rounded-md bg-surface px-2.5 py-1.5 font-mono text-[10px] text-ink-3">
          <MapPin size={12} /> 35 kabupaten/kota
        </div>
      </section>

      <aside className="flex min-h-0 flex-col overflow-hidden border-l border-line bg-surface">
        <div className="border-b border-line px-5 pb-3 pt-5">
          <h2 className="text-[18px] font-semibold leading-6 text-ink">
            {metric === "tax_gap" ? "Tax at stake" : metricLabel(metric)}
          </h2>
          <p className="mt-1 text-[12px] leading-4 text-ink-3">
            {withValue.length === accounts.length
              ? `${metric === "share" ? "Average" : "Sum"} over all 35 kab/kota, ${year}${metric === "share" ? "" : ", as a range"}`
              : `Regions with a ${metric === "declared" ? "reported value" : "value"} · ${withValue.length} of ${accounts.length}`}
          </p>
          <div className="mt-3 flex items-baseline gap-2">
            <p className="font-display text-[30px] leading-9 tracking-[-0.6px] text-ink">
              {metric === "tax_gap"
                ? `Rp ${billionRupiah(withValue.length ? total : null)}`
                : metric === "declared" || metric === "estimated"
                  ? `${mm3(total, 1)} Mm³`
                  : percent(average)}
            </p>
            <p className="text-[13px] text-ink-2">
              {metric === "tax_gap" ? "per year" : metric === "share" ? "reported" : metricLabel(metric).toLowerCase()}
            </p>
          </div>
          <p className="mt-1 text-[12px] leading-4 text-ink-2">
            {metric !== "declared"
              ? "Kota Semarang validated; the rest from the regency model, not validated."
              : withValue.length === accounts.length
                ? "All regions have a reported value."
                : "Other regions stay grey in the table and map."}
          </p>
        </div>

        <div className="flex items-center gap-2 bg-bg px-5 py-2">
          <p className="w-[18px] font-mono text-[10px] text-ink-3">#</p>
          <p className="font-mono text-[10px] tracking-[0.6px] text-ink-3">KAB/KOTA</p>
          <span className="flex-1" />
          <p className="font-mono text-[10px] tracking-[0.6px] text-ink-3">
            {metric === "tax_gap" ? "TAX GAP, BN RP/YR" : metricUnit(metric).toUpperCase()}
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {loading && <div className="px-5 py-8 text-[12px] text-ink-3">Loading accounts…</div>}
          {error && (
            <div className="px-5 py-4">
              <ErrorBlock message={error} retry={accountsState.reload} />
            </div>
          )}
          {!loading &&
            !error &&
            visible.map((account, index) => {
              const value = metricValue(account, metric, group, tariffs);
              const range = metricRange(account, metric, group, tariffs);
              const selectedRow = account.region.id === selected?.region.id;
              return (
                <Link
                  key={account.region.id}
                  href={`/accounts/${account.region.id}`}
                  className={cn(
                    "flex items-center gap-2 border-b border-line px-5 py-[9px] text-left hover:bg-bg",
                    selectedRow && "bg-blue-50",
                  )}
                >
                  <p className="w-[18px] font-mono text-[11px] text-ink-3">{index + 1}</p>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 whitespace-nowrap">
                      <p className="truncate text-[13px] font-medium leading-[18px] text-ink">
                        {account.region.name}
                      </p>
                      <p className="font-mono text-[10px] text-ink-3">Wil. {account.region.wilayah}</p>
                    </div>
                    {range ? (
                      <div className="mt-1.5 flex items-center gap-2">
                        <RangeBar
                          low={range.low}
                          high={range.high}
                          ceiling={maxValue}
                          tone={metric === "tax_gap" ? "amber" : "blue"}
                          className="w-[180px]"
                        />
                        {metric !== "declared" && account.estimate_method === "regency_model" && (
                          <p className="font-mono text-[10px] text-amber-800">model</p>
                        )}
                      </div>
                    ) : value == null ? (
                      <p className="mt-1 text-[10px] text-ink-3">not estimated</p>
                    ) : (
                      account.estimate_method === "regency_model" && (
                        <p className="mt-1 font-mono text-[10px] text-amber-800">model</p>
                      )
                    )}
                  </div>
                  <p className="text-right font-display text-[15px] leading-5 text-ink">
                    {valueText(account, metric, group, tariffs)}
                  </p>
                </Link>
              );
            })}
        </div>

        <div className="flex items-center justify-between border-t border-line px-5 py-3">
          <button
            onClick={() => setShowAll((value) => !value)}
            className="inline-flex items-center gap-1 text-[12px] text-blue-700"
          >
            {showAll ? "Show top 10" : "Show all 35"} <ChevronDown size={14} />
          </button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={14} />}
            onClick={() => exportCsv(accounts, metric, group, tariffs)}
          >
            Export table
          </Button>
        </div>
      </aside>
    </div>
  );
}
