"use client";

import { useRef } from "react";
import { TraceTag, cn } from "@/components/ui";
import { CONE_WIDTHS, type ConeWidth } from "@/data/run";
import { useT } from "@/i18n";

const IDX: Record<ConeWidth, number> = { low: 0, mid: 1, high: 2 };
/** position k (0, 1, 2) on a rail inset 8 px from each end */
const at = (k: number) => `calc(8px + (100% - 16px) * ${k / 2})`;

export function ConeWidthSlider({ value, onChange }: { value: ConeWidth; onChange: (b: ConeWidth) => void }) {
  const track = useRef<HTMLDivElement>(null);
  const { t, n } = useT();
  const i = IDX[value];
  const cur = CONE_WIDTHS[i];

  const pick = (clientX: number) => {
    const r = track.current!.getBoundingClientRect();
    const t = (clientX - r.left - 8) / (r.width - 16);
    onChange(CONE_WIDTHS[Math.max(0, Math.min(2, Math.round(t * 2)))].key);
  };

  return (
    <div className="flex flex-col gap-2.5 rounded-lg border border-line px-4 py-3.5">
      <div className="flex h-[18px] items-center gap-2">
        <span className="text-[13px] font-medium">{t("Cone width B")}</span>
        <TraceTag code="U4" size={11} />
        <span className="flex-1" />
        <span className="text-[11px] leading-[14px] text-primary">
          {n(cur.km)} km · {t(cur.label)}
        </span>
      </div>

      <div
        ref={track}
        role="slider"
        tabIndex={0}
        aria-label="Cone width B"
        aria-valuemin={1}
        aria-valuemax={2}
        aria-valuenow={cur.km}
        aria-valuetext={`${cur.km} km, ${cur.label}`}
        className="relative -mr-[3px] h-[34px] cursor-pointer outline-offset-4"
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          pick(e.clientX);
        }}
        onPointerMove={(e) => e.buttons === 1 && pick(e.clientX)}
        onKeyDown={(e) => {
          if (e.key === "ArrowRight" || e.key === "ArrowUp") onChange(CONE_WIDTHS[Math.min(2, i + 1)].key);
          if (e.key === "ArrowLeft" || e.key === "ArrowDown") onChange(CONE_WIDTHS[Math.max(0, i - 1)].key);
        }}
      >
        <span className="absolute inset-x-2 top-1.5 h-1 rounded-sm bg-subtle" />
        <span
          className="absolute left-2 top-1.5 h-1 rounded-sm bg-primary transition-[width] duration-200"
          style={{ width: `calc((100% - 16px) * ${i / 2})` }}
        />
        {CONE_WIDTHS.map((c, k) => (
          <span
            key={c.key}
            className={cn("absolute top-1 size-2 -translate-x-1 rounded-full", k <= i ? "bg-primary" : "bg-line-strong")}
            style={{ left: at(k) }}
          />
        ))}
        {CONE_WIDTHS.map((c, k) => (
          <span
            key={c.key}
            className={cn(
              "absolute top-5 whitespace-nowrap text-[11px] leading-[14px]",
              k === i ? "text-ink" : "text-ink-3",
              k === 0 ? "-translate-x-2" : k === 2 ? "-translate-x-[calc(100%-8px)]" : "-translate-x-1/2",
            )}
            style={{ left: at(k) }}
          >
            {n(c.km)} km
          </span>
        ))}
        <span
          className="absolute -top-px size-[18px] -translate-x-[9px] rounded-full bg-white shadow-[inset_0_0_0_2px_var(--color-primary),var(--shadow-knob)] transition-[left] duration-200"
          style={{ left: at(i) }}
        />
      </div>

      <p className="text-xs leading-4 text-ink-3">
        {t(
          "Radar alone cannot fix B. Volumes are stored for three widths; moving B rescales every volume while the order barely moves.",
        )}
      </p>
    </div>
  );
}
