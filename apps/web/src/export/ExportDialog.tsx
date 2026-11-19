"use client";

import { Check, Download, Info, Lock, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Button, TraceTags, cn } from "@/components/ui";
import { CONE_WIDTHS, HOT_SPOTS, rankOf, toLonLat } from "@/data/run";
import { useT } from "@/i18n";
import { useStore } from "@/state";

type Lang = "id" | "en" | "both";
type Version = "regulator" | "public";

const FILES = [
  { key: "geojson", title: "Hot spots · GeoJSON", text: "Position, 500 m cell, volume at low, mid and high B, 90% ranges, stability, land use", mb: 0.068, size: "68 KB" },
  { key: "rasters", title: "Rasters · GeoTIFF (cloud-optimised)", text: "Vertical, east-west, seasonal amplitude, change dates, background, uncertainty", mb: 184, size: "184 MB" },
  { key: "cards", title: "Model card and data card · PDF", text: "What the run is for, what it must not be used for, known limits", mb: 1.2, size: "1.2 MB" },
] as const;

type FileKey = (typeof FILES)[number]["key"];

/** 11 · Export audit (U5, O5). Opened from the top bar or the audit list. */
export function ExportDialog() {
  const { exportOpen, setExportOpen, role } = useStore();
  const { pick } = useT();
  const canRegulator = role === "regulator" || role === "analyst";
  const [sheet, setSheet] = useState(true);
  const [lang, setLang] = useState<Lang>("id");
  const [version, setVersion] = useState<Version>("regulator");
  const [files, setFiles] = useState<Record<FileKey, boolean>>({ geojson: true, rasters: true, cards: true });
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!exportOpen) return;
    setDone(false);
    setVersion(canRegulator ? "regulator" : "public");
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setExportOpen(false);
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [exportOpen, canRegulator, setExportOpen]);

  if (!exportOpen) return null;

  const count = (sheet ? 1 : 0) + FILES.filter((f) => files[f.key]).length;
  const mb = (sheet ? 0.7 : 0) + FILES.filter((f) => files[f.key]).reduce((s, f) => s + f.mb, 0);
  const sizeText = mb >= 1 ? `about ${Math.round(mb)} MB` : `about ${Math.round(mb * 1000)} KB`;

  const run = () => {
    if (files.geojson) downloadGeoJSON(version);
    if (sheet) window.open(`/sheet?lang=${lang}&version=${version}`, "_blank");
    setDone(true);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30"
      onPointerDown={(e) => e.target === e.currentTarget && setExportOpen(false)}
    >
      <div role="dialog" aria-modal aria-label="Export audit" className="flex max-h-[calc(100vh-40px)] w-[600px] flex-col overflow-hidden rounded-xl bg-surface shadow-[0_20px_60px_rgba(0,0,0,0.25)]">
        <div className="flex flex-col gap-1.5 px-6 pb-4 pt-5">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-semibold leading-[30px] tracking-[-0.01em]">{pick("Export audit", "Ekspor audit")}</h2>
            <TraceTags codes={["U5", "O5"]} />
            <span className="flex-1" />
            <button aria-label="Close" onClick={() => setExportOpen(false)} className="grid size-7 place-items-center rounded-md hover:bg-subtle">
              <X size={16} strokeWidth={2} />
            </button>
          </div>
          <p className="text-xs leading-4 text-ink-2">
            Run R-0007 · Semarang–Demak · Jan 2015 – Oct 2026 · signed off by A. Wibowo (BIG)
          </p>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-0 overflow-y-auto px-6 pb-5">
          <div className={cn("flex flex-col gap-3 rounded-[10px] border-2 p-4", sheet ? "border-primary" : "border-line")}>
            <Check2 on={sheet} onChange={setSheet}>
              <span className="text-[13px] font-medium">Audit sheet</span>
              <span className="text-[11px] text-ink-3">PDF · 2 pages</span>
            </Check2>
            <p className="-mt-1 pl-[30px] text-[13px] leading-[19px] text-ink-2">
              Map, ranked list with volumes for three cone widths and 90% ranges, validation summary, data sources and sign-off.
            </p>
            <div className={cn("flex flex-col gap-2 pl-[30px]", !sheet && "pointer-events-none opacity-40")}>
              <span className="eyebrow mt-1 text-ink">Language</span>
              <div className="flex w-fit rounded-md bg-subtle p-0.5">
                {(
                  [
                    ["id", "Bahasa Indonesia"],
                    ["en", "English"],
                    ["both", "Both"],
                  ] as const
                ).map(([k, l]) => (
                  <button
                    key={k}
                    onClick={() => setLang(k)}
                    className={cn("h-[26px] rounded px-2.5 text-[13px] leading-4", lang === k ? "bg-surface text-ink shadow-sm" : "text-ink-2")}
                  >
                    {l}
                  </button>
                ))}
              </div>
              <span className="eyebrow mt-2 text-ink">Version</span>
              <Radio on={version === "regulator"} disabled={!canRegulator} onClick={() => setVersion("regulator")}>
                Regulator: includes permit match
                <Lock size={13} strokeWidth={1.9} className="text-ink-3" />
              </Radio>
              <Radio on={version === "public"} onClick={() => setVersion("public")}>
                Public: cells and land-use classes only
              </Radio>
            </div>
          </div>

          <span className="eyebrow mb-2.5 mt-5 text-ink">Data</span>
          <div className="overflow-hidden rounded-[10px] border border-line">
            {FILES.map((f) => (
              <div key={f.key} className="flex flex-col gap-1 border-b border-line px-4 py-2.5">
                <div className="flex items-start">
                  <Check2 on={files[f.key]} onChange={(v) => setFiles((x) => ({ ...x, [f.key]: v }))}>
                    <span className="text-[13px] font-medium">{f.title}</span>
                  </Check2>
                  <span className="flex-1" />
                  <span className="text-[11px] leading-[14px] text-ink-3">{f.size}</span>
                </div>
                <p className="max-w-[400px] pl-[30px] text-xs leading-4 text-ink-2">{f.text}</p>
              </div>
            ))}
            <div className="flex flex-col gap-1 px-4 py-3 text-ink-3">
              <div className="flex items-center">
                <span className="flex items-center gap-3">
                  <span className="size-4 rounded-[3px] border border-line" />
                  <span className="text-[13px]">Well records</span>
                </span>
                <span className="flex-1" />
                <Lock size={14} strokeWidth={1.9} />
              </div>
              <p className="pl-[28px] text-xs leading-4">Restricted data from the Geological Agency, never exported</p>
            </div>
          </div>

          <div className="mt-4 flex gap-2.5 rounded-lg bg-bg px-4 py-3 text-xs leading-4 text-ink-2">
            <Info size={15} strokeWidth={1.9} className="mt-px flex-none" />
            <span>
              Every volume is labelled as lost storage and a lower bound on extraction, with its 90% range and the cone width
              assumed. Data gaps stay empty in every file.
            </span>
          </div>
        </div>

        <div className="flex h-[66px] flex-none items-center gap-4 border-t border-line bg-bg px-6">
          <span className="text-[11px] leading-[14px] text-ink-3">
            {done ? (
              <span className="text-pass">
                Hot spots saved{sheet ? ", audit sheet opened in a new tab (print to PDF)" : ""}. Rasters and cards are served by the run service.
              </span>
            ) : (
              `${count} files · ${sizeText}`
            )}
          </span>
          <span className="flex-1" />
          <Button variant="ghost" size="md" onClick={() => setExportOpen(false)}>
            {done ? "Close" : "Cancel"}
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={count === 0}
            className="disabled:opacity-50"
            icon={<Download size={16} strokeWidth={2} />}
            onClick={run}
          >
            Export {count} files
          </Button>
        </div>
      </div>
    </div>
  );
}

function Check2({ on, onChange, children }: { on: boolean; onChange: (v: boolean) => void; children: ReactNode }) {
  return (
    <label className="flex cursor-pointer items-center gap-3.5">
      <input type="checkbox" checked={on} onChange={(e) => onChange(e.target.checked)} className="peer absolute opacity-0" />
      <span
        className={cn(
          "grid size-4 flex-none place-items-center rounded-[3px] text-bg peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary",
          on ? "bg-primary" : "bg-surface shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
        )}
      >
        {on && <Check size={12} strokeWidth={2.6} />}
      </span>
      <span className="flex items-baseline gap-2">{children}</span>
    </label>
  );
}

function Radio({ on, disabled, onClick, children }: { on: boolean; disabled?: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      role="radio"
      aria-checked={on}
      disabled={disabled}
      onClick={onClick}
      title={disabled ? "Sign in as a regulator or analyst" : undefined}
      className="flex items-center gap-2.5 text-left text-[13px] leading-[19px] disabled:cursor-not-allowed disabled:opacity-45"
    >
      <span
        className={cn(
          "size-4 flex-none rounded-full bg-surface",
          on ? "shadow-[inset_0_0_0_5px_var(--color-primary)]" : "shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
        )}
      />
      <span className="flex items-center gap-2">{children}</span>
    </button>
  );
}

/** Real export of the demo hot spots, so the button produces a file. */
function downloadGeoJSON(version: Version) {
  const fc = {
    type: "FeatureCollection",
    name: "groundtrace_R-0007_hotspots",
    features: HOT_SPOTS.map((h) => {
      const { lon, lat } = toLonLat(h.x, h.y);
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [+lon.toFixed(5), -+lat.toFixed(5)] },
        properties: {
          cell_id: h.id,
          rank_mid_b: rankOf(h.id, "mid"),
          place: h.place,
          cell_size_m: 500,
          ...Object.fromEntries(
            CONE_WIDTHS.flatMap((c) => [
              [`volume_k_m3yr_b${c.km}`, h.volume[c.key].v],
              [`range90_b${c.km}`, [h.volume[c.key].lo, h.volume[c.key].hi]],
            ]),
          ),
          stability: h.stability,
          land_use: h.landUse,
          ...(version === "regulator" ? { permit_match: h.match.cls } : {}),
          note: "Lost storage, a lower bound on extraction. A lead for inspection, not a verdict.",
        },
      };
    }),
  };
  const blob = new Blob([JSON.stringify(fc, null, 2)], { type: "application/geo+json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `R-0007_hotspots_${version}.geojson`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
