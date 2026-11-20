"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  AlertTriangle,
  Droplets,
  FlaskConical,
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";
import type { PipePriority } from "@/lib/api";
import { api } from "@/lib/api";
import { mm3, num } from "@/lib/format";
import { useApi } from "@/lib/use-api";
import { useRole } from "@/components/neraca/role-context";
import { OverlayMap, type OverlayLayer } from "@/components/neraca/overlay-map";
import {
  Badge,
  Button,
  EmptyState,
  ErrorBlock,
  LabelBadge,
  LoadingBlock,
  cn,
} from "@/components/neraca/ui";

type LayerKey = "priority" | "demand4" | "demand16" | "clay" | "supply";

const LAYERS: {
  key: LayerKey;
  label: string;
  sub: string;
  badge?: "lead" | "validated" | "measured";
}[] = [
  { key: "priority", label: "Priority score", sub: "Weighted ranking per 4 km block" },
  {
    key: "demand4",
    label: "Unserved demand · 4 km",
    sub: "Households beyond PDAM + self-supplied business",
    badge: "lead",
  },
  {
    key: "demand16",
    label: "Unserved demand · 16 km",
    sub: "Split checked against the city total",
    badge: "validated",
  },
  {
    key: "clay",
    label: "Soft-clay thickness",
    sub: "Damage potential, metres",
    badge: "measured",
  },
  { key: "supply", label: "New and planned supply", sub: "SPAM service kecamatan" },
];

const WEIGHT_KEYS = ["demand", "damage", "supply"] as const;
type WeightKey = (typeof WEIGHT_KEYS)[number];

const WEIGHT_LABELS: Record<WeightKey, string> = {
  demand: "Unserved groundwater demand",
  damage: "Soft-clay thickness",
  supply: "Not yet on new supply",
};

const DEFAULT_WEIGHTS: Record<WeightKey, number> = {
  demand: 50,
  damage: 35,
  supply: 15,
};

const BLUE_RAMP = ["#eef5fb", "#cfe2f3", "#9cc4e4", "#5d9bcc", "#155a96"];
const BOUNDS: [[number, number], [number, number]] = [
  [110.33, -7.08],
  [110.6, -6.9],
];

const LAYER_VALUE: Record<Exclude<LayerKey, "demand16">, { get: (item: PipePriority) => number; unit: string; digits: number }> = {
  priority: { get: (item) => item.score, unit: "score", digits: 2 },
  demand4: { get: (item) => item.cell.demand_m3_yr / 1e6, unit: "Mm³/yr", digits: 1 },
  clay: { get: (item) => item.cell.clay_m, unit: "m clay", digits: 0 },
  supply: { get: (item) => item.cell.supply_m3_yr / 1e6, unit: "Mm³/yr SPAM", digits: 1 },
};

function LayerBadge({ tone }: { tone: "lead" | "validated" | "measured" }) {
  if (tone === "lead") {
    return (
      <Badge tone="amber" dot>
        Lead
      </Badge>
    );
  }
  if (tone === "validated") return <LabelBadge label="TESTED" dot={false} />;
  return <LabelBadge label="MEASURED" dot={false} />;
}

export default function PipesPage() {
  const { role } = useRole();
  const [layer, setLayer] = useState<LayerKey>("priority");
  const [weights, setWeights] = useState<Record<WeightKey, number>>({
    ...DEFAULT_WEIGHTS,
  });

  const weightKey = `${weights.demand}-${weights.damage}-${weights.supply}`;
  const priorityState = useApi(`pipe-priority-${weightKey}-${role}`, (signal) =>
    api.pipePriority(
      {
        demand: weights.demand / 100,
        damage: weights.damage / 100,
        supply: weights.supply / 100,
      },
      role,
      signal,
    ),
  );
  const spamState = useApi(`pipe-spam-${role}`, (signal) => api.spamTest(role, signal));
  const priority = priorityState.data;
  const unavailableReason =
    priority?.status === "unavailable" ? priority.reason : null;
  const items = useMemo(
    () => (priority?.status === "available" ? priority.items : []),
    [priority],
  );
  const shown = LAYER_VALUE[layer === "demand16" ? "demand4" : layer];
  const values = items.map(shown.get);
  const low = Math.min(...values);
  const high = Math.max(...values);
  const overlays = useMemo<OverlayLayer[]>(
    () => [
      {
        id: "blocks",
        data: {
          type: "FeatureCollection",
          features: items.map((item) => ({
            type: "Feature",
            properties: {
              id: item.cell.id,
              t: high > low ? (shown.get(item) - low) / (high - low) : 0,
              served: item.cell.supply_m3_yr > 0,
            },
            geometry: { type: "Polygon", coordinates: [item.cell.polygon] },
          })),
        },
        layers: [
          {
            id: "blocks-fill",
            type: "fill",
            paint: {
              "fill-color": ["interpolate", ["linear"], ["get", "t"], ...BLUE_RAMP.flatMap((c, i) => [i / 4, c])] as never,
              "fill-opacity": 0.72,
            },
          },
          {
            id: "blocks-line",
            type: "line",
            paint: {
              "line-color": ["case", ["get", "served"], "#b45309", "#ffffff"] as never,
              "line-width": ["case", ["get", "served"], 2, 1] as never,
              "line-dasharray": [2, 1],
            },
          },
        ],
      },
    ],
    [items, shown, low, high],
  );
  const spam = spamState.data;
  const total = weights.demand + weights.damage + weights.supply;

  const setWeight = (key: WeightKey, raw: number) => {
    const value = Math.max(0, Math.min(100, Math.round(raw)));
    setWeights((previous) => {
      const others = WEIGHT_KEYS.filter((item) => item !== key);
      const remaining = 100 - value;
      const otherSum = others.reduce((sum, item) => sum + previous[item], 0);
      const firstRaw =
        otherSum > 0
          ? (previous[others[0]] / otherSum) * remaining
          : remaining / others.length;
      const first = Math.max(0, Math.min(remaining, Math.round(firstRaw)));
      return {
        ...previous,
        [key]: value,
        [others[0]]: first,
        [others[1]]: remaining - first,
      };
    });
  };

  return (
    <div className="grid h-[calc(100vh-56px)] grid-cols-[320px_minmax(0,1fr)_400px] overflow-hidden">
      <aside className="flex min-h-0 flex-col gap-[18px] overflow-y-auto border-r border-line bg-surface px-5 pb-4 pt-5">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[18px] font-semibold leading-6 text-ink">
            Pipes instead of pumps
          </h1>
          <p className="text-[13px] leading-[19px] text-ink-2">
            Where piped surface water would replace the most groundwater, weighted by
            how much damage sinking does there.
          </p>
        </div>

        <div className="flex flex-col gap-1">
          <p className="text-[12px] font-medium leading-4 text-ink-2">Map shows</p>
          {LAYERS.map((item) => {
            const active = layer === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setLayer(item.key)}
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
                <span className="flex min-w-0 flex-col">
                  <span className="flex flex-wrap items-center gap-1">
                    <span className="text-[12.5px] font-medium leading-[18px] text-ink">
                      {item.label}
                    </span>
                    {item.badge && <LayerBadge tone={item.badge} />}
                  </span>
                  <span className="text-[12px] leading-4 text-ink-3">{item.sub}</span>
                </span>
              </button>
            );
          })}
          <p className="px-2.5 pt-1 text-[11px] leading-[15px] text-ink-3">
            Each layer colours the same 22 blocks. The 16 km validated split exists for one cell
            only (west and central Semarang), so it is quoted, not mapped.
          </p>
        </div>

        <div className="rounded-lg bg-bg p-4">
          <div className="flex items-center gap-1.5">
            <SlidersHorizontal size={14} className="text-ink-2" />
            <p className="text-[12px] font-medium leading-4 text-ink">Weights</p>
          </div>
          <div className="mt-3 flex flex-col gap-3.5">
            {WEIGHT_KEYS.map((key) => (
              <div key={key}>
                <div className="flex items-center justify-between gap-3">
                  <label
                    htmlFor={`weight-${key}`}
                    className="text-[12px] leading-4 text-ink-2"
                  >
                    {WEIGHT_LABELS[key]}
                  </label>
                  <span className="font-mono text-[11px] leading-4 text-ink">
                    {weights[key]}%
                  </span>
                </div>
                <input
                  id={`weight-${key}`}
                  type="range"
                  min={0}
                  max={100}
                  step={1}
                  value={weights[key]}
                  onChange={(event) => setWeight(key, Number(event.target.value))}
                  className="mt-1.5 h-1.5 w-full cursor-pointer accent-blue-700"
                />
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <p className="text-[11px] leading-4 text-ink-3">
              Weights sum to {total}%.
            </p>
            <button
              onClick={() => setWeights({ ...DEFAULT_WEIGHTS })}
              className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-700"
            >
              <RotateCcw size={11} /> Reset
            </button>
          </div>
          {priorityState.loading && priority ? (
            <p className="mt-2 text-[11px] leading-4 text-ink-3">Re-ranking…</p>
          ) : null}
          {priorityState.error ? (
            <div className="mt-3">
              <ErrorBlock message={priorityState.error} retry={priorityState.reload} />
            </div>
          ) : null}
        </div>

        <div className="flex-1" />

        <p className="text-[11px] leading-[15px] text-ink-3">
          Demand: NERACA demand model (4 km Lead, 16 km Validated). Clay: soft-clay
          thickness layer. Supply: SPAM Semarang Barat service kecamatan.
        </p>
      </aside>

      <section className="relative min-h-0 overflow-hidden bg-sea">
        <OverlayMap overlays={overlays} bounds={BOUNDS} />

        <div className="pointer-events-none absolute left-4 top-4 flex max-w-[470px] items-start gap-2 rounded-lg bg-surface px-3 py-2 shadow-card">
          <LabelBadge label="SCENARIO" dot={false} />
          <p className="text-[12px] leading-4 text-ink-2">
            Ranking follows your weights. Ranking inside a city failed validation (file 12), so
            this is a planning priority, not a prediction of where sinking will stop.
          </p>
        </div>

        {unavailableReason && (
          <div className="absolute left-4 top-[86px] flex w-[490px] items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/95 px-3 py-2.5 shadow-card">
            <AlertTriangle size={15} className="mt-0.5 shrink-0 text-amber-800" />
            <div>
              <p className="text-[12px] font-semibold leading-4 text-amber-800">
                Priority cells are not published
              </p>
              <p className="mt-1 text-[11px] leading-[16px] text-amber-800">
                {unavailableReason}
              </p>
            </div>
          </div>
        )}

        <div className="absolute left-4 top-[96px] w-[270px] rounded-xl bg-surface p-3.5 shadow-pop">
          <div className="flex items-center gap-1.5">
            <span className="flex size-5 items-center justify-center rounded-full bg-amber-100 text-amber-800">
              <Droplets size={12} />
            </span>
            <p className="text-[13px] font-semibold leading-[18px] text-ink">
              {spam?.name ?? "SPAM Semarang Barat"}
            </p>
          </div>
          <p className="mt-1.5 text-[12px] leading-4 text-ink-2">
            Since Jan 2024 ·{" "}
            {spam?.uptake_lps_2024_01 == null
              ? "605 L/s"
              : `${num(spam.uptake_lps_2024_01)} L/s`}
          </p>
          <p className="mt-0.5 text-[11px] leading-4 text-ink-3">
            {spam?.connections_actual_2024_09 == null
              ? "47,261 connections by Sep 2024"
              : `${num(spam.connections_actual_2024_09)} connections by Sep 2024`}
          </p>
        </div>

        <div className="absolute bottom-[200px] left-4 w-[330px] rounded-lg bg-navy-900 px-3 py-2 text-white shadow-pop">
          <p className="text-[10px] uppercase tracking-[0.6px] text-white/60">
            Validated 16 km cell
          </p>
          <p className="mt-1 text-[12px] font-medium leading-4">
            27.9 / 43.8 / 54.7 Mm³{" "}
            <span className="font-normal text-white/70">(P10/P50/P90)</span>
          </p>
        </div>

        <div className="absolute bottom-4 left-4 w-[330px] rounded-lg bg-surface p-3 shadow-card">
          <p className="text-[12px] font-medium leading-4 text-ink">
            {LAYERS.find((item) => item.key === layer)?.label}
            {layer === "demand16" ? " (not per block; shown: 4 km demand)" : ""}
          </p>
          <div className="mt-2 flex gap-0.5 overflow-hidden rounded-sm">
            {BLUE_RAMP.map((colour) => (
              <div
                key={colour}
                className="h-2.5 flex-1"
                style={{ backgroundColor: colour }}
              />
            ))}
          </div>
          <div className="mt-1 flex justify-between font-mono text-[10px] leading-3 text-ink-3">
            <span>{items.length ? num(low, shown.digits) : "—"}</span>
            <span>{shown.unit}</span>
            <span>{items.length ? num(high, shown.digits) : "—"}</span>
          </div>
          <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[10.5px] text-ink-2">
            <span className="inline-flex items-center gap-1.5">
              <span className="size-2.5 rounded-[2px] border border-dashed border-amber-600 bg-amber-100" />
              Served by new SPAM
            </span>
          </div>
          <p className="mt-2 text-[10px] leading-[14px] text-ink-3">
            22 blocks of 4 km, the grid of the demand model. SPAM supply is spread over Semarang
            Barat, Tugu and Ngaliyan by area, because the service map is not public.
          </p>
        </div>
      </section>

      <aside className="flex min-h-0 flex-col overflow-hidden border-l border-line bg-surface">
        <div className="border-b border-line px-5 pb-3 pt-5">
          <h2 className="text-[18px] font-semibold leading-6 text-ink">
            Where pipes come first
          </h2>
          <p className="mt-1 text-[12px] leading-4 text-ink-3">
            4 km blocks ranked by your weights. The score is a planning priority.
          </p>
        </div>

        <div className="grid grid-cols-[18px_minmax(0,1fr)_58px_46px_58px] items-center gap-2 bg-bg px-5 py-2 font-mono text-[9.5px] tracking-[0.4px] text-ink-3">
          <span>#</span>
          <span>BLOCK</span>
          <span className="text-right">DEMAND</span>
          <span className="text-right">CLAY</span>
          <span className="text-right">SCORE</span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {priorityState.loading && !priority ? (
            <LoadingBlock label="Ranking cells…" />
          ) : priorityState.error ? (
            <ErrorBlock message={priorityState.error} retry={priorityState.reload} />
          ) : items.length > 0 ? (
            <div>
              {items.map((item, index) => (
                <div
                  key={item.cell.id}
                  className="grid grid-cols-[18px_minmax(0,1fr)_58px_46px_58px] items-center gap-2 border-b border-line py-2"
                >
                  <span className="font-mono text-[11px] text-ink-3">{index + 1}</span>
                  <div className="min-w-0">
                    <p className="truncate text-[12.5px] font-medium leading-4 text-ink" title={item.cell.id}>
                      {item.cell.districts.join(", ") || item.cell.id}
                    </p>
                    <div className="mt-1 h-1 overflow-hidden rounded-full bg-subtle">
                      <div
                        className="h-full rounded-full bg-blue-700"
                        style={{ width: `${Math.max(2, item.score * 100)}%` }}
                      />
                    </div>
                  </div>
                  <p className="text-right text-[11px] leading-4 text-ink">
                    {mm3(item.cell.demand_m3_yr, 1)}
                  </p>
                  <p className="text-right text-[11px] leading-4 text-ink" title="Mean soft-clay thickness">
                    {num(item.cell.clay_m)} m
                  </p>
                  <p className="text-right font-mono text-[11px] leading-4 text-ink">
                    {num(item.score, 2)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No pipe-priority ranking yet"
              icon={<AlertTriangle size={20} />}
            >
              {unavailableReason ??
                "The backend returned no ranking cells. Nothing is ranked or invented."}
              <p className="mt-3 font-mono text-[10px] text-ink-3">
                requested: {weights.demand}% demand · {weights.damage}% clay ·{" "}
                {weights.supply}% supply
              </p>
            </EmptyState>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-line px-5 py-3">
          <p className="max-w-[190px] text-[11px] leading-4 text-ink-3">
            Demand in Mm³/yr (4 km, not validated at this scale). Clay: mean thickness, m.
          </p>
          <Link href="/pipes/spam">
            <Button
              variant="secondary"
              size="sm"
              icon={<FlaskConical size={14} />}
            >
              SPAM test
            </Button>
          </Link>
        </div>
      </aside>
    </div>
  );
}
