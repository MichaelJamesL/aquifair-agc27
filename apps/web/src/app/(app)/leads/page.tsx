"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Building,
  Download,
  Factory,
  HelpCircle,
  Hospital,
  Hotel,
  Layers,
  ShieldAlert,
  Warehouse,
} from "lucide-react";
import type { Lead } from "@/lib/api";
import { api, failedFilters } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { num } from "@/lib/format";
import { useRole } from "@/components/neraca/role-context";
import { OverlayMap, type OverlayLayer } from "@/components/neraca/overlay-map";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorBlock,
  LoadingBlock,
  cn,
} from "@/components/neraca/ui";

const BOUNDS: [[number, number], [number, number]] = [
  [110.3, -7.08],
  [110.66, -6.88],
];

const USE_CLASSES = [
  { key: "factory", label: "Factory", icon: Factory, colour: "#7c3aed" },
  { key: "hotel", label: "Hotel", icon: Hotel, colour: "#0e7490" },
  { key: "mall", label: "Mall", icon: Building, colour: "#be185d" },
  { key: "hospital", label: "Hospital", icon: Hospital, colour: "#15803d" },
  { key: "warehouse", label: "Warehouse", icon: Warehouse, colour: "#a16207" },
  { key: "unknown", label: "Unknown", icon: HelpCircle, colour: "#9ca3af" },
] as const;

/** Why a candidate is not a lead, or a class that is not from an OSM tag on the building itself. */
function classBadge(lead: Lead): string | null {
  if (lead.use_class === "unknown" && lead.filters["3"]) return "site check";
  const failed = failedFilters(lead);
  if (failed.length) return `fails ${failed.join(", ")}`;
  if (lead.labels.use_class !== "WEAK") return null;
  return lead.use_class_basis?.startsWith("Overture") ? "POI only" : "estate only";
}

const ZONE_LEGEND = [
  { key: "safe", label: "Aman", colour: "#9ccff0" },
  { key: "vulnerable", label: "Rawan", colour: "#f6eb8c" },
  { key: "critical", label: "Kritis", colour: "#f4a3a3" },
  { key: "damaged", label: "Rusak", colour: "#e0393e" },
  { key: "recharge", label: "Imbuhan", colour: "#9be27a" },
];

const FILTERS = [
  { key: "1", label: "New roof since 2022, at least 1,000 m²" },
  { key: "2", label: "Water-using class (factory, hotel, mall, hospital)" },
  { key: "3", label: "Inside a critical or damaged zone" },
  { key: "4", label: "Piped coverage below 50 % (proxy; hotels, malls, hospitals only)" },
];

// Piped coverage per kecamatan, classed so the 50 % cut-off of filter 4 is a class edge (one hue, light to dark).
const COVERAGE_CLASSES = [
  { label: "< 25 %", colour: "#cfe2f3" },
  { label: "25–50 %", colour: "#9cc4e4" },
  { label: "50–75 %", colour: "#5d9bcc" },
  { label: "≥ 75 %", colour: "#155a96" },
];
const COVERAGE_NO_DATA = "#9ca3af";
const COVERAGE_BASIS: Record<string, string> = {
  "Kota Semarang": "PDAM customers per resident, scaled to the city's 65 % service level (BPS 2024)",
  "Kab. Demak": "households with piped water per family card (Portal Data Demak)",
};

function CoverageTip({ properties }: { properties: Record<string, unknown> }) {
  const coverage = properties.coverage as number | null;
  const regency = String(properties.regency ?? "");
  return (
    <div className="space-y-0.5">
      <p className="text-[12.5px] font-semibold leading-4 text-ink">{String(properties.kecamatan ?? "")}</p>
      <p className="text-[11px] text-ink-3">{regency}</p>
      {coverage == null ? (
        <p className="pt-1 text-[11.5px] leading-4">
          No piped-coverage figure per kecamatan is published here, so a hotel, mall or hospital cannot pass filter 4.
        </p>
      ) : (
        <>
          <p className="pt-1 text-[11.5px] leading-4">
            <span className="font-mono font-medium text-ink">{Math.round(coverage * 100)} %</span> piped coverage,{" "}
            {String(properties.year ?? "")}
          </p>
          <p className="text-[11.5px] leading-4">
            {coverage < 0.5
              ? "Below 50 %: hotels, malls and hospitals here pass filter 4."
              : "50 % or more: hotels, malls and hospitals here fail filter 4."}
          </p>
          {COVERAGE_BASIS[regency] && <p className="text-[10.5px] leading-[14px] text-ink-3">{COVERAGE_BASIS[regency]}</p>}
        </>
      )}
    </div>
  );
}

type LayerKey = "zones" | "coverage" | "wells" | "leads";

const LAYERS: { key: LayerKey; label: string }[] = [
  { key: "zones", label: "Conservation zones, ESDM 2022" },
  { key: "coverage", label: "Piped coverage per kecamatan (proxy)" },
  { key: "wells", label: "Sumur Bor on the 2022 zone map" },
  { key: "leads", label: "Leads (inspector only)" },
];

function CountTile({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-lg bg-bg px-2.5 py-2">
      <p className="font-display text-[20px] leading-6 tracking-[-0.3px] text-ink">{value}</p>
      <p className="mt-0.5 text-[10px] leading-3 text-ink-3">{label}</p>
    </div>
  );
}

function exportCsv(leads: Lead[]) {
  const header = ["id", "use_class", "district", "regency", "lat", "lon", "footprint_m2", "built_year", "zone", "pdam_coverage", "sinking_mm_yr", "fails_filters"];
  const rows = leads.map((lead) =>
    [lead.id, lead.use_class, lead.district, lead.regency ?? "", lead.lat, lead.lon, lead.footprint_m2, lead.built_year, lead.zone ?? "", lead.pdam_coverage ?? "", lead.sinking_mm_yr ?? "", failedFilters(lead).join(" ")]
      .map((value) => `"${String(value).replaceAll('"', '""')}"`)
      .join(","),
  );
  const blob = new Blob([[header.join(","), ...rows].join("\n")], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "neraca-leads.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

export default function LeadsPage() {
  const router = useRouter();
  const { role, setRole } = useRole();
  const isInspector = role === "inspector";
  const [activeClasses, setActiveClasses] = useState<string[]>([]);
  const [checked, setChecked] = useState<string[]>(["2", "3", "4"]);
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    zones: true,
    coverage: false,
    wells: true,
    leads: true,
  });

  const zonesState = useApi("map-zones", (signal) => api.zones(signal));
  const wellsState = useApi("map-zone-wells", (signal) => api.zoneWells(signal));
  const coverageState = useApi("map-pdam-coverage", (signal) => api.pdamCoverage(signal));
  // every candidate (stage 1); the filter checkboxes pick the subset in the browser
  const leadsState = useApi(`leads-${role}`, (signal) =>
    isInspector ? api.leads(role, signal, "1") : Promise.resolve(null),
  );
  const summaryState = useApi("leads-public-summary", (signal) => api.leadSummary(signal));
  const hitState = useApi(`lead-hits-${role}`, (signal) =>
    isInspector ? api.hitRate(role, signal) : Promise.resolve([]),
  );

  const candidates = useMemo(() => leadsState.data?.items ?? [], [leadsState.data]);
  // a filter not applied to a class (null) counts as passed
  const allLeads = useMemo(
    () => candidates.filter((lead) => checked.every((key) => lead.filters[key] !== false)),
    [candidates, checked],
  );
  const leads = useMemo(
    () => (activeClasses.length ? allLeads.filter((lead) => activeClasses.includes(lead.use_class)) : allLeads),
    [allLeads, activeClasses],
  );
  const funnel = summaryState.data?.funnel ?? [];
  const detector = leadsState.data?.method.detector;
  const dropped = leadsState.data?.method.dropped;
  const reason = summaryState.data?.status === "unavailable" ? summaryState.data.reason : null;

  const classCounts = useMemo(() => {
    const result: Record<string, number> = {};
    if (isInspector) {
      for (const lead of allLeads) result[lead.use_class] = (result[lead.use_class] ?? 0) + 1;
    } else {
      for (const row of summaryState.data?.items ?? []) {
        for (const [key, value] of Object.entries(row.by_use_class)) result[key] = (result[key] ?? 0) + value;
      }
    }
    return result;
  }, [allLeads, isInspector, summaryState.data]);

  const visits = (hitState.data ?? []).reduce((sum, row) => sum + row.visits, 0);
  const unregistered = (hitState.data ?? []).reduce((sum, row) => sum + row.unregistered, 0);
  const totalLeads = (summaryState.data?.items ?? []).reduce((sum, row) => sum + row.leads, 0);
  const inspectorLeads = funnel.find((step) => step.step === "1-4")?.count ?? 0;

  const overlays = useMemo<OverlayLayer[]>(() => {
    const zoneColour = ["match", ["get", "zone"], ...ZONE_LEGEND.flatMap((z) => [z.key, z.colour]), "#cccccc"];
    const wells = wellsState.data
      ? {
          type: "FeatureCollection" as const,
          features: wellsState.data.items.map((w) => ({
            type: "Feature" as const,
            properties: {},
            geometry: { type: "Point" as const, coordinates: [w.lon, w.lat] },
          })),
        }
      : null;
    const leadPoints = {
      type: "FeatureCollection" as const,
      features: leads.map((lead) => ({
        type: "Feature" as const,
        properties: { id: lead.id, use_class: lead.use_class },
        geometry: { type: "Point" as const, coordinates: [lead.lon, lead.lat] },
      })),
    };
    const leadShapes = {
      type: "FeatureCollection" as const,
      features: leads.map((lead) => ({
        type: "Feature" as const,
        properties: { id: lead.id },
        geometry: { type: "Polygon" as const, coordinates: [lead.polygon] },
      })),
    };
    return [
      {
        id: "zones",
        data: (zonesState.data as GeoJSON.FeatureCollection | null) ?? null,
        visible: layers.zones,
        layers: [
          { id: "zones-fill", type: "fill", paint: { "fill-color": zoneColour as never, "fill-opacity": 0.42 } },
        ],
      },
      {
        id: "coverage",
        data: (coverageState.data?.geojson as GeoJSON.FeatureCollection | undefined) ?? null,
        visible: layers.coverage,
        layers: [
          {
            id: "coverage-fill",
            type: "fill",
            paint: {
              "fill-color": [
                "case",
                ["==", ["get", "coverage"], null],
                COVERAGE_NO_DATA,
                ["step", ["get", "coverage"], ...COVERAGE_CLASSES.flatMap((c, i) => (i ? [i / 4, c.colour] : [c.colour]))],
              ] as never,
              "fill-opacity": [
                "case",
                ["boolean", ["feature-state", "hover"], false],
                0.8,
                ["==", ["get", "coverage"], null],
                0.18,
                0.6,
              ] as never,
            },
          },
          {
            id: "coverage-line",
            type: "line",
            paint: {
              "line-color": "#1e3a5f",
              "line-width": ["case", ["boolean", ["feature-state", "hover"], false], 2.5, 0.6] as never,
            },
          },
        ],
      },
      {
        id: "wells",
        data: wells,
        visible: layers.wells,
        layers: [
          {
            id: "wells-dot",
            type: "circle",
            paint: { "circle-radius": 2.2, "circle-color": "#7f1d1d", "circle-opacity": 0.8 },
          },
        ],
      },
      {
        id: "lead-shapes",
        data: leadShapes,
        visible: layers.leads && isInspector,
        layers: [
          { id: "lead-shape-line", type: "line", minzoom: 13, paint: { "line-color": "#111827", "line-width": 1.5 } },
        ],
      },
      {
        id: "leads",
        data: leadPoints,
        visible: layers.leads && isInspector,
        layers: [
          {
            id: "leads-dot",
            type: "circle",
            paint: {
              "circle-radius": 6,
              "circle-color": [
                "match",
                ["get", "use_class"],
                ...USE_CLASSES.flatMap((c) => [c.key, c.colour]),
                "#111827",
              ] as never,
              "circle-stroke-color": "#ffffff",
              "circle-stroke-width": 1.5,
            },
          },
        ],
      },
    ] as OverlayLayer[];
  }, [zonesState.data, coverageState.data, wellsState.data, leads, layers, isInspector]);

  const toggleClass = (key: string) =>
    setActiveClasses((current) => (current.includes(key) ? current.filter((item) => item !== key) : [...current, key]));

  return (
    <div className="grid h-[calc(100vh-56px)] grid-cols-[320px_minmax(0,1fr)_400px] overflow-hidden">
      <aside className="flex min-h-0 flex-col gap-[18px] overflow-y-auto border-r border-line bg-surface px-5 pb-4 pt-5">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[18px] font-semibold leading-6 text-ink">Inspection leads</h1>
          <p className="text-[13px] leading-[19px] text-ink-2">
            New large water users inside zones where no new well permit can be issued. Each lead is a
            reason to visit, not a finding.
          </p>
        </div>

        {isInspector && (
          <div className="flex flex-col gap-1.5">
            <p className="text-[12px] font-medium leading-4 text-ink-2">Show roofs that pass</p>
            {FILTERS.map((filter) => {
              const locked = filter.key === "1"; // every candidate is a new roof
              return (
                <label key={filter.key} className="flex cursor-pointer items-start gap-2 py-[3px] text-[12px] leading-4 text-ink">
                  <input
                    type="checkbox"
                    checked={locked || checked.includes(filter.key)}
                    disabled={locked}
                    onChange={() =>
                      setChecked((current) =>
                        current.includes(filter.key) ? current.filter((key) => key !== filter.key) : [...current, filter.key],
                      )
                    }
                    className="mt-px size-[14px] shrink-0 accent-blue-700"
                  />
                  <span className="w-3 shrink-0 font-mono text-[10px] leading-4 text-ink-3">{filter.key}</span>
                  <span className="flex-1">{filter.label}</span>
                  <span className="font-mono text-[11px] text-ink-3">
                    {num(candidates.filter((lead) => lead.filters[filter.key] !== false).length)}
                  </span>
                </label>
              );
            })}
            <p className="text-[11px] leading-[16px] text-ink-3">
              {num(allLeads.length)} roofs pass the ticked filters; leads pass all four. Unknown-class site checks:
              tick only 3, then pick Unknown.
            </p>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <p className="text-[12px] font-medium leading-4 text-ink-2">Water-use class</p>
          <div className="flex flex-wrap gap-1.5">
            {USE_CLASSES.map((item) => {
              const Icon = item.icon;
              const active = activeClasses.includes(item.key);
              return (
                <button
                  key={item.key}
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggleClass(item.key)}
                  className={cn(
                    "inline-flex h-[30px] items-center gap-1.5 rounded-full border px-2.5 text-[12px] leading-4 transition-colors",
                    active ? "border-blue-700 bg-blue-50 text-blue-700" : "border-line-strong bg-surface text-ink-2 hover:bg-bg",
                  )}
                >
                  <span className="size-2 rounded-full" style={{ backgroundColor: item.colour }} />
                  <Icon size={14} className={active ? "text-blue-700" : "text-ink-3"} />
                  <span className="font-medium text-ink">{item.label}</span>
                  <span className={active ? "text-blue-700" : "text-ink-3"}>{classCounts[item.key] ?? 0}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <p className="text-[12px] font-medium leading-4 text-ink-2">Layers</p>
          {LAYERS.map((item) => (
            <label key={item.key} className="flex cursor-pointer items-center gap-2.5 rounded-md py-[5px] text-[13px] text-ink">
              <input
                type="checkbox"
                checked={layers[item.key]}
                disabled={item.key === "leads" && !isInspector}
                onChange={() => setLayers((current) => ({ ...current, [item.key]: !current[item.key] }))}
                className="size-[14px] shrink-0 accent-blue-700"
              />
              {item.label}
            </label>
          ))}
        </div>

        <div className="rounded-lg bg-bg px-3 py-3">
          <p className="text-[12px] font-medium leading-4 text-ink">Which sites become leads</p>
          {funnel.length > 0 ? (
            <ol className="mt-2 space-y-1.5">
              {funnel.map((step) => (
                <li key={step.step} className="flex items-baseline gap-2 text-[11px] leading-[16px] text-ink-2">
                  <span className="w-7 shrink-0 font-mono text-[10px] text-ink-3">{step.step === "unknown" ? "?" : step.step}</span>
                  <span className="flex-1">{step.label}</span>
                  <span className="font-mono text-[12px] font-medium text-ink">{num(step.count)}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-[11px] leading-[16px] text-ink-3">{reason ?? "Loading the filter counts…"}</p>
          )}
          <details className="group mt-2 border-t border-line pt-2">
            <summary className="cursor-pointer list-none text-[11px] font-medium leading-4 text-blue-700">
              <span className="group-open:hidden">How the filters work</span>
              <span className="hidden group-open:inline">Hide details</span>
            </summary>
          {detector && (
            <p className="mt-2 text-[11px] leading-[16px] text-ink-3">
              Step 1 roof detector, tested on the half of the map it did not learn from:{" "}
              {Math.round(detector.accuracy * 100)} % correct, {Math.round(detector.roof_recall * 100)} % of known
              roofs found.
              {dropped &&
                ` Removed before step 1: ${num(dropped.road_or_runway_shape ?? 0)} road or runway shapes, ` +
                  `${num(dropped.larger_than_25_ha ?? 0)} patches over 25 ha, ` +
                  `${num(dropped.already_in_microsoft_footprints ?? 0)} already in Microsoft footprints, ` +
                  `${num(dropped.radar_not_a_building_now ?? 0)} that radar does not see as a building now ` +
                  `(bare fill, fields), ${num(dropped.radar_building_already_in_2022 ?? 0)} that radar saw ` +
                  `as a building in 2022.`}
            </p>
          )}
          <p className="mt-2 border-t border-line pt-2 text-[11px] leading-[16px] text-ink-3">
            Four filters, no weighted score. Filter 4 is a proxy until PDAM releases coverage per
            kelurahan, and is not applied to factories: PDAM sold industry 0.22 Mm³ in 2022 (Perda Kota
            Semarang 4/2024), so household piped coverage says little about a factory.
          </p>
          </details>
        </div>

        <div className="flex-1" />

        <p className="text-[11px] leading-[15px] text-ink-3">
          Zones and wells: Dinas ESDM Jateng 2022 map under Permen ESDM 31/2018, digitised from the
          vector PDF. New roofs: Sentinel-2 2021–2026. Class: OpenStreetMap, then Overture places. Coverage: BPS Kota
          Semarang 2024, Portal Data Demak 2025.
        </p>
      </aside>

      <section className="relative min-h-0 overflow-hidden bg-sea">
        <OverlayMap
          overlays={overlays}
          bounds={BOUNDS}
          clickableLayers={["leads-dot"]}
          onFeatureClick={(_, feature) => router.push(`/leads/${feature.properties?.id}`)}
          hoverLayers={["coverage-fill"]}
          tooltip={(_, feature) => <CoverageTip properties={feature.properties ?? {}} />}
        />

        {!isInspector && (
          <div className="absolute left-4 top-4 z-10 w-[360px]">
            <Card className="shadow-pop">
              <div className="flex items-center gap-2">
                <Badge tone="amber" dot>
                  Inspector only
                </Badge>
                <span className="text-[11px] text-ink-3">Risk R7</span>
              </div>
              <p className="mt-2 text-[12px] leading-[18px] text-ink-2">
                Lead points and addresses are withheld. The public view gets counts per district (right).
              </p>
              <Button
                variant="primary"
                size="sm"
                className="mt-3"
                icon={<ShieldAlert size={14} />}
                onClick={() => setRole("inspector")}
              >
                Switch to inspector
              </Button>
            </Card>
          </div>
        )}

        <div className="absolute bottom-4 left-4 z-10 flex w-[380px] flex-col gap-2">
        {layers.coverage && (
          <div className="rounded-xl bg-surface p-3.5 shadow-pop">
            <p className="text-[12px] font-medium leading-4 text-ink">Piped water coverage per kecamatan · filter 4 proxy</p>
            <div className="mt-2.5 grid grid-cols-5 gap-2">
              {[...COVERAGE_CLASSES, { label: "no data", colour: COVERAGE_NO_DATA }].map((item) => (
                <span key={item.label} className="flex items-center gap-1.5 text-[11px] text-ink-2">
                  <span className="size-2.5 shrink-0 rounded-[2px] border border-line" style={{ backgroundColor: item.colour }} />
                  {item.label}
                </span>
              ))}
            </div>
            <p className="mt-2.5 border-t border-line pt-2 text-[10px] leading-[15px] text-ink-3">
              Share of a kecamatan on PDAM pipes: Kota Semarang 2023, Kab. Demak 2025. Below 50 % counts as outside the
              network for hotels, malls and hospitals; factories are not checked. Hover a kecamatan for its value.
            </p>
          </div>
        )}
        <div className="rounded-xl bg-surface p-3.5 shadow-pop">
          <div className="flex items-center gap-2">
            <Layers size={14} className="text-ink-3" />
            <p className="text-[12px] font-medium leading-4 text-ink">Groundwater conservation zone · ESDM 2022</p>
          </div>
          <div className="mt-2.5 grid grid-cols-5 gap-2">
            {ZONE_LEGEND.map((zone) => (
              <span key={zone.key} className="flex items-center gap-1.5 text-[11px] text-ink-2">
                <span className="size-2.5 rounded-[2px] border border-line" style={{ backgroundColor: zone.colour }} />
                {zone.label}
              </span>
            ))}
          </div>
          <p className="mt-2.5 border-t border-line pt-2 text-[10px] leading-[15px] text-ink-3">
            Kritis: new wells only for non-industrial use, with volume caps. Rusak: no new abstraction,
            PDAM only. Dark dots: the map&apos;s {num(wellsState.data?.items.length ?? 0)} &ldquo;Sumur Bor&rdquo;
            markers. Coast fitted to OpenStreetMap: reclaimed land the 2022 map leaves out takes the nearest zone.
          </p>
        </div>
        </div>
      </section>

      <aside className="flex min-h-0 flex-col overflow-hidden border-l border-line bg-surface">
        <div className="border-b border-line px-5 pb-4 pt-5">
          <h2 className="text-[18px] font-semibold leading-6 text-ink">{isInspector ? "Lead list" : "Leads per district"}</h2>
          <p className="mt-1 text-[12px] leading-4 text-ink-3">
            {isInspector
              ? checked.length === 3
                ? "Sorted by district. Nothing is ranked: every lead passed the same four filters."
                : `Roofs passing filter ${["1", ...[...checked].sort()].join(", ")}: candidates, not all leads. The badge says which filter each one fails.`
              : "Counts only; no addresses or coordinates."}
          </p>
          <div className="mt-3 grid grid-cols-4 gap-2">
            <CountTile value={num(isInspector ? inspectorLeads : totalLeads)} label="leads" />
            <CountTile value={isInspector ? num(visits) : "—"} label="visited" />
            <CountTile value={isInspector ? num(unregistered) : "—"} label="unregistered" />
            <CountTile value={isInspector && visits ? `${Math.round((100 * unregistered) / visits)}%` : "—"} label="hit rate" />
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {isInspector && leadsState.loading && !leadsState.data && <LoadingBlock label="Loading the lead list" />}
          {isInspector && leadsState.error && <ErrorBlock message={leadsState.error} retry={leadsState.reload} />}

          {!isInspector &&
            (summaryState.data?.items.length ? (
              <table className="w-full text-[12px]">
                <thead>
                  <tr className="border-b border-line text-left text-[11px] text-ink-3">
                    <th className="py-1.5 font-medium">District</th>
                    <th className="py-1.5 font-medium">By class</th>
                    <th className="py-1.5 text-right font-medium">Leads</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryState.data.items.map((row) => (
                    <tr key={row.district} className="border-b border-line last:border-b-0">
                      <td className="py-2 text-ink">{row.district}</td>
                      <td className="py-2 text-[11px] capitalize text-ink-3">
                        {Object.entries(row.by_use_class)
                          .map(([key, value]) => `${key} ${value}`)
                          .join(" · ")}
                      </td>
                      <td className="py-2 text-right font-mono text-ink">{row.leads}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState title="No district counts" icon={<ShieldAlert size={20} />}>
                {reason ?? "Loading district counts…"}
              </EmptyState>
            ))}

          {isInspector && leadsState.data && leads.length === 0 && (
            <EmptyState title="No lead matches the class filter" icon={<Building size={20} />}>
              Clear the class filter to see every lead.
            </EmptyState>
          )}

          {isInspector && leads.length > 0 && (
            <ul className="flex flex-col">
              {leads.map((lead) => (
                <li key={lead.id} className="border-b border-line py-3 last:border-b-0">
                  <Link href={`/leads/${lead.id}`} className="flex items-start gap-2 text-left hover:text-blue-700">
                    <span
                      className="mt-1.5 size-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: USE_CLASSES.find((c) => c.key === lead.use_class)?.colour }}
                    />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5 text-[13px] font-medium capitalize text-ink">
                        {lead.use_class} · {lead.district}
                        {classBadge(lead) && (
                          <Badge tone={lead.labels.use_class === "WEAK" && !failedFilters(lead).length ? "amber" : "gray"} className="h-[18px] px-1.5 text-[10px] normal-case">
                            {classBadge(lead)}
                          </Badge>
                        )}
                      </span>
                      <span className="mt-0.5 block text-[11px] text-ink-3">
                        {num(lead.footprint_m2)} m² new roof · since {lead.built_year} · {lead.zone ? `${lead.zone} zone` : "not in a closed zone"} ·{" "}
                        {lead.pdam_coverage == null ? "coverage unknown" : `${Math.round(lead.pdam_coverage * 100)}% piped`}
                      </span>
                    </span>
                    <ArrowRight size={14} className="mt-1 shrink-0 text-ink-3" />
                  </Link>
                </li>
              ))}
            </ul>
          )}

          {isInspector && (
            <div className="mt-4 rounded-lg bg-bg p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle size={14} className="mt-0.5 shrink-0 text-amber-600" />
                <p className="text-[11px] leading-[16px] text-ink-2">
                  A visit is not a verdict. Record what you find on the lead card so the hit rate (V6)
                  can be measured.
                </p>
              </div>
            </div>
          )}

          <Link
            href="/leads/validation"
            className="mt-4 inline-flex items-center gap-1 text-[12px] font-medium text-blue-700"
          >
            How leads are checked <ArrowRight size={13} />
          </Link>
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-line px-5 py-3">
          <p className="font-mono text-[10px] text-ink-3">
            {isInspector ? `Showing ${leads.length} of ${allLeads.length}` : `${summaryState.data?.items.length ?? 0} districts`}
          </p>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={14} />}
            disabled={!isInspector || leads.length === 0}
            onClick={() => exportCsv(leads)}
          >
            Export list
          </Button>
        </div>
      </aside>
    </div>
  );
}
