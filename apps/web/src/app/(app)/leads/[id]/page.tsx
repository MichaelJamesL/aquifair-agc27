"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Building,
  ClipboardCheck,
  Droplets,
  Layers,
  ListChecks,
  MapPinned,
  Ruler,
  ShieldAlert,
  Waves,
} from "lucide-react";
import { api, failedFilters, leadImageUrl, postFeedback, type Feedback, type Lead } from "@/lib/api";
import { num } from "@/lib/format";
import { OverlayMap, type OverlayLayer } from "@/components/neraca/overlay-map";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import {
  Badge,
  Button,
  Card,
  CodeTag,
  EmptyState,
  ErrorBlock,
  InfoNote,
  LabelBadge,
  LoadingBlock,
  SectionTitle,
  cn,
} from "@/components/neraca/ui";

const ZONE_LABEL: Record<string, string> = {
  safe: "Safe",
  vulnerable: "Vulnerable",
  critical: "Critical",
  damaged: "Damaged",
};

function zoneLabel(zone: string | null) {
  if (!zone) return "not critical or damaged";
  return ZONE_LABEL[zone.toLowerCase()] ?? zone;
}

function coordinateText(lat: number, lon: number) {
  const latText = `${Math.abs(lat).toFixed(3)}° ${lat >= 0 ? "N" : "S"}`;
  const lonText = `${Math.abs(lon).toFixed(3)}° ${lon >= 0 ? "E" : "W"}`;
  return `${latText}, ${lonText}`;
}

function Breadcrumb({ current }: { current: string }) {
  return (
    <div className="flex items-center gap-2 text-[12px] text-ink-3">
      <Link
        href="/leads"
        className="inline-flex items-center gap-1 text-ink-2 hover:text-ink"
      >
        <ArrowLeft size={14} /> All leads
      </Link>
      <span>/</span>
      <span className="text-ink">Semarang–Demak</span>
      <span>/</span>
      <span className="max-w-[280px] truncate text-ink" title={current}>
        {current}
      </span>
    </div>
  );
}

function LeadShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-[1100px] px-10 pb-14 pt-6">
      <Breadcrumb current="Lead" />
      {children}
    </div>
  );
}

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const leadId = params.id;
  const { role, setRole } = useRole();
  const isInspector = role === "inspector";

  const leadsState = useApi(`lead-detail-${role}-${leadId}`, (signal) =>
    isInspector
      ? api.lead(leadId, role, signal).then(
          (item) => ({ items: [item], reason: null }),
          (error: unknown) => {
            if (error instanceof Error && error.message.includes("not found")) return { items: [], reason: null };
            throw error;
          },
        )
      : Promise.resolve({ items: [], reason: null }),
  );
  const summaryState = useApi("lead-detail-public-summary", (signal) => api.leadSummary(signal));

  const reason = leadsState.data?.reason ?? summaryState.data?.reason ?? null;
  const lead = leadsState.data?.items.find((item) => item.id === leadId) ?? null;

  if (!isInspector) {
    return (
      <LeadShell>
        <div className="mx-auto mt-8 max-w-[760px]">
          <p className="eyebrow text-ink-3">Module B · Inspection leads</p>
          <h1 className="mt-2 font-display text-[30px] font-medium leading-9 tracking-[-0.5px] text-ink">
            Lead record
          </h1>
          <p className="mt-2 text-[13px] leading-[19px] text-ink-2">
            A lead carries coordinates, a building footprint and satellite images of the site. Those
            fields are withheld from public, regulator and planner views (risk R7).
          </p>
          <div className="mt-5">
            <EmptyState
              title="Lead addresses are inspector-only"
              icon={<ShieldAlert size={22} />}
              action={
                <Button
                  variant="primary"
                  size="sm"
                  icon={<ShieldAlert size={14} />}
                  onClick={() => setRole("inspector")}
                >
                  Switch to inspector
                </Button>
              }
            >
              Switch to the inspector role to load this record. The public view only exposes
              counts per district.
              {reason && (
                <span className="mt-2 block text-[11px] leading-[16px] text-ink-3">{reason}</span>
              )}
            </EmptyState>
          </div>
        </div>
      </LeadShell>
    );
  }

  if (leadsState.loading && !leadsState.data) {
    return (
      <LeadShell>
        <div className="mt-6">
          <LoadingBlock label="Loading the lead record" />
        </div>
      </LeadShell>
    );
  }

  if (leadsState.error) {
    return (
      <LeadShell>
        <div className="mt-6">
          <ErrorBlock message={leadsState.error} retry={leadsState.reload} />
        </div>
      </LeadShell>
    );
  }

  if (!lead) {
    return (
      <LeadShell>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <Badge tone="amber" dot>
            Not issued
          </Badge>
          <CodeTag>{leadId}</CodeTag>
          <span className="text-[12px] text-ink-3">Module B · Semarang–Demak</span>
        </div>

        <div className="mt-3">
          <h1 className="font-display text-[32px] font-medium leading-10 tracking-[-0.5px] text-ink">
            Lead not available
          </h1>
          <p className="mt-2 max-w-[660px] text-[13px] leading-[19px] text-ink-2">
            No lead with this id exists in the current list. Lead ids come from the position of the new
            roof; when the satellite layers are rebuilt, a site can drop out of the list.
          </p>
        </div>

        <div className="mt-6">
          <EmptyState
            title="No record to show"
            icon={<MapPinned size={22} />}
            action={
              <div className="flex items-center gap-2">
                <Link href="/leads">
                  <Button variant="primary" size="sm" icon={<ArrowLeft size={14} />}>
                    Back to the lead map
                  </Button>
                </Link>
                <Link href="/leads/validation">
                  <Button variant="secondary" size="sm" icon={<ArrowRight size={14} />}>
                    How leads are checked
                  </Button>
                </Link>
              </div>
            }
          >
            {reason ??
              "The backend returned no lead list and no reason. This page will not invent an address, footprint or visit outcome to fill the gap."}
          </EmptyState>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-4">
          {[
            {
              n: "1",
              title: "A new large building",
              body: "A roof that appears after the 2022 zone map and holds for at least two dry seasons, at least 1,000 m², radar-bright now and not in 2022, in a factory, hotel, mall or hospital class. Source: Sentinel-2 2021–2026, Sentinel-1, OpenStreetMap, Overture places.",
            },
            {
              n: "2",
              title: "Inside a closed zone",
              body: "The point must fall in a critical or damaged conservation zone, where no new well permit can be issued.",
            },
            {
              n: "3",
              title: "Outside the PDAM proxy",
              body: "Hotels, malls and hospitals only: the district has piped coverage below 50 %. The network map is not public, so this is a proxy, not a boundary. Factories skip it: PDAM sells industry almost no water.",
            },
          ].map((item) => (
            <Card key={item.n} className="bg-surface">
              <div className="flex items-center gap-2">
                <span className="flex size-5 items-center justify-center rounded-full border border-line-strong font-mono text-[11px] text-ink-2">
                  {item.n}
                </span>
                <p className="text-[13px] font-medium leading-[18px] text-ink">{item.title}</p>
              </div>
              <p className="mt-2 text-[12px] leading-[17px] text-ink-2">{item.body}</p>
            </Card>
          ))}
        </div>
      </LeadShell>
    );
  }

  return <LeadRecord lead={lead} />;
}

const OUTCOMES: { key: Feedback["outcome"]; label: string }[] = [
  { key: "unregistered_well", label: "Unregistered well" },
  { key: "registered_well", label: "Registered well" },
  { key: "pdam_customer", label: "PDAM customer" },
  { key: "no_well", label: "No well" },
];

function Row({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-line pb-2.5 last:border-b-0 last:pb-0">
      <span className="inline-flex shrink-0 items-center gap-2 text-ink-3">
        {icon} {label}
      </span>
      <span className="text-right font-medium text-ink">{children}</span>
    </div>
  );
}

function LeadRecord({ lead }: { lead: Lead }) {
  const feedbackState = useApi(`lead-feedback-${lead.id}`, (signal) => api.leadFeedback(lead.id, "inspector", signal));
  const [inspector, setInspector] = useState("");
  const [outcome, setOutcome] = useState<Feedback["outcome"]>("unregistered_well");
  const [note, setNote] = useState("");
  const [visitedAt, setVisitedAt] = useState(() => new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const visits = feedbackState.data ?? [];
  const overlays = useMemo<OverlayLayer[]>(
    () => [
      {
        id: "lead-shape",
        data: {
          type: "FeatureCollection",
          features: [{ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [lead.polygon] } }],
        },
        layers: [
          { id: "lead-shape-fill", type: "fill", paint: { "fill-color": "#f59e0b", "fill-opacity": 0.35 } },
          { id: "lead-shape-line", type: "line", paint: { "line-color": "#b45309", "line-width": 2 } },
        ],
      },
    ],
    [lead.polygon],
  );
  const lons = lead.polygon.map((p) => p[0]);
  const lats = lead.polygon.map((p) => p[1]);
  const pad = 0.004;
  const bounds: [[number, number], [number, number]] = [
    [Math.min(...lons) - pad, Math.min(...lats) - pad],
    [Math.max(...lons) + pad, Math.max(...lats) + pad],
  ];

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      await postFeedback(lead.id, { inspector, outcome, note: note.trim() || null, visited_at: visitedAt || null });
      setNote("");
      feedbackState.reload();
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Saving failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <LeadShell>
      <div className="mt-5 flex flex-wrap items-center gap-2">
        {lead.use_class === "unknown" ? (
          <Badge tone="gray" dot>
            Site check · class unknown, not a lead
          </Badge>
        ) : failedFilters(lead).length ? (
          <Badge tone="gray" dot>
            Candidate · fails filter {failedFilters(lead).join(", ")}, not a lead
          </Badge>
        ) : (
          <Badge tone="amber" dot>
            Lead <span className="capitalize">{lead.use_class}</span>
          </Badge>
        )}
        <Badge tone={visits.length ? "blue" : "gray"} dot>
          {visits.length ? `${visits.length} visit${visits.length > 1 ? "s" : ""}` : "Not visited"}
        </Badge>
        <CodeTag>{lead.id}</CodeTag>
        <span className="ml-auto text-[12px] text-ink-3">
          {lead.district}
          {lead.regency ? `, ${lead.regency}` : ""}
        </span>
      </div>

      <div className="mt-3">
        <h1 className="flex items-center gap-2 font-display text-[30px] font-medium capitalize leading-9 tracking-[-0.5px] text-ink">
          <Building size={22} className="text-ink-3" />
          {lead.use_class === "unknown" ? "Unknown class" : lead.use_class} · {lead.district}
        </h1>
        <p className="mt-1 text-[12px] text-ink-3">
          {coordinateText(lead.lat, lead.lon)} · conservation zone {zoneLabel(lead.zone)} ·{" "}
          <a
            className="text-blue-700 hover:underline"
            href={`https://www.google.com/maps/search/?api=1&query=${lead.lat},${lead.lon}`}
            target="_blank"
            rel="noreferrer"
          >
            open in maps
          </a>
        </p>
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_420px] items-start gap-5">
        <div className="space-y-4">
          <Card padded={false} className="overflow-hidden">
            <div className="border-b border-line px-4 py-3">
              <SectionTitle right={<CodeTag>Sentinel-2, dry season</CodeTag>}>Before and after</SectionTitle>
            </div>
            <div className="grid grid-cols-2 gap-px bg-line">
              {([2022, 2026] as const).map((year) => (
                <figure key={year} className="bg-surface">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={leadImageUrl(lead.id, year)}
                    alt={`Sentinel-2 true colour ${year} around lead ${lead.id}`}
                    className="aspect-square w-full [image-rendering:pixelated]"
                  />
                  <figcaption className="px-3 py-2 text-[11px] text-ink-3">
                    {year === 2022 ? "2022, when the zone map was made" : "2026, new roof outlined"} · 640 m across
                  </figcaption>
                </figure>
              ))}
            </div>
          </Card>

          <Card padded={false} className="overflow-hidden">
            <div className="border-b border-line px-4 py-3">
              <SectionTitle right={<CodeTag>Inspector only</CodeTag>}>New-roof footprint</SectionTitle>
            </div>
            <div className="h-[300px]">
              <OverlayMap overlays={overlays} bounds={bounds} />
            </div>
            <p className="px-4 py-3 text-[11px] leading-[16px] text-ink-3">
              Footprint traced on 10 m pixels (about one pixel of error at the edges). A patch can hold more
              than one building.
            </p>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <div className="space-y-2.5 text-[12px]">
              <Row icon={<Ruler size={14} />} label="New roof">
                {num(lead.footprint_m2)} m²
                <span className="block text-[11px] font-normal text-ink-3">roofed from the {lead.built_year} dry season</span>
              </Row>
              <Row icon={<ListChecks size={14} />} label="Filters 1-4">
                {["1", "2", "3", "4"]
                  .map((key) => `${key} ${lead.filters[key] === true ? "✓" : lead.filters[key] === false ? "✗" : "n/a"}`)
                  .join(" · ")}
              </Row>
              <Row icon={<Layers size={14} />} label="Conservation zone">
                {zoneLabel(lead.zone)}
              </Row>
              <Row icon={<Droplets size={14} />} label="PDAM supply">
                <span className="block max-w-[220px]">{lead.pdam_status}</span>
              </Row>
              <Row icon={<Building size={14} />} label="Water-use class">
                <span className="capitalize">{lead.use_class}</span>
                {lead.use_class_basis && (
                  <span className="block text-[11px] font-normal text-ink-3">{lead.use_class_basis}</span>
                )}
              </Row>
              <Row icon={<Waves size={14} />} label="Sinking here">
                {lead.sinking_mm_yr == null ? "—" : `${lead.sinking_mm_yr} mm/yr`}
                <span className="ml-1 text-[11px] font-normal text-ink-3">2023–26, context</span>
              </Row>
            </div>
          </Card>

          <Card>
            <p className="text-[12px] font-medium text-ink">Provenance</p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {Object.entries(lead.labels).map(([key, label]) => (
                <span key={key} className="inline-flex items-center gap-1 text-[11px] text-ink-3">
                  <span className="capitalize">{key.replaceAll("_", " ")}</span>
                  <LabelBadge label={label} dot={false} />
                </span>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-1">
              {lead.source_ids.map((id) => (
                <CodeTag key={id}>{id}</CodeTag>
              ))}
            </div>
          </Card>

          <Card>
            <p className="text-[12px] font-medium text-ink">Record field result</p>
            <form onSubmit={submit} className="mt-3 space-y-2.5 text-[12px]">
              <div className="grid grid-cols-2 gap-1.5">
                {OUTCOMES.map((item) => (
                  <label
                    key={item.key}
                    className={cn(
                      "flex cursor-pointer items-center gap-2 rounded-md border px-2.5 py-2",
                      outcome === item.key ? "border-blue-700 bg-blue-50 text-blue-700" : "border-line-strong text-ink-2",
                    )}
                  >
                    <input
                      type="radio"
                      name="outcome"
                      className="accent-blue-700"
                      checked={outcome === item.key}
                      onChange={() => setOutcome(item.key)}
                    />
                    {item.label}
                  </label>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <input
                  required
                  value={inspector}
                  onChange={(event) => setInspector(event.target.value)}
                  placeholder="Inspector name"
                  className="h-8 rounded-md border border-line-strong px-2.5 text-ink"
                />
                <input
                  type="date"
                  value={visitedAt}
                  onChange={(event) => setVisitedAt(event.target.value)}
                  className="h-8 rounded-md border border-line-strong px-2.5 text-ink"
                />
              </div>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="What did you find? (optional)"
                rows={2}
                className="w-full rounded-md border border-line-strong px-2.5 py-1.5 text-ink"
              />
              {saveError && <p className="text-[11px] text-red-700">{saveError}</p>}
              <Button type="submit" variant="primary" size="sm" icon={<ClipboardCheck size={14} />} disabled={saving || !inspector.trim()}>
                {saving ? "Saving…" : "Save visit"}
              </Button>
            </form>
            {visits.length > 0 && (
              <ul className="mt-3 space-y-2 border-t border-line pt-3">
                {visits.map((visit) => (
                  <li key={visit.id} className="text-[11px] leading-[16px] text-ink-2">
                    <span className="font-medium text-ink">{OUTCOMES.find((o) => o.key === visit.outcome)?.label}</span> ·{" "}
                    {visit.visited_at} · {visit.inspector}
                    {visit.note && <span className="block text-ink-3">{visit.note}</span>}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <InfoNote tone="gray" icon={<ClipboardCheck size={14} />}>
            A lead is a reason to visit, not a verdict. Each saved visit feeds the hit rate per class (V6).
          </InfoNote>

          <Link href="/leads">
            <Button variant="secondary" size="md" icon={<ArrowLeft size={15} />}>
              Back to all leads
            </Button>
          </Link>
        </div>
      </div>
    </LeadShell>
  );
}
