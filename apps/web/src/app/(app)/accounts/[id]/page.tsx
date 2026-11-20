"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Download,
  Droplets,
  Info,
  Landmark,
} from "lucide-react";
import type { Account, AccountYear, TariffTable } from "@/lib/api";
import { api } from "@/lib/api";
import { billionRupiah, mm3, num, percent, rangeMm3, rangeText } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import {
  Badge,
  Button,
  Card,
  CodeTag,
  ErrorBlock,
  InfoNote,
  LabelBadge,
  RangeBar,
  SectionTitle,
  Stat,
  cn,
} from "@/components/neraca/ui";

const PERDA_SERIES = [
  { label: "2003–06", value: 20, range: "15–25" },
  { label: "2016", value: 13.1, range: null },
  { label: "2017", value: 15.5, range: null },
  { label: "2018", value: 27.7, range: null },
  { label: "2019", value: 13.8, range: null },
];

// Base water price (HAB) per price area, Central Java Governor Regulation 7/2025; the tariff API returns NPA rows, not HAB.
const HAB: Record<string, number> = { A: 2561, B: 2795, C: 2824 };

const PDAM_SALES = [
  { label: "Households", value: 41.63, width: "81%" },
  { label: "Niaga (business)", value: 4.35, width: "9%" },
  { label: "Industry", value: 0.22, width: "1%" },
];

function gapTaxRange(account: Account) {
  const gapMid = account.gap.central;
  const tax = account.tax_per_m3;
  if (gapMid == null || tax.low == null || tax.high == null) {
    return null;
  }
  return {
    low: Math.max(0, gapMid * tax.low),
    high: Math.max(0, gapMid * tax.high),
  };
}

function historyBars(history: AccountYear[] | null, withPerda: boolean) {
  const fromApi = (history ?? [])
    .filter((point) => point.declared.value != null)
    .map((point) => ({
      label: String(point.year),
      value: (point.declared.value ?? 0) / 1_000_000,
      range: null as string | null,
    }));
  return withPerda ? [...PERDA_SERIES, ...fromApi] : fromApi;
}

function PriceTable({ table }: { table: TariffTable | null }) {
  if (!table) return <div className="py-6 text-[12px] text-ink-3">Loading price table…</div>;
  const groups = [1, 2, 3, 4, 5];
  return (
    <div className="mt-4 overflow-hidden rounded-lg border border-line">
      <div className="grid grid-cols-[1fr_78px_86px_78px] bg-bg px-3 py-2 font-mono text-[10px] tracking-[0.4px] text-ink-3">
        <span>GROUP</span>
        <span>0–50 m³</span>
        <span>&gt;2,500 m³</span>
        <span>TAX 20%</span>
      </div>
      {groups.map((group) => {
        const first = table.rows.find((row) => row.group === group && row.tier_key === "0_50");
        const last = table.rows.find((row) => row.group === group && row.tier_key === "over_2500");
        if (!first || !last) return null;
        return (
          <div
            key={group}
            className="grid grid-cols-[1fr_78px_86px_78px] border-t border-line px-3 py-2 text-[12px]"
          >
            <span className="text-ink">
              {first.group_name} {first.group === 1 ? "water as product" : ""}
              {first.group === 2 ? "high-risk business" : ""}
              {first.group === 3 ? "medium-risk business" : ""}
              {first.group === 4 ? "low-risk business" : ""}
              {first.group === 5 ? "social / govt / BUMD" : ""}
            </span>
            <span className="text-ink-2">{num(first.npa_idr.value, 0)}</span>
            <span className="text-ink-2">{num(last.npa_idr.value, 0)}</span>
            <span className="font-medium text-ink">{num(last.tax_idr.value, 0)}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function AccountDetailPage() {
  const params = useParams<{ id: string }>();
  const regionId = params.id;
  const { role } = useRole();
  const accountState = useApi(`account-${regionId}-${role}`, (signal) =>
    api.account(regionId, role, signal),
  );
  const historyState = useApi(`history-${regionId}-${role}`, (signal) =>
    api.accountHistory(regionId, role, signal),
  );
  const billingState = useApi(`billing-${regionId}-${role}`, (signal) =>
    api.billingCheck(regionId, role, signal),
  );
  const tariffsState = useApi(`tariffs-${role}`, (signal) =>
    Promise.all(["A", "B", "C"].map((wilayah) => api.tariffs(wilayah, role, signal))),
  );

  const account = accountState.data;
  if (accountState.loading && !account) {
    return (
      <div className="mx-auto max-w-[1360px] px-10 py-10">
        <div className="h-[400px] animate-pulse rounded-xl bg-subtle" />
      </div>
    );
  }
  if (accountState.error || !account) {
    return (
      <div className="mx-auto max-w-[760px] px-10 py-16">
        <ErrorBlock
          message={accountState.error ?? "Account not found"}
          retry={accountState.reload}
        />
      </div>
    );
  }

  const table =
    tariffsState.data?.find((item) => item.wilayah === account.region.wilayah) ?? null;
  const gapTax = gapTaxRange(account);
  const gapTaxText = gapTax
    ? `Rp ${num(gapTax.low / 1_000_000_000, 0)}–${num(gapTax.high / 1_000_000_000, 0)}`
    : "—";
  const semarang = account.region.id === "3374"; // the Bylaw, PDAM and validated figures are Semarang City's
  const model = account.estimate_method === "regency_model";
  const history = historyBars(historyState.data, semarang);
  const maxHistory = Math.max(...history.map((point) => point.value), 1);
  const estimatedHigh = account.estimate.high ?? 0;
  const declared = account.declared.value ?? 0;
  const gapHigh = Math.max(0, account.gap.high ?? 0);
  const declaredWidth = estimatedHigh > 0 ? Math.min(100, (declared / estimatedHigh) * 100) : 0;
  const gapWidth = estimatedHigh > 0 ? Math.min(100, (gapHigh / estimatedHigh) * 100) : 0;
  const billing = billingState.data;

  return (
    <div className="mx-auto w-full max-w-[1440px] px-10 pb-14 pt-8">
      <div className="flex items-center gap-2 text-[12px] text-ink-3">
        <Link href="/accounts" className="inline-flex items-center gap-1 text-ink-2 hover:text-ink">
          <ArrowLeft size={14} /> Accounts
        </Link>
        <span>/</span>
        <span>Central Java</span>
        <span>/</span>
        <span className="text-ink">{account.region.name}</span>
      </div>

      <div className="mt-5 flex items-start justify-between gap-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-display text-[34px] font-medium leading-10 tracking-[-0.5px] text-ink">
              {account.region.name}
            </h1>
            <CodeTag>Area {account.region.wilayah}</CodeTag>
            <LabelBadge label={account.estimate.label} />
          </div>
          <p className="mt-2 max-w-[760px] text-[13px] leading-[19px] text-ink-2">
            Groundwater account for {account.year}. Declared abstraction from the ESDM office,
            estimated use from{" "}
            {model ? "a regency model that is not validated" : "the validated 16 km split"}, priced
            with Central Java Governor Regulation 7/2025.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Link href="/accounts/asean">
            <Button variant="secondary" size="md" icon={<Landmark size={15} />}>
              Compare cities
            </Button>
          </Link>
          <Button
            variant="primary"
            size="md"
            icon={<Download size={15} />}
            onClick={() => window.print()}
          >
            Export account
          </Button>
        </div>
      </div>

      <div className="mt-7 grid grid-cols-4 gap-4">
        <Stat
          label={`Declared ${account.year}`}
          value={account.declared.value == null ? "—" : mm3(account.declared.value, 2)}
          unit="Mm³"
          sub="ESDM records"
          badge={<LabelBadge label={account.declared.label} />}
        />
        <Stat
          label={model ? "Estimated use · model" : "Estimated use · validated"}
          value={rangeMm3(account.estimate, 1)}
          unit="Mm³"
          sub={model ? "households + business, not validated" : "16 km split, P10–P90"}
          badge={<LabelBadge label={account.estimate.label} />}
        />
        <Stat
          label="Taxable gap"
          value={rangeMm3(account.gap, 1)}
          unit="Mm³"
          sub={
            model && account.gap.high === 0
              ? "none visible: declared is above the model"
              : "estimated minus exempt and declared"
          }
          badge={<LabelBadge label={account.gap.label} />}
        />
        <Stat
          label="Tax gap"
          value={gapTaxText}
          unit="bn Rp per year"
          sub="midpoint gap × tax band"
          badge={<LabelBadge label="CALCULATED" />}
        />
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_460px] items-start gap-5">
        <div className="space-y-5">
          <Card>
            <SectionTitle right={<LabelBadge label="CALCULATED" />}>
              Declared vs estimated
            </SectionTitle>
            <p className="mt-3 max-w-[800px] text-[12px] leading-[18px] text-ink-2">
              The bar puts the declared volume against the {model ? "modelled" : "validated"}{" "}
              estimate. The gap is the difference after exempt household wells and public supply
              wells are removed.
            </p>
            {model && (
              <div className="mt-3 space-y-2 rounded-lg border border-line bg-bg p-3 text-[12px] leading-[18px] text-ink-2">
                <p>{account.estimate.note}</p>
                <p>{account.gap.note}</p>
              </div>
            )}
            <div className="mt-5 flex h-9 overflow-hidden rounded-md">
              <div className="bg-blue-700" style={{ width: `${declaredWidth}%` }} />
              <div className="bg-amber-400" style={{ width: `${gapWidth}%` }} />
              <div className="flex-1 bg-blue-100" />
            </div>
            <div className="mt-2 flex items-center justify-between font-mono text-[10px] text-ink-3">
              <span>0</span>
              <span>{num(estimatedHigh / 2_000_000, 0)}</span>
              <span>{num(estimatedHigh / 1_000_000, 0)} Mm³</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-[11px] text-ink-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-[2px] bg-blue-700" />
                Declared, business ({mm3(declared, 1)})
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-[2px] bg-amber-400" />
                Taxable gap, high end ({mm3(gapHigh, 1)})
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-[2px] bg-blue-100" />
                Above declared + gap, if any
              </span>
            </div>
          </Card>

          {semarang && (
          <Card>
            <SectionTitle>Where the gap comes from</SectionTitle>
            <p className="mt-3 text-[12px] leading-[18px] text-ink-2">
              The app never prints one “lost revenue” number. The gap mixes three things, each
              with its own evidence.
            </p>
            <div className="mt-5 grid grid-cols-3 gap-4">
              {[
                {
                  n: "1",
                  badge: "Not tax",
                  tone: "gray" as const,
                  title: "Real decline in pumping",
                  body:
                    "Registered volume was 15–25 Mm³ in 2003–06 and about 10 Mm³ in 2022–23. Part of the drop is real: PDAM supply grew and some factories closed.",
                },
                {
                  n: "2",
                  badge: "Taxable",
                  tone: "amber" as const,
                  title: "Under-reporting by permit holders",
                  body:
                    "Registered volume jumped from 15.5 to 27.7 Mm³ (2017→2018) and fell to 13.8 Mm³ a year later. Meters and self-reports are noisy.",
                },
                {
                  n: "3",
                  badge: "Taxable",
                  tone: "amber" as const,
                  title: "Unregistered wells",
                  body:
                    "In West Java, about 200 of at least 6,000 well points have a permit. Inspection leads point to new large users without one.",
                },
              ].map((item) => (
                <div key={item.n} className="rounded-lg border border-line bg-bg p-4">
                  <div className="flex items-center gap-2">
                    <span className="flex size-5 items-center justify-center rounded-full border border-line-strong font-mono text-[11px] text-ink-2">
                      {item.n}
                    </span>
                    <Badge tone={item.tone} dot>
                      {item.badge}
                    </Badge>
                  </div>
                  <p className="mt-3 text-[13px] font-medium leading-[18px] text-ink">{item.title}</p>
                  <p className="mt-2 text-[12px] leading-[17px] text-ink-2">{item.body}</p>
                </div>
              ))}
            </div>
          </Card>
          )}

          <Card>
            <SectionTitle>Registered abstraction, {account.region.name} (Mm³)</SectionTitle>
            <div className="mt-5 flex h-[150px] items-end gap-5">
              {history.map((point) => (
                <div key={point.label} className="flex flex-1 flex-col items-center">
                  {point.range && (
                    <span className="mb-1 font-mono text-[10px] text-ink-3">{point.range}</span>
                  )}
                  <span className="mb-1 text-[10px] text-ink-2">{num(point.value, 2)}</span>
                  <div
                    className="w-full max-w-[54px] rounded-t-[2px] bg-blue-700"
                    style={{ height: `${Math.max(6, (point.value / maxHistory) * 108)}px` }}
                  />
                  <span className="mt-1 font-mono text-[10px] text-ink-3">{point.label}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] leading-[16px] text-ink-3">
              {semarang
                ? "Year-to-year swings show the declared series is itself noisy. Semarang City Bylaw 2024 for 2003–19; ESDM open data 2020–23."
                : "ESDM open data 2020–23. Years with no declared volume are left out."}
            </p>
          </Card>

          <Card>
            <SectionTitle
              right={
                <Badge
                  tone={billing?.check.result === "pass" ? "green" : billing?.check.result === "fail" ? "red" : "amber"}
                  dot
                >
                  {billing?.check.status === "done" ? `V1 ${billing.check.result}` : "Waiting for data"}
                </Badge>
              }
            >
              First check: is billing leaking?
            </SectionTitle>
            <p className="mt-3 max-w-[800px] text-[12px] leading-[18px] text-ink-2">
              Realised groundwater tax divided by declared volume gives the rupiah actually
              collected per m³. If it sits far below the price table, metering or billing leaks
              before any unregistered well is counted. No satellite data needed.
            </p>
            <div className="mt-5 grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-3">
              <div className="rounded-lg border border-line bg-bg p-4">
                <p className="text-[12px] text-ink-2">Tax realised, {billing?.year ?? account.year}</p>
                <p className="mt-2 font-display text-[22px] text-ink">
                  {billing?.realised_tax.value == null ? "—" : `Rp ${num(billing.realised_tax.value / 1e9, 2)} bn`}
                </p>
                <p className="mt-1 text-[11px] text-ink-3">
                  {billing?.realised_tax.source_ids.join(", ") || "APBD realisation not obtained"}
                </p>
              </div>
              <span className="text-[20px] text-ink-3">÷</span>
              <div className="rounded-lg border border-line bg-bg p-4">
                <p className="text-[12px] text-ink-2">Declared volume</p>
                <p className="mt-2 font-display text-[22px] text-ink">
                  {mm3(billing?.declared_volume.value ?? account.declared.value, 2)} Mm³
                </p>
                <p className="mt-1 text-[11px] text-ink-3">{billing?.year ?? account.year}, ESDM</p>
              </div>
              <span className="text-[20px] text-ink-3">=</span>
              <div className="rounded-lg border border-line bg-bg p-4">
                <p className="text-[12px] text-ink-2">Implied tax</p>
                <p className="mt-2 font-display text-[22px] text-ink">
                  {billing?.implied_tax_per_m3.value == null ? "—" : `Rp ${num(billing.implied_tax_per_m3.value)}`}/m³
                </p>
                <p className="mt-1 text-[11px] text-ink-3">
                  band {billing ? rangeText(billing.expected_band, 0) : "—"} Rp/m³
                </p>
              </div>
            </div>
            {billing && billing.history.length > 0 && (
              <table className="mt-4 w-full text-[12px]">
                <thead>
                  <tr className="border-b border-line text-left text-[11px] text-ink-3">
                    <th className="py-1.5 font-medium">Year</th>
                    <th className="py-1.5 font-medium">Realised tax</th>
                    <th className="py-1.5 font-medium">Declared</th>
                    <th className="py-1.5 font-medium">Rp/m³</th>
                    <th className="py-1.5 font-medium">Band (20% of NPA, groups 2–4)</th>
                    <th className="py-1.5 font-medium">Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {billing.history.map((row) => (
                    <tr key={row.year} className="border-b border-line align-top last:border-b-0">
                      <td className="py-2 font-mono text-ink">{row.year}</td>
                      <td className="py-2 text-ink">
                        {row.realised_tax.value == null ? "—" : `Rp ${num(row.realised_tax.value / 1e9, 2)} bn`}
                      </td>
                      <td className="py-2 text-ink">{mm3(row.declared_volume.value, 2)} Mm³</td>
                      <td className="py-2 font-medium text-ink">{num(row.implied_tax_per_m3.value)}</td>
                      <td className="py-2 text-ink-2">
                        {rangeText(row.expected_band, 0)}
                        <span className="block text-[10px] text-ink-3">{row.regulation}</span>
                      </td>
                      <td className="py-2 text-[11px] text-ink-2">{row.outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <p className="mt-4 text-[11px] leading-[16px] text-ink-3">{billing?.note}</p>
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <div className="flex items-center gap-2">
              <SectionTitle>Groundwater price (NPA)</SectionTitle>
              <CodeTag>Governor Regulation 7/2025</CodeTag>
            </div>
            <p className="mt-3 text-[12px] leading-[18px] text-ink-2">
              Price area {account.region.wilayah}, good quality, alternative source exists (table 3a).
              NPA = HAB × BAT, HAB Rp {num(HAB[account.region.wilayah], 0)} per m³.
            </p>
            <PriceTable table={table} />
            <p className="mt-3 text-[11px] leading-[16px] text-ink-3">
              Rp per m³. Five volume tiers; only the first and last are shown. The price area C annex
              prints its P column with an apparent typo, so the NPA column is used as printed.
            </p>
          </Card>

          {semarang && (
          <Card>
            <SectionTitle>Who pumps</SectionTitle>
            <div className="mt-4 flex items-baseline gap-3">
              <p className="font-display text-[34px] leading-9 text-blue-700">96%</p>
              <p className="text-[12px] leading-[17px] text-ink-2">
                of registered abstraction is industrial
              </p>
            </div>
            <p className="mt-4 text-[12px] text-ink-2">
              PDAM sales by user group, 2022 (of 51.66 Mm³ distributed)
            </p>
            <div className="mt-3 space-y-3">
              {PDAM_SALES.map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <span className="w-[110px] text-[12px] text-ink-2">{item.label}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-subtle">
                    <div className="h-full rounded-full bg-blue-700" style={{ width: item.width }} />
                  </div>
                  <span className="w-[36px] text-right font-mono text-[11px] text-ink-2">
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-[11px] leading-[16px] text-ink-3">
              Industry runs almost entirely on its own wells. PDAM covers 62% of domestic demand
              and itself takes about 19% of its supply from deep groundwater.
            </p>
          </Card>
          )}

          <Card>
            <SectionTitle>What the gap is worth</SectionTitle>
            <div className="mt-4 space-y-3 text-[12px]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-2">Tax per 1 Mm³ undeclared business use</span>
                <span className="font-medium text-ink">
                  {/* tax_per_m3 is Rp per m³; the row is per 1 Mm³ */}
                  Rp {billionRupiah(account.tax_per_m3.low === null ? null : account.tax_per_m3.low * 1_000_000)}–
                  {billionRupiah(account.tax_per_m3.high === null ? null : account.tax_per_m3.high * 1_000_000)}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-2">Taxable gap, range</span>
                <span className="font-medium text-ink">{rangeMm3(account.gap, 1)} Mm³</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-2">Tax gap, range</span>
                <span className="font-medium text-amber-800">
                  {gapTax ? `${gapTaxText} bn/yr` : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-ink-2">Declared tax base</span>
                <span className="font-medium text-ink">
                  Rp {billionRupiah(account.declared_tax_base.low)}–
                  {billionRupiah(account.declared_tax_base.high)}
                </span>
              </div>
            </div>
            <InfoNote tone="amber" icon={<AlertTriangle size={14} />} className="mt-4">
              Household exemption is from a secondary source. Check the UU 1/2022 article before
              leaving households out of the rupiah figure.
            </InfoNote>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <Info size={15} className="text-blue-700" />
              <p className="text-[12px] font-medium text-ink">What this page does not say</p>
            </div>
            <p className="mt-2 text-[11px] leading-[17px] text-ink-2">
              The gap is a range, not a finding.{" "}
              {model
                ? "This regency or city has no validated estimate: the regency model scales Semarang City's industrial rate by mapped industrial land, and moving models between places has been off by 5–27× elsewhere."
                : "The estimate is validated only at 16 km; it does not identify individual wells."}{" "}
              The declared series is itself noisy.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
