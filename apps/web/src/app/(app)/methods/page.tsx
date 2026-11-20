"use client";

import Link from "next/link";
import { useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  Coins,
  Droplets,
  ExternalLink,
  Layers,
  MapPin,
  ShieldCheck,
  Waves,
} from "lucide-react";
import type { Source, ValidationCheck } from "@/lib/api";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import {
  Badge,
  Button,
  Card,
  ErrorBlock,
  LabelBadge,
  LoadingBlock,
  SectionTitle,
} from "@/components/neraca/ui";

type GroupKey = "radar" | "records" | "water";

const LABELS: {
  tone: "blue" | "amber" | "gray";
  name: string;
  copy: string;
  foot: string;
}[] = [
  {
    tone: "blue",
    name: "Validated",
    copy: "Checked against an independent truth with a pass mark set in advance.",
    foot: "16 km demand split · Sentinel-1 rate maps tied to GNSS",
  },
  {
    tone: "amber",
    name: "Lead",
    copy: "Useful for planning or a visit, not yet checked. Always shown as a range.",
    foot: "4 km demand · tax gap · inspection leads · pipe ranking",
  },
  {
    tone: "gray",
    name: "Data",
    copy: "Official records shown as published, with year and source.",
    foot: "ESDM declared volumes · NPA price table · conservation zones",
  },
];

const STEPS = [
  {
    title: "Sinking",
    icon: Activity,
    body: "Sentinel-1 radar, two directions (LiCSAR 076D / 127A). Rates 2018–22 and 2023–26, tied to GNSS.",
  },
  {
    title: "Why it sinks",
    icon: Layers,
    body: "About 80% of the pattern follows soft-clay thickness; the rest is a regional fall in deep-aquifer pressure. So sinking does not point at single wells.",
  },
  {
    title: "How much is used",
    icon: Droplets,
    body: "Kota Semarang: validated 16 km split, 27.9 / 43.8 / 54.7 Mm³ (P10/P50/P90). The other 34 kab/kota: a regency model from BPS population, household water sources and OSM industrial land, not validated.",
  },
  {
    title: "Who and where",
    icon: MapPin,
    body: "Declared volumes, NPA prices, conservation zones, new buildings, PDAM coverage and SPAM service areas.",
  },
];

const RADAR_IDS = new Set([
  "LICSAR",
  "X08",
  "X05",
  "EXP04",
  "EXP08",
  "EXP09",
  "EXP13",
  "EXP14",
  "ADWR",
  "EXP05",
  "S2-L2A",
  "IO-LULC",
]);

const RECORD_IDS = new Set([
  "PERGUB-7-2025",
  "ESDM-NPA-2020",
  "ESDM-NPA-2021",
  "ESDM-NPA-2022",
  "ESDM-NPA-2023",
  "BPS-JATENG",
  "BPS-POP-JT",
  "BPS-WATER-JT",
  "PERDA-SMG-2024",
  "PERDA-10-2023",
  "TERC-2024",
  "DDTC-SMG",
  "LO-2022",
  "ZONE-2022",
  "APBD-SMG",
  "PERDA-SMG-2-2024",
  "KEPGUB-211-2025",
  "PERGUB-19-2017",
  "PERGUB-54-2018",
  "BPS-SMG-DA-2024",
  "DEMAK-DINPUTARU-2025",
  "DEMAK-KK-2025",
  "GADM",
]);

const GROUPS: { key: GroupKey; title: string }[] = [
  { key: "radar", title: "Radar and ground" },
  { key: "records", title: "Records and law" },
  { key: "water", title: "Buildings and water" },
];

const MODULE_LABEL = { A: "Accounts", B: "Leads", C: "Pipes" } as const;

const DOT_TONE: Record<string, string> = {
  OFFICIAL: "bg-green-700",
  MEASURED: "bg-blue-500",
  TESTED: "bg-blue-700",
  CALCULATED: "bg-ink-3",
  WEAK: "bg-amber-500",
  SCENARIO: "bg-purple-700",
  MISSING: "bg-red-700",
};

function groupOf(id: string): GroupKey {
  if (RADAR_IDS.has(id)) return "radar";
  if (RECORD_IDS.has(id)) return "records";
  return "water";
}

function CheckBadge({ check }: { check: ValidationCheck }) {
  if (check.status === "done") {
    return (
      <Badge tone={check.result === "fail" ? "red" : "blue"} dot>
        done · {check.result}
      </Badge>
    );
  }
  if (check.status === "planned") {
    return (
      <Badge tone="amber" dot>
        planned · waiting
      </Badge>
    );
  }
  return (
    <Badge tone="gray" dot>
      waiting
    </Badge>
  );
}

function SourceRow({ source }: { source: Source }) {
  const name = (
    <span className="text-[12px] font-medium leading-[16px] text-ink">
      {source.name}
    </span>
  );
  return (
    <li className="flex items-start gap-2 border-b border-line/70 py-1.5 last:border-b-0">
      <span
        className={`mt-[6px] size-1.5 shrink-0 rounded-full ${DOT_TONE[source.label] ?? "bg-ink-3"}`}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-1">
          {source.url ? (
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="hover:text-blue-700"
            >
              {name}
            </a>
          ) : (
            name
          )}
          {source.url && (
            <ExternalLink size={10} className="mt-1 shrink-0 text-ink-3" />
          )}
        </div>
        <p className="mt-0.5 text-[10px] leading-[14px] text-ink-3">
          {source.publisher}
          {source.accessed ? ` · ${source.accessed}` : ""}
        </p>
      </div>
      <LabelBadge label={source.label} dot={false} className="mt-0.5 shrink-0" />
    </li>
  );
}

export default function MethodsPage() {
  const { role } = useRole();
  const validationState = useApi(`methods-validation-${role}`, (signal) =>
    api.validation(role, signal),
  );
  const sourcesState = useApi(`methods-sources-${role}`, (signal) =>
    api.sources(role, signal),
  );

  const checks = useMemo(
    () =>
      [...(validationState.data ?? [])].sort((a, b) => a.code.localeCompare(b.code)),
    [validationState.data],
  );

  const sources = sourcesState.data ?? [];
  const grouped = useMemo(() => {
    const result: Record<GroupKey, Source[]> = { radar: [], records: [], water: [] };
    for (const source of sources) result[groupOf(source.id)].push(source);
    return result;
  }, [sources]);

  return (
    <div className="mx-auto w-full max-w-[1440px] px-10 pb-14 pt-8">
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="font-display text-[30px] font-medium leading-9 tracking-[-0.5px] text-ink">
            How every layer is made
          </h1>
          <p className="mt-2 max-w-[820px] text-[13px] leading-[19px] text-ink-2">
            Every layer either stands on a result this project validated or carries the
            Lead label. Tests are written down before they run.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Link href="/leads/validation">
            <Button variant="secondary" size="md" icon={<ShieldCheck size={15} />}>
              Validation
            </Button>
          </Link>
          <Link href="/accounts">
            <Button variant="secondary" size="md" icon={<Coins size={15} />}>
              Account book
            </Button>
          </Link>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-5">
        {LABELS.map((item) => (
          <Card key={item.name} className="p-5">
            <Badge tone={item.tone} dot>
              {item.name}
            </Badge>
            <p className="mt-4 text-[13px] font-medium leading-[19px] text-ink">
              {item.copy}
            </p>
            <p className="mt-4 text-[11px] leading-[16px] text-ink-3">{item.foot}</p>
          </Card>
        ))}
      </div>

      <div className="mt-5 grid grid-cols-[minmax(0,1.04fr)_minmax(0,0.96fr)] items-start gap-5">
        <Card className="p-6">
          <h2 className="text-[15px] font-semibold leading-5 text-ink">
            From radar and records to the three modules
          </h2>
          <div className="mt-5 space-y-5">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className="flex gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-700">
                    <Icon size={17} />
                  </span>
                  <div>
                    <p className="text-[13px] font-semibold leading-[18px] text-ink">
                      {index + 1} · {step.title}
                    </p>
                    <p className="mt-1 text-[12px] leading-[17px] text-ink-2">
                      {step.body}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-5 grid grid-cols-3 gap-2.5">
            <Link
              href="/accounts"
              className="rounded-lg bg-amber-50 px-3 py-2.5 text-[11px] leading-[15px] text-ink-2 hover:bg-amber-100"
            >
              <span className="font-medium text-ink">Accounts:</span> declared vs
              estimated, priced
            </Link>
            <Link
              href="/leads"
              className="rounded-lg bg-blue-50 px-3 py-2.5 text-[11px] leading-[15px] text-ink-2 hover:bg-blue-100"
            >
              <span className="font-medium text-ink">Leads:</span> new users in no-permit
              zones
            </Link>
            <Link
              href="/pipes"
              className="rounded-lg bg-blue-50 px-3 py-2.5 text-[11px] leading-[15px] text-ink-2 hover:bg-blue-100"
            >
              <span className="font-medium text-ink">Pipes:</span> where piped water
              replaces pumps
            </Link>
          </div>
        </Card>

        <div id="tests" className="scroll-mt-20">
          <Card className="p-6">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-[15px] font-semibold leading-5 text-ink">
                Tests, in the order they run
              </h2>
              <Link
                href="/leads/validation"
                className="text-[11px] font-medium text-blue-700 hover:underline"
              >
                Validation page
              </Link>
            </div>

            {validationState.loading && !validationState.data ? (
              <div className="mt-4">
                <LoadingBlock label="Loading checks…" />
              </div>
            ) : validationState.error ? (
              <div className="mt-4">
                <ErrorBlock
                  message={validationState.error}
                  retry={validationState.reload}
                />
              </div>
            ) : (
              <div className="mt-3">
                {checks.map((check, index) => (
                  <details
                    key={check.code}
                    className="group border-t border-line py-2.5 first:border-t-0"
                  >
                    <summary className="flex cursor-pointer list-none items-start gap-2.5 [&::-webkit-details-marker]:hidden">
                      <span className="mt-0.5 w-3 shrink-0 font-mono text-[10px] text-ink-3">
                        {index + 1}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-[12.5px] font-medium leading-[17px] text-ink">
                          {check.name}
                        </span>
                        <span className="mt-0.5 block text-[10.5px] leading-4 text-ink-3">
                          {check.code} · {MODULE_LABEL[check.module]}
                        </span>
                      </span>
                      <CheckBadge check={check} />
                      <ChevronDown
                        size={13}
                        className="mt-1 shrink-0 text-ink-3 transition-transform group-open:rotate-180"
                      />
                    </summary>
                    <div className="ml-[22px] mt-2 rounded-md bg-bg px-3 py-2 text-[11px] leading-[16px] text-ink-2">
                      <span className="font-medium text-ink">Pass mark. </span>
                      {check.pass_mark}
                      <span className="mt-1 block text-ink-3">
                        Recorded result: {check.result}
                      </span>
                      {check.detail && <span className="mt-1 block text-ink">{check.detail}</span>}
                    </div>
                  </details>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      <div className="mt-5">
        <Card className="p-6">
          <SectionTitle
            right={
              <span className="font-mono text-[10px] text-ink-3">
                {sources.length} entries
              </span>
            }
          >
            Data sources
          </SectionTitle>
          <p className="mt-2 max-w-[900px] text-[12px] leading-[18px] text-ink-2">
            Official records, measured layers and research experiments linked to the app.
            Missing entries stay missing; they are never filled with a guess.
          </p>

          {sourcesState.loading && !sourcesState.data ? (
            <div className="mt-4">
              <LoadingBlock label="Loading sources…" />
            </div>
          ) : sourcesState.error ? (
            <div className="mt-4">
              <ErrorBlock message={sourcesState.error} retry={sourcesState.reload} />
            </div>
          ) : (
            <div className="mt-5 grid grid-cols-3 gap-x-8 gap-y-2">
              {GROUPS.map((group) => (
                <div key={group.key}>
                  <p className="eyebrow text-ink-3">
                    {group.title}
                    <span className="ml-1.5 font-mono text-[9px] tracking-normal">
                      {grouped[group.key].length}
                    </span>
                  </p>
                  <ul className="mt-1.5">
                    {grouped[group.key].map((source) => (
                      <SourceRow key={source.id} source={source} />
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-line pt-3 text-[11px] text-ink-3">
            <span className="inline-flex items-center gap-1.5">
              <AlertTriangle size={12} className="text-amber-600" />
              Missing sources carry the Missing label.
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Waves size={12} />
              Layer labels follow the same three tiers shown above.
            </span>
          </div>
        </Card>
      </div>
    </div>
  );
}
