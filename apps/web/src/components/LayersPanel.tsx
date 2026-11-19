"use client";

import { Check, Layers, Lock } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useT } from "@/i18n";
import { LAYERS } from "@/data/layers";
import { RUN } from "@/data/run";
import { useStore, type ContextLayers } from "@/state";
import { TraceTag, cn } from "./ui";

const CONTEXT: { key: keyof ContextLayers; label: string; locked?: boolean }[] = [
  { key: "hotspots", label: "Hot-spot markers (500 m cells)" },
  { key: "gnss", label: "GNSS stations (InaCORS)" },
  { key: "industrial", label: "Industrial land" },
  { key: "buildings", label: "Building footprints" },
  { key: "permits", label: "Permit register", locked: true },
];

export function LayersPanel() {
  const { layer, setLayer, ctx, toggleCtx, role } = useStore();
  const { t } = useT();
  const pathname = usePathname();
  const router = useRouter();
  const restricted = role === "public" || role === "planner";
  // The background layer opens the planner view (screen 10); any other layer leaves it.
  const pickLayer = (k: typeof layer) => {
    setLayer(k);
    if (k === "background" && (pathname === "/" || pathname === "/audit")) router.push("/planner");
    else if (k !== "background" && pathname === "/planner") router.push("/");
  };
  const shown = pathname === "/planner" ? "background" : layer;
  return (
    <aside className="flex w-[300px] flex-none flex-col gap-1 overflow-y-auto border-r border-line bg-surface p-4">
      <div className="flex h-6 items-center gap-2 pb-1">
        <Layers size={16} strokeWidth={1.9} />
        <span className="text-[15px] font-semibold leading-5">{t("Layers")}</span>
        <span className="flex-1" />
        <span className="text-[11px] leading-[14px] text-ink-3">{RUN.id}</span>
      </div>

      <div className="eyebrow text-ink-3">{t("Research outputs")}</div>
      <div role="radiogroup" aria-label="Research outputs" className="flex flex-col gap-1">
        {LAYERS.map((l) => {
          const on = l.key === shown;
          return (
            <button
              key={l.key}
              role="radio"
              aria-checked={on}
              onClick={() => pickLayer(l.key)}
              className={cn(
                "flex gap-2.5 rounded-md px-2.5 py-2 text-left transition-colors",
                on ? "bg-primary-tint" : "hover:bg-bg",
              )}
            >
              <span
                className={cn(
                  "size-3.5 flex-none rounded-full bg-surface",
                  on ? "shadow-[inset_0_0_0_4.5px_var(--color-primary)]" : "shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
                )}
              />
              <span className="flex min-w-0 flex-col gap-0.5">
                <span className="flex items-center gap-1.5 text-[13px] font-medium leading-4">
                  {t(l.name)}
                  <TraceTag code={l.code} />
                </span>
                <span className="text-xs leading-4 text-ink-3">{t(l.desc)}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="h-2 flex-none" />
      <div className="eyebrow text-ink-3">{t("Context")}</div>
      {CONTEXT.map((c) => (
        <label
          key={c.key}
          title={c.locked && restricted ? t("Regulator only") : undefined}
          className={cn(
            "flex h-[31px] flex-none items-center gap-2.5 rounded-md px-2.5 py-1.5",
            c.locked && restricted ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:bg-bg",
          )}
        >
          <input
            type="checkbox"
            disabled={c.locked && restricted}
            checked={ctx[c.key] && !(c.locked && restricted)}
            onChange={() => toggleCtx(c.key)}
            className="peer pointer-events-none absolute opacity-0"
          />
          <span
            className={cn(
              "grid size-3.5 flex-none place-items-center rounded-[3px] text-bg peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-primary",
              ctx[c.key] && !(c.locked && restricted) ? "bg-primary" : "bg-surface shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
            )}
          >
            {ctx[c.key] && !(c.locked && restricted) && <Check size={12} strokeWidth={2.4} />}
          </span>
          <span className="text-[13px] leading-[19px]">{t(c.label)}</span>
          {c.locked && (
            <>
              <span className="flex-1" />
              <span title={t("Regulator only")}>
                <Lock size={13} strokeWidth={1.9} className="text-ink-3" />
              </span>
            </>
          )}
        </label>
      ))}

      <span className="flex-1" />

      <div className="mt-1 flex flex-none flex-col gap-2 rounded-lg bg-subtle p-3">
        <div className="flex h-5 items-center">
          <span className="text-xs font-medium">{t("Usable pixels")}</span>
          <span className="flex-1" />
          <span className="text-[15px] font-medium leading-5">{RUN.usablePixels}%</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-[3px] bg-line">
          <span className="block h-full rounded-[3px] bg-primary" style={{ width: `${RUN.usablePixels}%` }} />
        </div>
        <p className="-mr-0.5 text-xs leading-4 text-ink-2">
          {t("of built-up and industrial land (64% of the whole area). Hatched areas lost radar signal and stay empty.")}
        </p>
      </div>
      <p className="flex-none text-[11px] leading-[14px] text-ink-3">{t(RUN.footnote)}</p>
    </aside>
  );
}
