import type { Legend as LegendT } from "@/data/layers";

export function GapSwatch() {
  return (
    <svg width="18" height="12" viewBox="0 0 18 12" className="flex-none" aria-hidden>
      <defs>
        <pattern id="hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="4" height="4" fill="#e6e2d9" />
          <line x1="0" y1="0" x2="0" y2="4" stroke="#847e74" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="18" height="12" fill="url(#hatch)" />
    </svg>
  );
}

export function Legend({ legend }: { legend: LegendT }) {
  return (
    <div className="flex w-[268px] flex-col gap-2 rounded-md border border-line bg-white/94 px-3 py-2.5">
      <div className="text-xs font-medium">{legend.title}</div>
      {legend.kind === "ramp" ? (
        <>
          <div className="h-2 rounded-[2px]" style={{ background: `linear-gradient(90deg, ${legend.stops.join(", ")})` }} />
          <div className="flex justify-between text-[11px] leading-[14px] text-ink-3">
            {legend.ticks.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </>
      ) : (
        <div className="grid grid-cols-[repeat(4,auto)] justify-start gap-x-2.5 gap-y-1 text-[11px] leading-[14px] text-ink-2">
          {legend.items.map((i) => (
            <span key={i.label} className="flex items-center gap-[5px]">
              <i className="size-2.5 rounded-[2px] opacity-85" style={{ background: i.color }} />
              {i.label}
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-2 text-xs leading-4 text-ink-2">
        <GapSwatch />
        <span>No data: radar signal lost over fish ponds and rice fields. Drawn as gaps, never interpolated.</span>
      </div>
    </div>
  );
}
