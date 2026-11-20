"use client";

import Link from "next/link";
import { useMemo, type ReactNode } from "react";
import {
  AlertTriangle,
  Droplets,
  FileText,
  Info,
  Waves,
} from "lucide-react";
import { api } from "@/lib/api";
import { mm3, num } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import { OverlayMap, type OverlayLayer } from "@/components/neraca/overlay-map";
import {
  Badge,
  Button,
  Card,
  ErrorBlock,
  InfoNote,
} from "@/components/neraca/ui";

const SERVED = ["Semarang Barat", "Tugu", "Ngaliyan"];
const PLACEBO = ["Genuk", "Pedurungan", "Gayamsari"];
const BOUNDS: [[number, number], [number, number]] = [
  [110.27, -7.15],
  [110.52, -6.92],
];

const CITIES = [
  {
    city: "Bangkok",
    fact: "Charge + pipes + ban where pipes exist. Sinking down to about 0–1 cm/yr.",
  },
  {
    city: "Ho Chi Minh City",
    fact: "716,581 → 252,528 m³/day by end 2024 as SAWACO sealed wells.",
  },
  {
    city: "Jakarta",
    fact: "Pergub 93/2021 bans groundwater for large buildings in nine zones and 12 road segments from Aug 2023.",
  },
];

const CAVEATS = [
  "Clay in the west is thinner (about 20 m), so there is less room to slow.",
  "Connections ramped up from 2022 to 2024, not on one date.",
  "We do not know if new customers used groundwater before.",
];

function signed(value: number | null | undefined, digits = 1) {
  if (value == null) return "—";
  return `${value > 0 ? "+" : ""}${num(value, digits)}`;
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-6 py-2 text-[12px] leading-4">
      <dt className="shrink-0 text-ink-3">{label}</dt>
      <dd className="text-right font-medium text-ink">{value}</dd>
    </div>
  );
}

export default function SpamTestPage() {
  const { role } = useRole();
  const spamState = useApi(`spam-test-${role}`, (signal) => api.spamTest(role, signal));
  const periodsState = useApi(`pipe-periods-${role}`, (signal) =>
    api.pipePeriods(role, signal),
  );
  const coverageState = useApi("map-pdam-coverage", (signal) => api.pdamCoverage(signal));
  const overlays = useMemo<OverlayLayer[]>(() => {
    const features = (coverageState.data?.geojson.features ?? [])
      .filter((feature) => feature.properties.regency === "Kota Semarang")
      .map((feature) => ({
        ...feature,
        properties: {
          ...feature.properties,
          group: SERVED.includes(feature.properties.kecamatan)
            ? "served"
            : PLACEBO.includes(feature.properties.kecamatan)
              ? "placebo"
              : "other",
        },
      }));
    return [
      {
        id: "kecamatan",
        data: { type: "FeatureCollection", features } as GeoJSON.FeatureCollection,
        layers: [
          {
            id: "kecamatan-fill",
            type: "fill",
            paint: {
              "fill-color": ["match", ["get", "group"], "served", "#5d9bcc", "placebo", "#f59e0b", "#f7f5ef"] as never,
              "fill-opacity": 0.55,
            },
          },
          { id: "kecamatan-line", type: "line", paint: { "line-color": "#1e3a5f", "line-width": 0.7 } },
        ],
      },
    ];
  }, [coverageState.data]);

  const spam = spamState.data;
  const periods = periodsState.data ?? [];
  const fast2018 = periods.find((period) => period.key === "2018_22")?.fast_mm_yr;
  const fast2023 = periods.find((period) => period.key === "2023_26")?.fast_mm_yr;
  const designMm3 =
    spam?.design_capacity_lps == null
      ? null
      : (spam.design_capacity_lps * 31_536) / 1_000_000;
  const absorbedText =
    spam?.uptake_lps_2024_01 == null && spam?.uptake_m3_yr_2024 == null
      ? "—"
      : `${spam?.uptake_lps_2024_01 == null ? "—" : `${num(spam.uptake_lps_2024_01)} L/s`} · ${
          spam?.uptake_m3_yr_2024 == null
            ? "—"
            : `about ${mm3(spam.uptake_m3_yr_2024, 0)} Mm³/yr`
        }`;
  const connectionsText =
    spam?.connections_actual_2024_09 == null && spam?.connections_target == null
      ? "—"
      : `${spam?.connections_actual_2024_09 == null ? "—" : `${num(spam.connections_actual_2024_09)} now`} · ${
          spam?.connections_target == null
            ? "—"
            : `${num(spam.connections_target)} target`
        }`;
  const statusLabel = spam?.status ? spam.status.replaceAll("_", " ") : "not run";
  const served = {
    before: spam?.served_mean_mm_yr?.["2018_22"] ?? 0,
    after: spam?.served_mean_mm_yr?.["2023_26"] ?? 0,
  };
  const control = {
    before: spam?.control_mean_mm_yr?.["2018_22"] ?? 0,
    after: spam?.control_mean_mm_yr?.["2023_26"] ?? 0,
  };

  return (
    <div className="mx-auto w-full max-w-[1440px] px-10 pb-14 pt-8">
      <div className="flex items-start justify-between gap-6">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="font-display text-[30px] font-medium leading-9 tracking-[-0.5px] text-ink">
              Did sinking slow where pipe water arrived?
            </h1>
            <Badge tone="blue" dot>
              Pre-registered
            </Badge>
            <Badge tone={spam?.status === "pass" ? "green" : spam?.status === "not_run" ? "gray" : "amber"} dot>
              {spam?.status === "not_run" ? "Result pending" : `Result: ${spam?.status ?? "…"}`}
            </Badge>
          </div>
          <p className="mt-2 max-w-[760px] text-[13px] leading-[19px] text-ink-2">
            SPAM Semarang Barat brought reservoir water to the west of the city from
            January 2024. If pipes replace pumps, sinking there should slow more than in
            similar places without new supply.
          </p>
          <p className="mt-1.5 text-[11px] leading-4 text-ink-3">
            Test status: <span className="font-mono">{statusLabel}</span>
            {spam?.run_date ? ` · run ${spam.run_date} under the pre-registration` : ""}
            {spam?.preregistration ? <span className="font-mono"> ({spam.preregistration})</span> : null}
          </p>
        </div>
        <Link href="/methods#tests">
          <Button variant="secondary" size="md" icon={<FileText size={15} />}>
            Read the protocol
          </Button>
        </Link>
      </div>

      <div className="mt-6 grid grid-cols-[minmax(0,0.96fr)_minmax(0,1.04fr)] items-start gap-5">
        <div className="space-y-5">
          <Card padded={false} className="overflow-hidden">
            <div className="relative h-[520px] bg-sea">
              <OverlayMap overlays={overlays} bounds={BOUNDS} />
              <div className="pointer-events-none absolute left-4 top-4 rounded-md bg-surface/95 px-2.5 py-1.5 shadow-card">
                <p className="text-[11px] font-medium leading-4 text-ink">Kota Semarang, kecamatan</p>
                <p className="text-[10px] leading-[14px] text-ink-3">
                  Served in the west, placebo area in the east
                </p>
              </div>
              <p className="pointer-events-none absolute bottom-3 left-4 right-14 rounded-md bg-surface/90 px-2.5 py-1.5 text-[10px] leading-[14px] text-ink-3">
                The SPAM service map is not public, so the three kecamatan named by the government
                stand in for it (risk R4). Controls are all other 200 m cells with similar clay and
                built-up share.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-line px-4 py-3 text-[11px] text-ink-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-[2px] bg-blue-400" />
                Service area: Tugu, Semarang Barat, Ngaliyan
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-[2px] border border-amber-500 bg-amber-100" />
                Placebo area: Genuk, Pedurungan, Gayamsari
              </span>
            </div>
          </Card>

          <Card>
            <h2 className="text-[15px] font-semibold leading-5 text-ink">
              Cities that swapped pumps for pipes
            </h2>
            <div className="mt-3 divide-y divide-line">
              {CITIES.map((item) => (
                <div
                  key={item.city}
                  className="grid grid-cols-[132px_minmax(0,1fr)] gap-4 py-2.5 text-[12px] leading-[17px]"
                >
                  <p className="font-medium text-ink">{item.city}</p>
                  <p className="text-ink-2">{item.fact}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[10.5px] leading-[15px] text-ink-3">
              Comparators only. None is used as evidence for Semarang.
            </p>
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-[18px] font-semibold leading-6 text-ink">
                The test: difference in differences
              </h2>
              <Badge tone={spam?.status === "pass" ? "green" : "amber"} dot>
                {statusLabel}
              </Badge>
            </div>
            <p className="mt-1 text-[12px] leading-4 text-ink-3">
              Change in sinking rate, 2023–26 minus 2018–22, mm/yr
            </p>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-blue-50 p-3.5">
                <p className="text-[12px] font-medium leading-4 text-blue-700">
                  Service area
                </p>
                <p className="mt-4 font-display text-[24px] leading-7 text-ink">
                  Δ = {signed(served.after - served.before)}
                </p>
                <p className="mt-1.5 font-mono text-[9.5px] leading-3 text-ink-3">
                  {num(served.before, 1)} → {num(served.after, 1)} mm/yr · {num(spam?.served_cells ?? 0)} cells
                </p>
              </div>
              <div className="rounded-lg bg-amber-50 p-3.5">
                <p className="text-[12px] font-medium leading-4 text-amber-800">
                  All other cells (raw)
                </p>
                <p className="mt-4 font-display text-[24px] leading-7 text-ink">
                  Δ = {signed(control.after - control.before)}
                </p>
                <p className="mt-1.5 font-mono text-[9.5px] leading-3 text-ink-3">
                  {num(control.before, 1)} → {num(control.after, 1)} mm/yr
                </p>
              </div>
            </div>

            <div className="mt-3 rounded-lg border border-line bg-bg px-3 py-2.5">
              <div className="flex items-center justify-between gap-3">
                <p className="font-mono text-[11px] leading-4 text-ink">
                  Effect of pipes, matched on clay × built-up = {signed(spam?.delta_mm_yr)} mm/yr
                </p>
                <p className="shrink-0 text-[10.5px] text-ink-3">
                  shift null 5–95 %: {signed(spam?.shift_null_p05)} to {signed(spam?.shift_null_p95)}
                </p>
              </div>
              <dl className="mt-2 grid grid-cols-3 gap-2 border-t border-line pt-2 text-[11px]">
                <div>
                  <dt className="text-ink-3">p (slowdown)</dt>
                  <dd className="font-medium text-ink">{spam?.p_lower == null ? "—" : num(spam.p_lower, 2)}</dd>
                </div>
                <div>
                  <dt className="text-ink-3">Placebo years</dt>
                  <dd className="font-medium text-ink">
                    {signed(spam?.placebo_years_delta_mm_yr)} · {spam?.placebo_year_clean ? "clean" : "not clean"}
                  </dd>
                </div>
                <div>
                  <dt className="text-ink-3">Placebo area</dt>
                  <dd className="font-medium text-ink">
                    {signed(spam?.placebo_area_delta_mm_yr)} · {spam?.placebo_area_clean ? "clean" : "not clean"}
                  </dd>
                </div>
              </dl>
              <p className="mt-2 border-t border-line pt-2 text-[11px] leading-[16px] text-ink-2">
                Positive control (V8): {spam?.positive_control_passed ? "passed" : "failed"} ·{" "}
                {signed(spam?.positive_control_delta_mm_yr, 2)} mm/yr vs null 5th percentile{" "}
                {signed(spam?.positive_control_null_p05, 2)}. {spam?.positive_control_note}
              </p>
            </div>

            <InfoNote tone="blue" icon={<Info size={15} />} className="mt-3">
              Already seen city-wide: the fastest-sinking areas slowed from{" "}
              {fast2018 == null ? "103" : num(fast2018, 0)} to{" "}
              {fast2023 == null ? "89" : num(fast2023, 0)} mm/yr. The cause is open.
            </InfoNote>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-blue-50 p-4">
              <p className="text-[13px] font-semibold leading-[18px] text-ink">
                If the west slowed more
              </p>
              <p className="mt-2 text-[12px] leading-[17px] text-ink-2">
                Pipes help locally. Put new pipes where the priority map ranks highest.
              </p>
            </div>
            <div className="rounded-xl bg-amber-50 p-4">
              <p className="text-[13px] font-semibold leading-[18px] text-ink">
                If there is no difference
              </p>
              <p className="mt-2 text-[12px] leading-[17px] text-ink-2">
                Pressure loss is regional, so the benefit spreads across the aquifer.
                Rank pipes by volume replaced, not by place.
              </p>
            </div>
          </div>

          <Card>
            <div className="flex items-center gap-2">
              <span className="flex size-6 items-center justify-center rounded-full bg-blue-50 text-blue-700">
                <Droplets size={14} />
              </span>
              <h2 className="text-[15px] font-semibold leading-5 text-ink">
                {spam?.name ?? "SPAM Semarang Barat"}
              </h2>
              <span className="flex-1" />
              <Badge tone="amber" dot>
                {statusLabel}
              </Badge>
            </div>

            {spamState.error ? (
              <div className="mt-3">
                <ErrorBlock message={spamState.error} retry={spamState.reload} />
              </div>
            ) : (
              <dl className="mt-3 divide-y divide-line">
                <Fact label="Source" value="Jatibarang reservoir, surface water" />
                <Fact
                  label="Design capacity"
                  value={
                    designMm3 == null
                      ? "—"
                      : `${num(spam?.design_capacity_lps)} L/s · ${num(designMm3, 1)} Mm³/yr`
                  }
                />
                <Fact label="Absorbed, Jan 2024" value={absorbedText} />
                <Fact label="Connections" value={connectionsText} />
                <Fact
                  label="Scale"
                  value="About 2× the city’s declared groundwater"
                />
              </dl>
            )}

            <InfoNote
              tone="amber"
              icon={<AlertTriangle size={14} />}
              className="mt-3"
            >
              <p className="font-medium">What the app concludes</p>
              <p className="mt-0.5">
                {spam?.outcome_wording ??
                  "The SPAM Semarang Barat before/after test has not been run. The app shows the design and the data on disk, but makes no claim."}
              </p>
            </InfoNote>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <Waves size={15} className="text-ink-3" />
              <h2 className="text-[14px] font-semibold leading-5 text-ink">
                Caveats written down before the run
              </h2>
            </div>
            <ul className="mt-3 space-y-2">
              {CAVEATS.map((caveat) => (
                <li
                  key={caveat}
                  className="flex gap-2 text-[12px] leading-[17px] text-ink-2"
                >
                  <AlertTriangle
                    size={14}
                    className="mt-0.5 shrink-0 text-amber-600"
                  />
                  {caveat}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
