import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  Grid2x2,
  MapPin,
} from "lucide-react";
import { Badge, Button, cn } from "@/components/neraca/ui";

const LAND =
  "M 68 176 C 88 146 104 130 142 126 L 186 122 L 212 100 L 258 116 L 300 94 L 346 108 L 392 88 L 434 100 L 478 90 L 520 118 L 538 160 L 522 196 L 542 232 L 516 266 L 530 296 L 492 314 L 454 296 L 426 322 L 388 310 L 356 336 L 316 322 L 282 344 L 246 328 L 208 336 L 176 312 L 140 304 L 120 276 L 88 258 L 96 224 L 70 204 Z";

const PATCHES = [
  { d: "M 60 150 L 140 118 L 190 130 L 175 190 L 110 205 L 74 180 Z", step: 0 },
  { d: "M 140 118 L 212 100 L 258 116 L 248 174 L 190 184 L 175 190 L 190 130 Z", step: 1 },
  { d: "M 212 100 L 258 116 L 300 94 L 330 128 L 310 176 L 248 174 Z", step: 0 },
  { d: "M 300 94 L 346 108 L 372 146 L 348 186 L 310 176 L 330 128 Z", step: 1 },
  { d: "M 346 108 L 392 88 L 412 128 L 398 166 L 354 154 L 372 146 Z", step: 4 },
  { d: "M 392 88 L 434 100 L 470 92 L 478 132 L 430 154 L 412 128 Z", step: 2 },
  { d: "M 434 100 L 478 90 L 520 118 L 514 158 L 470 150 L 478 132 Z", step: 0 },
  { d: "M 514 158 L 538 160 L 522 196 L 500 190 Z", step: 0 },
  { d: "M 470 150 L 514 158 L 500 190 L 468 206 L 430 154 Z", step: 1 },
  { d: "M 398 166 L 430 154 L 468 206 L 440 236 L 398 220 L 348 186 Z", step: 2 },
  { d: "M 348 186 L 398 220 L 372 252 L 330 240 L 310 176 Z", step: 1 },
  { d: "M 310 176 L 330 240 L 290 258 L 250 236 L 248 174 Z", step: 0 },
  { d: "M 250 236 L 290 258 L 268 296 L 222 282 L 206 236 Z", step: 1 },
  { d: "M 190 184 L 248 174 L 250 236 L 206 236 L 182 220 Z", step: 0 },
  { d: "M 110 205 L 175 190 L 182 220 L 170 260 L 120 250 Z", step: 1 },
  { d: "M 170 260 L 206 236 L 222 282 L 240 312 L 196 320 L 168 296 Z", step: 0 },
  { d: "M 290 258 L 330 240 L 372 252 L 356 298 L 310 308 L 268 296 Z", step: 1 },
  { d: "M 372 252 L 398 220 L 440 236 L 460 270 L 420 300 L 356 298 Z", step: 2 },
  { d: "M 460 270 L 468 206 L 500 190 L 522 196 L 542 232 L 516 266 Z", step: 0 },
];

const AMBER_RAMP = ["#fdf0d2", "#f9d48f", "#f2ae52", "#e0812a", "#b5591a"];
const BLUE_RAMP = ["#dcebf7", "#c4ddf0", "#9cc4e4", "#5d9bcc", "#155a96"];

function MiniMap({
  id,
  tone = "amber",
  seaLabel = true,
}: {
  id: string;
  tone?: "amber" | "blue";
  seaLabel?: boolean;
}) {
  const ramp = tone === "blue" ? BLUE_RAMP : AMBER_RAMP;
  return (
    <svg
      viewBox="0 0 640 420"
      preserveAspectRatio="xMidYMid slice"
      className="h-full w-full"
      aria-hidden
    >
      <rect width="640" height="420" fill="#d7e6f2" />
      <g stroke="#c3d8e8" strokeWidth="1" fill="none" opacity="0.7">
        <path d="M -20 340 C 130 300 220 370 380 320 S 580 280 680 330" />
        <path d="M -20 60 C 120 100 210 40 360 80 S 560 120 680 80" />
      </g>
      <path d={LAND} fill="#efece3" stroke="#d8d4c9" strokeWidth="1.4" />
      <clipPath id={`land-${id}`}>
        <path d={LAND} />
      </clipPath>
      <g clipPath={`url(#land-${id})`}>
        {PATCHES.map((patch, index) => (
          <path
            key={index}
            d={patch.d}
            fill={ramp[patch.step]}
            stroke="#f5f4f0"
            strokeWidth="1.2"
          />
        ))}
      </g>
      {seaLabel && (
        <text
          x="86"
          y="84"
          fill="#6f9fc4"
          fontSize="17"
          fontStyle="italic"
          fontFamily="Newsreader, Georgia, serif"
        >
          Laut Jawa
        </text>
      )}
    </svg>
  );
}

function Logo({ size = "md" }: { size?: "md" | "sm" }) {
  const height = size === "sm" ? 24 : 32;
  // the PNG is 5336 x 1379; next/image serves a resized copy
  return (
    <Image
      src="/AquiFair_logo_for_light_bg.png"
      alt="AquiFair"
      width={Math.round((height * 5336) / 1379)}
      height={height}
      priority={size === "md"}
    />
  );
}

const HERO_ROWS = [
  {
    label: "Declared 2023",
    tone: "green" as const,
    tag: "Data",
    value: "10.07",
    unit: "Mm³",
    sub: "Dinas ESDM record, 35 kab/kota",
    accent: false,
  },
  {
    label: "Validated estimate",
    tone: "blue" as const,
    tag: "Validated",
    value: "27.9–54.7",
    unit: "Mm³",
    sub: "P10–P90, 16 km demand split",
    accent: false,
  },
  {
    label: "Taxable gap",
    tone: "gray" as const,
    tag: "Calculated",
    value: "−17.2 to 44.6",
    unit: "Mm³/yr",
    sub: "After exempt household wells",
    accent: false,
  },
  {
    label: "Tax per 1 Mm³",
    tone: "gray" as const,
    tag: "Calculated",
    value: "Rp 8.85–13.43 bn",
    unit: "",
    sub: "Undeclared business use",
    accent: true,
  },
];

const PREVIEW_ROWS = [
  { name: "Kota Semarang", value: "144–218", estimated: true },
  { name: "Kab. Semarang", value: "not estimated", estimated: false },
  { name: "Kendal", value: "not estimated", estimated: false },
  { name: "Demak", value: "not estimated", estimated: false },
  { name: "Grobogan", value: "not estimated", estimated: false },
  { name: "Boyolali", value: "not estimated", estimated: false },
  { name: "Cilacap", value: "not estimated", estimated: false },
  { name: "Pati", value: "not estimated", estimated: false },
];

function BrowserChrome({ path }: { path: string }) {
  return (
    <div className="flex h-8 items-center gap-3 border-b border-line bg-bg px-3">
      <div className="flex gap-1.5">
        <span className="size-2 rounded-full bg-line-strong" />
        <span className="size-2 rounded-full bg-line-strong" />
        <span className="size-2 rounded-full bg-line-strong" />
      </div>
      <div className="mx-auto flex h-5 w-[280px] items-center justify-center rounded-full border border-line bg-surface font-mono text-[9px] text-ink-3">
        aquifair.app{path}
      </div>
      <div className="w-[38px]" />
    </div>
  );
}

function AppPreview() {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-surface shadow-card">
      <BrowserChrome path="/accounts" />

      <div className="flex h-10 items-center gap-3 border-b border-line px-3">
        <Logo size="sm" />
        <span className="h-4 w-px bg-line" />
        <span className="flex flex-col">
          <span className="text-[9px] font-medium leading-3 text-ink">Jawa Tengah</span>
          <span className="text-[8px] leading-3 text-ink-3">35 kab/kota · 2023</span>
        </span>
        <div className="ml-2 flex h-full items-end gap-3">
          {["Accounts", "Leads", "Pipes", "Methods"].map((tab, index) => (
            <span
              key={tab}
              className={cn(
                "flex h-full items-center border-b-2 text-[8px]",
                index === 0
                  ? "border-blue-700 text-ink"
                  : "border-transparent text-ink-3",
              )}
            >
              {tab}
            </span>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="rounded bg-subtle px-1 py-0.5 font-mono text-[7px] text-ink-2">
            EN
          </span>
          <span className="flex size-4 items-center justify-center rounded-full bg-blue-100 text-[7px] font-medium text-blue-700">
            DS
          </span>
        </div>
      </div>

      <div className="grid h-[400px] grid-cols-[206px_minmax(0,1fr)_296px]">
        <aside className="overflow-hidden border-r border-line p-3">
          <p className="text-[11px] font-semibold leading-4 text-ink">Groundwater accounts</p>
          <p className="mt-1 text-[8px] leading-[12px] text-ink-2">
            Declared vs estimated use per kab/kota, priced with the official groundwater price.
          </p>

          <p className="mt-3 text-[8px] font-medium text-ink-2">Year</p>
          <div className="mt-1 flex rounded bg-subtle p-0.5">
            {["2020", "2021", "2022", "2023"].map((year) => (
              <span
                key={year}
                className={cn(
                  "flex h-4 flex-1 items-center justify-center rounded font-mono text-[7px]",
                  year === "2023" ? "bg-surface text-ink" : "text-ink-3",
                )}
              >
                {year}
              </span>
            ))}
          </div>

          <p className="mt-3 text-[8px] font-medium text-ink-2">Map shows</p>
          <div className="mt-1 space-y-0.5">
            {[
              ["Tax gap", "Rupiah per year, range", true],
              ["Declared volume", "m³ from ESDM records", false],
              ["Estimated use", "m³, business and household", false],
            ].map(([label, sub, active]) => (
              <div
                key={String(label)}
                className={cn(
                  "flex items-start gap-1.5 rounded px-1.5 py-1",
                  active && "bg-blue-50",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 flex size-2 items-center justify-center rounded-full border",
                    active ? "border-blue-700" : "border-line-strong",
                  )}
                >
                  {active && <span className="size-1 rounded-full bg-blue-700" />}
                </span>
                <span className="flex flex-col">
                  <span className="text-[8px] font-medium leading-3 text-ink">{label}</span>
                  <span className="text-[7px] leading-3 text-ink-3">{sub}</span>
                </span>
              </div>
            ))}
          </div>

          <div className="mt-3 flex items-center gap-1">
            <p className="text-[8px] font-medium text-ink-2">Priced as use group</p>
            <span className="rounded border border-line-strong px-1 font-mono text-[6px] text-ink-3">
              NPA
            </span>
          </div>
          <div className="mt-1 flex rounded bg-subtle p-0.5">
            {["K4 low", "K3 medium", "K2 high"].map((group) => (
              <span
                key={group}
                className={cn(
                  "flex h-4 flex-1 items-center justify-center rounded text-[7px]",
                  group === "K3 medium" ? "bg-surface text-ink" : "text-ink-3",
                )}
              >
                {group}
              </span>
            ))}
          </div>

          <div className="mt-3 rounded bg-bg p-2">
            <p className="text-[7px] font-medium text-ink">Tax gap · bn Rp per year</p>
            <div className="mt-1 flex gap-0.5">
              {AMBER_RAMP.map((colour) => (
                <span key={colour} className="h-1.5 flex-1" style={{ backgroundColor: colour }} />
              ))}
            </div>
            <div className="mt-1 flex justify-between font-mono text-[6px] text-ink-3">
              <span>0</span>
              <span>5</span>
              <span>10</span>
              <span>20</span>
              <span>40+</span>
            </div>
          </div>

          <p className="mt-2 text-[7px] leading-[11px] text-ink-3">
            Every figure is a range. The gap mixes real decline, under-reporting and unregistered
            wells.
          </p>
        </aside>

        <section className="relative min-w-0 overflow-hidden bg-sea">
          <MiniMap id="hero" />

          <div className="absolute left-2.5 top-2.5 flex max-w-[360px] items-center gap-1.5 rounded bg-surface px-2 py-1 shadow-card">
            <Badge tone="amber" dot className="h-[16px] px-1.5 text-[7px]">
              Lead
            </Badge>
            <p className="text-[7px] leading-[10px] text-ink-2">
              Only Kota Semarang has a validated estimate. Grey is not zero.
            </p>
          </div>

          <div className="absolute right-2.5 top-2.5 flex flex-col gap-0.5">
            {["+", "−"].map((glyph) => (
              <span
                key={glyph}
                className="flex size-5 items-center justify-center rounded border border-line bg-surface text-[10px] text-ink-2 shadow-card"
              >
                {glyph}
              </span>
            ))}
          </div>

          <div className="absolute left-1/2 top-[32%] w-[192px] -translate-x-1/2 rounded-lg border border-line bg-surface p-2.5 shadow-pop">
            <div className="flex items-center gap-1.5">
              <p className="text-[9px] font-semibold text-ink">Kota Semarang</p>
              <span className="rounded border border-line-strong px-1 font-mono text-[6px] text-ink-3">
                Wil. C
              </span>
            </div>
            <div className="mt-1.5 space-y-1 text-[8px]">
              <div className="flex items-center gap-2">
                <span className="text-ink-3">Declared 2023</span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-ink">10.07 Mm³</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-ink-3">Gap</span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-ink">−17.2 to 44.6</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-ink-3">Tax / Mm³</span>
                <span className="h-px flex-1 bg-line" />
                <span className="font-medium text-amber-800">Rp 8.85–13.43 bn</span>
              </div>
            </div>
            <span className="mt-1.5 inline-flex items-center gap-1 text-[8px] font-medium text-blue-700">
              Open account <ArrowRight size={9} />
            </span>
          </div>

          <div className="absolute bottom-2.5 left-2.5 rounded bg-surface/90 px-2 py-1 font-mono text-[6px] text-ink-3">
            Boundaries: geoBoundaries · 0&nbsp;&nbsp;50 km
          </div>
          <div className="absolute bottom-2.5 right-2.5 flex items-center gap-1 rounded bg-surface/90 px-2 py-1 font-mono text-[6px] text-ink-3">
            <MapPin size={8} /> 35 kabupaten/kota
          </div>
        </section>

        <aside className="flex min-w-0 flex-col border-l border-line">
          <div className="border-b border-line px-3 py-2.5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold text-ink">Tax at stake</p>
              <Badge tone="gray" dot className="h-[16px] px-1.5 text-[7px]">
                Estimate
              </Badge>
            </div>
            <p className="mt-1 text-[7px] text-ink-3">Per 1 Mm³ of undeclared business use</p>
            <p className="mt-1.5 font-display text-[16px] leading-6 tracking-[-0.3px] text-ink">
              Rp 8.85–13.43 bn
            </p>
          </div>

          <div className="flex items-center justify-between bg-bg px-3 py-1 font-mono text-[6px] tracking-[0.4px] text-ink-3">
            <span>KAB/KOTA</span>
            <span>TAX GAP, BN RP/YR</span>
          </div>

          <div className="min-h-0 flex-1 overflow-hidden">
            {PREVIEW_ROWS.map((row, index) => (
              <div
                key={row.name}
                className={cn(
                  "flex items-center gap-2 border-b border-line px-3 py-[6px]",
                  index === 0 && "bg-blue-50",
                )}
              >
                <span className="w-2 font-mono text-[7px] text-ink-3">{index + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[8px] font-medium leading-3 text-ink">{row.name}</p>
                  {row.estimated ? (
                    <div className="mt-1 h-1 rounded-full bg-subtle">
                      <div className="h-full w-[64%] rounded-full bg-blue-500" />
                    </div>
                  ) : (
                    <p className="text-[6px] leading-3 text-ink-3">not estimated</p>
                  )}
                </div>
                <span
                  className={cn(
                    "whitespace-nowrap text-right font-display text-[8px] text-ink",
                    !row.estimated && "font-sans text-[6px] text-ink-3",
                  )}
                >
                  {row.value}
                </span>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between border-t border-line px-3 py-1.5 text-[7px] text-ink-3">
            <span>Show all 35</span>
            <span>Download table</span>
          </div>
        </aside>
      </div>
    </div>
  );
}

function AccountsPreview() {
  return (
    <div className="h-[300px] overflow-hidden rounded-xl border border-line bg-surface shadow-card">
      <div className="flex items-center gap-2 border-b border-line px-4 py-2">
        <p className="text-[11px] font-semibold text-ink">Kota Semarang</p>
        <span className="rounded border border-line-strong px-1 font-mono text-[7px] text-ink-3">
          Wil. C
        </span>
        <Badge tone="blue" dot className="h-[16px] px-1.5 text-[7px]">
          Validated
        </Badge>
        <span className="ml-auto text-[7px] text-ink-3">Groundwater account · 2023</span>
      </div>

      <div className="grid grid-cols-4 gap-2 px-3 pt-3">
        {[
          ["Declared", "10.07", "Mm³", "green", "Data"],
          ["Validated use", "27.9–54.7", "Mm³", "blue", "Tested"],
          ["Taxable gap", "−17.2–44.6", "Mm³", "gray", "Calculated"],
          ["Tax / Mm³", "8.85–13.43", "bn Rp", "gray", "Calculated"],
        ].map(([label, value, unit, tone, tag]) => (
          <div key={String(label)} className="rounded-lg border border-line p-2">
            <p className="text-[7px] text-ink-2">{label}</p>
            <p className="mt-1 font-display text-[13px] leading-4 text-ink">
              {value} <span className="font-sans text-[6px] text-ink-3">{unit}</span>
            </p>
            <Badge tone={tone as "green"} className="mt-1 h-[14px] px-1 text-[6px]">
              {tag}
            </Badge>
          </div>
        ))}
      </div>

      <div className="mt-2 grid grid-cols-[1.35fr_1fr] gap-3 border-t border-line p-3">
        <div>
          <p className="text-[8px] font-medium text-ink">Declared vs estimated</p>
          <div className="mt-1.5 flex h-5 overflow-hidden rounded-[3px]">
            <div className="w-[18%] bg-blue-700" />
            <div className="w-[41%] bg-amber-400" />
            <div className="flex-1 bg-blue-100" />
          </div>
          <div className="mt-1 flex justify-between font-mono text-[6px] text-ink-3">
            <span>0</span>
            <span>27.9</span>
            <span>54.7 Mm³</span>
          </div>
          <div className="mt-2 space-y-1">
            {[
              ["bg-blue-700", "Declared, business 10.07"],
              ["bg-amber-400", "Taxable gap, high end 44.6"],
              ["bg-blue-100", "Above declared + gap"],
            ].map(([colour, text]) => (
              <div key={text} className="flex items-center gap-1.5 text-[7px] text-ink-2">
                <span className={cn("size-1.5 rounded-[1px]", colour)} />
                {text}
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-lg bg-bg p-2">
          <p className="text-[7px] font-medium text-ink">Groundwater price</p>
          <p className="mt-0.5 text-[6px] leading-[9px] text-ink-3">
            Pergub Jateng 7/2025 · Wilayah C · top tier, 20% tax
          </p>
          <div className="mt-1.5 space-y-1">
            {["K1", "K2", "K3", "K4", "K5"].map((group, index) => (
              <div key={group} className="flex items-center gap-1.5">
                <span className="w-3 font-mono text-[6px] text-ink-3">{group}</span>
                <div className="h-1 flex-1 rounded-full bg-subtle">
                  <div
                    className="h-full rounded-full bg-blue-500"
                    style={{ width: `${92 - index * 14}%` }}
                  />
                </div>
                <span className="font-mono text-[6px] text-ink-3">
                  {index === 0 ? "15,715" : index === 4 ? "6,565" : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const BUILDINGS = [
  [44, 54, 14, 9],
  [72, 40, 20, 12],
  [104, 66, 10, 16],
  [136, 46, 18, 10],
  [160, 82, 12, 12],
  [52, 112, 18, 10],
  [88, 104, 12, 14],
  [116, 126, 20, 9],
  [148, 118, 10, 16],
  [188, 40, 14, 10],
  [208, 74, 18, 12],
  [232, 52, 10, 18],
  [186, 110, 16, 9],
  [214, 134, 12, 12],
  [256, 96, 15, 11],
  [270, 132, 10, 14],
  [58, 168, 20, 10],
  [94, 182, 14, 12],
  [126, 164, 10, 16],
  [156, 186, 18, 9],
  [196, 170, 12, 12],
  [232, 188, 16, 10],
  [266, 168, 10, 14],
];

function LeadsPreview() {
  return (
    <div className="flex h-[300px] overflow-hidden rounded-xl border border-line bg-surface shadow-card">
      <div className="relative min-w-0 flex-1 overflow-hidden bg-[#f2ecda]">
        <svg viewBox="0 0 320 300" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
          <rect width="320" height="300" fill="#f2ecda" />
          <path d="M -10 40 L 330 118" stroke="#ffffff" strokeWidth="9" />
          <path d="M -10 210 L 330 140" stroke="#ffffff" strokeWidth="7" />
          <path d="M 96 -10 L 132 310" stroke="#ffffff" strokeWidth="6" />
          <path d="M 236 -10 L 208 310" stroke="#ffffff" strokeWidth="5" />
          <path d="M -10 40 L 330 118" stroke="#d9d2bd" strokeWidth="1" strokeDasharray="4 5" />
          <path d="M 24 274 C 100 248 190 282 320 238" stroke="#b9cfdd" strokeWidth="6" fill="none" />
          {BUILDINGS.map(([x, y, w, h]) => (
            <rect key={`${x}-${y}`} x={x} y={y} width={w} height={h} rx="1" fill="#b8b19f" />
          ))}
          <circle
            cx="168"
            cy="150"
            r="42"
            fill="#ee9b2f"
            fillOpacity="0.08"
            stroke="#ee9b2f"
            strokeWidth="1.2"
            strokeDasharray="4 4"
          />
          <rect x="156" y="140" width="24" height="16" rx="1" fill="#e0812a" stroke="#8f4e0e" />
          <circle cx="168" cy="148" r="3" fill="#0d1a33" />
        </svg>

        <div className="absolute left-2.5 top-2.5 flex items-center gap-1.5 rounded bg-surface px-2 py-1 shadow-card">
          <Badge tone="amber" dot className="h-[16px] px-1.5 text-[7px]">
            In no-new-permit zone
          </Badge>
          <span className="text-[7px] text-ink-2">Illustrative preview</span>
        </div>

        <div className="absolute bottom-2.5 left-2.5 flex gap-0.5 rounded bg-surface px-1.5 py-1 shadow-card">
          {["No permit", "PDAM gap", "New build"].map((chip, index) => (
            <span
              key={chip}
              className={cn(
                "rounded px-1 py-0.5 text-[6px]",
                index === 0 ? "bg-amber-100 text-amber-800" : "text-ink-3",
              )}
            >
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="w-[178px] shrink-0 border-l border-line p-3">
        <p className="text-[10px] font-semibold leading-4 text-ink">Lead card · illustrative</p>
        <p className="text-[7px] text-ink-3">Semarang Barat · preview only</p>

        <div className="mt-2 flex h-[76px] items-center justify-center rounded bg-bg text-ink-3">
          <MapPin size={16} />
          <span className="ml-1 font-mono text-[6px]">field photo after visit</span>
        </div>

        <div className="mt-2 space-y-1">
          {[
            ["Use class", "Industry"],
            ["PDAM", "No mains"],
            ["Zone", "No new permit"],
            ["Sinking", "12 mm/yr"],
            ["Status", "Unvisited"],
          ].map(([key, value]) => (
            <div key={key} className="flex items-center justify-between gap-2 text-[7px]">
              <span className="text-ink-3">{key}</span>
              <span className="font-medium text-ink">{value}</span>
            </div>
          ))}
        </div>

        <div className="mt-2 rounded bg-amber-50 px-1.5 py-1 text-[6px] leading-[9px] text-amber-800">
          Why this lead: new large building, inside a zone with no new groundwater permit.
        </div>
      </div>
    </div>
  );
}

function PipesPreview() {
  return (
    <div className="grid h-[300px] grid-cols-[142px_minmax(0,1fr)_164px] overflow-hidden rounded-xl border border-line bg-surface shadow-card">
      <div className="border-r border-line p-3">
        <p className="text-[9px] font-semibold leading-3 text-ink">Pipes instead of pumps</p>
        <p className="mt-1 text-[6px] leading-[9px] text-ink-3">
          Priority = demand + damage − supply
        </p>

        <div className="mt-3 space-y-2.5">
          {[
            ["Demand", 46],
            ["Damage", 38],
            ["No supply", 30],
          ].map(([label, value]) => (
            <div key={String(label)}>
              <div className="flex items-center justify-between text-[6px]">
                <span className="text-ink-2">{label}</span>
                <span className="font-mono text-ink-3">{value}</span>
              </div>
              <div className="relative mt-1 h-1 rounded-full bg-subtle">
                <div className="h-full rounded-full bg-blue-500" style={{ width: `${value}%` }} />
                <span
                  className="absolute -top-0.5 size-2 rounded-full border border-surface bg-blue-700"
                  style={{ left: `calc(${value}% - 4px)` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 rounded bg-bg p-1.5">
          <p className="text-[6px] font-medium text-ink">Subsidence period</p>
          <div className="mt-1 flex rounded bg-subtle p-0.5 text-[6px]">
            <span className="flex-1 rounded bg-surface px-1 py-0.5 text-center text-ink">2015–20</span>
            <span className="flex-1 px-1 py-0.5 text-center text-ink-3">2007–11</span>
          </div>
        </div>

        <p className="mt-2 text-[6px] leading-[9px] text-ink-3">
          The SPAM Semarang Barat test checks whether sinking slowed where pipes arrived.
        </p>
      </div>

      <div className="relative min-w-0 overflow-hidden bg-sea">
        <MiniMap id="pipes" tone="blue" seaLabel={false} />
        <div className="absolute left-2 top-2 rounded bg-surface/90 px-1.5 py-1 text-[6px] text-ink-2 shadow-card">
          Illustrative cells · 4 km
        </div>
        <div className="absolute bottom-2 left-2 flex items-center gap-0.5 rounded bg-surface/90 px-1.5 py-1">
          {BLUE_RAMP.map((colour) => (
            <span key={colour} className="h-1.5 w-3" style={{ backgroundColor: colour }} />
          ))}
        </div>
      </div>

      <div className="border-l border-line p-3">
        <p className="text-[8px] font-semibold text-ink">Priority cells</p>
        <p className="text-[6px] text-ink-3">Weighted score, top 6</p>
        <div className="mt-2 space-y-1.5">
          {[
            ["Semarang Barat", 92],
            ["Semarang Utara", 84],
            ["Genuk", 76],
            ["Pedurungan", 63],
            ["Semarang Timur", 58],
            ["Gajahmungkur", 41],
          ].map(([name, value], index) => (
            <div key={String(name)} className="flex items-center gap-1.5">
              <span className="w-2 font-mono text-[6px] text-ink-3">{index + 1}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[7px] text-ink">{name}</p>
                <div className="mt-0.5 h-0.5 rounded-full bg-subtle">
                  <div className="h-full rounded-full bg-blue-700" style={{ width: `${value}%` }} />
                </div>
              </div>
              <span className="font-mono text-[6px] text-ink-3">{value}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[6px] leading-[9px] text-ink-3">
          Illustrative only. The tab ranks the 22 real 4 km blocks with your weights.
        </p>
      </div>
    </div>
  );
}

const TOOLS = [
  {
    number: "01",
    title: "Groundwater accounts",
    body: "Declared use against estimated use for every kab/kota, priced with the official NPA table. The gap is split into real decline, under-reporting and unregistered wells, so the tax figure is never one number.",
    audience: "Bapenda · Dinas ESDM · DPRD",
    meta: "35 kab/kota · 2020–2023 · NPA K1–K5",
    link: { href: "/accounts", label: "Open groundwater accounts" },
    note: null,
    preview: <AccountsPreview />,
  },
  {
    number: "02",
    title: "Inspection leads",
    body: "New large buildings inside no-new-permit zones and outside the PDAM network, ranked for a visit. Inspectors record what they find, and the hit rate per class decides next month’s list.",
    audience: "Dinas ESDM inspectors",
    meta: "Semarang–Demak · official 2022 zones · Sentinel-2 2021–26 · OSM classes",
    link: { href: "/leads", label: "Open inspection leads" },
    note: "Filter 4 uses a kecamatan coverage proxy until PDAM shares kelurahan data.",
    preview: <LeadsPreview />,
  },
  {
    number: "03",
    title: "Pipes instead of pumps",
    body: "Where piped surface water should replace the most groundwater, weighted by soft-clay thickness. The SPAM Semarang Barat test checks whether sinking slowed where pipes arrived.",
    audience: "PDAM · Bappeda · PUPR",
    meta: "22 blocks of 4 km · SPAM Semarang Barat test run, inconclusive",
    link: { href: "/pipes", label: "Open pipes instead of pumps" },
    note: "Preview only. Semarang–Demak only.",
    preview: <PipesPreview />,
  },
];

const LABEL_ROWS = [
  {
    tag: "Validated",
    tone: "blue" as const,
    title: "Checked against a true value",
    body: "The 16 km demand split matches the city total; radar rates are tied to GNSS stations.",
  },
  {
    tag: "Lead",
    tone: "amber" as const,
    title: "A reason to look, not a verdict",
    body: "The 4 km demand map, inspection leads and the pipe ranking. Always shown as a range.",
  },
  {
    tag: "Data",
    tone: "gray" as const,
    title: "As published, with the arithmetic shown",
    body: "Declared volumes, the NPA price table and the 2022 conservation zones, plus the tax gap and tax per m³ computed from them.",
  },
  {
    tag: "Missing",
    tone: "red" as const,
    title: "Not estimated is not zero",
    body: "When a number is not in the record it stays grey and says so. It is never filled with a guess.",
  },
];

const REGULATOR_POINTS = [
  {
    title: "About 80% of Semarang’s sinking follows soft-clay thickness.",
    body: "The rest is a regional fall in deep-aquifer pressure. A sinking bowl does not point at one well, so leads come from buildings and zoning instead.",
  },
  {
    title: "Names stay with Dinas ESDM.",
    body: "The public view shows areas, ranges and land-use classes. Permit holders, well locations and field photos stay behind sign-in.",
  },
  {
    title: "Tests are written down before they run.",
    body: "The Arizona check for leads and the SPAM Semarang Barat check for pipes each have a pass mark set in advance.",
  },
];

const CREDITS = [
  "Dinas ESDM Jateng open data, 2020–23 · CC-BY",
  "Pergub Jateng 7/2025 groundwater price",
  "Perda Kota Semarang 10/2023",
  "Sentinel-1 LiCSAR · COMET",
  "geoBoundaries · kab/kota boundaries",
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-line">
        <div className="mx-auto flex h-[76px] max-w-[1240px] items-center px-10">
          <Link href="/" aria-label="AquiFair home">
            <Logo />
          </Link>

          <nav className="ml-auto flex items-center gap-7 text-[12px] font-medium text-ink-2">
            {[
              ["Accounts", "/accounts"],
              ["Leads", "/leads"],
              ["Pipes", "/pipes"],
              ["Methods", "/methods"],
            ].map(([label, href]) => (
              <Link key={label} href={href} className="transition-colors hover:text-ink">
                {label}
              </Link>
            ))}
          </nav>

          <div className="ml-7 flex items-center gap-3">
            <Link href="/sign-in" className="text-[12px] font-medium text-blue-700 hover:text-primary-hover">
              Sign in
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-[1240px] px-10 pb-12 pt-[68px]">
          <div className="grid grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] gap-16">
            <div>
              <h1 className="font-serif-display max-w-[680px] text-[50px] leading-[1.07] tracking-[-0.025em] text-ink">
                Kota Semarang declared 10 million m³ of groundwater in 2023. It used somewhere
                between 25 and 48.
              </h1>
              <p className="mt-6 max-w-[540px] text-[14px] leading-[22px] text-ink-2">
                AquiFair puts that gap on a map for every kab/kota in Central Java, shows inspectors
                the new large buildings most likely to have drilled, and shows where piped water
                should replace pumps.
              </p>
              <div className="mt-8 flex items-center gap-6">
                <Link href="/accounts">
                  <Button
                    variant="primary"
                    size="md"
                    icon={<Grid2x2 size={15} />}
                    className="h-10 px-4 text-[13px]"
                  >
                    Open the account book
                  </Button>
                </Link>
                <Link
                  href="/methods"
                  className="inline-flex items-center gap-1.5 text-[13px] font-medium text-blue-700 transition-colors hover:text-primary-hover"
                >
                  How the estimate works <ArrowRight size={15} />
                </Link>
              </div>
            </div>

            <div className="pt-2">
              <p className="eyebrow text-ink-3">Kota Semarang, 2023 · million m³ a year</p>

              <div className="relative mt-6 h-3 overflow-hidden rounded-sm bg-subtle">
                <div
                  className="absolute inset-y-0 left-0 bg-blue-700"
                  style={{ width: `${(10.07 / 60) * 100}%` }}
                />
                <div
                  className="absolute inset-y-0 bg-amber-400/85"
                  style={{
                    left: `${(27.9 / 60) * 100}%`,
                    width: `${((54.7 - 27.9) / 60) * 100}%`,
                  }}
                />
              </div>
              <div className="mt-1.5 flex justify-between font-mono text-[9px] text-ink-3">
                {[0, 15, 30, 45, 60].map((tick) => (
                  <span key={tick}>{tick}</span>
                ))}
              </div>
              <div className="mt-2 flex items-center gap-4 text-[10px] text-ink-2">
                <span className="inline-flex items-center gap-1.5">
                  <span className="size-2 rounded-[1px] bg-blue-700" />
                  Declared, 10.07
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="size-2 rounded-[1px] bg-amber-400" />
                  Validated range, 27.9–54.7
                </span>
              </div>

              <div className="mt-7 divide-y divide-line border-y border-line">
                {HERO_ROWS.map((row) => (
                  <div key={row.label} className="flex items-start justify-between gap-4 py-3.5">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-[12px] font-medium leading-4 text-ink">{row.label}</p>
                        <Badge tone={row.tone} dot>
                          {row.tag}
                        </Badge>
                      </div>
                      <p className="mt-1 text-[11px] leading-4 text-ink-3">{row.sub}</p>
                    </div>
                    <p
                      className={cn(
                        "whitespace-nowrap text-right font-display text-[20px] leading-6 tracking-[-0.3px]",
                        row.accent ? "text-amber-800" : "text-ink",
                      )}
                    >
                      {row.value}
                      {row.unit && (
                        <span className="ml-1 font-sans text-[10px] text-ink-3">{row.unit}</span>
                      )}
                    </p>
                  </div>
                ))}
              </div>

              <p className="mt-4 text-[11px] leading-[17px] text-ink-3">
                The tax figure prices the undeclared business part only, at 0.20 × NPA. The
                estimate is checked at 16 km against the city total. Sources: Dinas ESDM Jateng
                2023; Pergub Jateng 7/2025.
              </p>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1240px] px-10">
          <AppPreview />
          <p className="mt-3 text-[11px] leading-[16px] text-ink-3">
            The account is a view, not a verdict. Values outside Kota Semarang stay at “not
            estimated” until there is a validated 16 km split.
          </p>
        </section>

        <section className="mx-auto max-w-[1240px] px-10 pb-6 pt-16">
          <h2 className="font-serif-display text-[40px] leading-[1.1] tracking-[-0.02em] text-ink">
            Three tools, one set of numbers
          </h2>

          <div className="mt-6 divide-y divide-line border-y border-line">
            {TOOLS.map((tool) => (
              <div
                key={tool.number}
                className="grid grid-cols-[minmax(0,0.82fr)_minmax(0,1.18fr)] gap-14 py-9"
              >
                <div className="max-w-[400px]">
                  <p className="font-mono text-[11px] leading-4 text-amber-600">{tool.number}</p>
                  <h3 className="mt-3 text-[24px] font-medium leading-[30px] tracking-[-0.3px] text-ink">
                    {tool.title}
                  </h3>
                  <p className="mt-3 text-[13px] leading-[21px] text-ink-2">{tool.body}</p>
                  <p className="mt-5 text-[11px] font-semibold text-ink">Used by {tool.audience}</p>
                  <p className="mt-1 text-[11px] leading-[16px] text-ink-3">{tool.meta}</p>
                  {tool.note && (
                    <div className="mt-3 flex items-center gap-2">
                      <Badge tone={tool.number === "02" ? "amber" : "gray"} dot>
                        {tool.number === "02" ? "Proxy for filter 4" : "Semarang–Demak"}
                      </Badge>
                      <span className="text-[11px] text-ink-3">{tool.note}</span>
                    </div>
                  )}
                  <Link
                    href={tool.link.href}
                    className="mt-5 inline-flex items-center gap-1.5 text-[12px] font-medium text-blue-700 transition-colors hover:text-primary-hover"
                  >
                    {tool.link.label} <ArrowRight size={14} />
                  </Link>
                </div>
                <div className="min-w-0">{tool.preview}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-surface">
          <div className="mx-auto grid max-w-[1240px] grid-cols-[0.82fr_1.18fr] gap-16 px-10 py-16">
            <div>
              <h2 className="font-serif-display text-[40px] leading-[1.08] tracking-[-0.02em] text-ink">
                Every number carries its label
              </h2>
              <p className="mt-5 max-w-[360px] text-[13px] leading-[21px] text-ink-2">
                Radar shows where the ground sinks, not which well caused it. So AquiFair follows
                water and money, and says how sure each figure is.
              </p>
            </div>

            <div className="divide-y divide-line border-y border-line">
              {LABEL_ROWS.map((row) => (
                <div key={row.tag} className="grid grid-cols-[104px_1fr] gap-8 py-5">
                  <div>
                    <Badge tone={row.tone} dot>
                      {row.tag}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-[13px] font-semibold leading-[18px] text-ink">{row.title}</p>
                    <p className="mt-1.5 text-[12px] leading-[18px] text-ink-2">{row.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-[1240px] grid-cols-[0.82fr_1.18fr] gap-16 px-10 py-16">
          <div>
            <h2 className="font-serif-display text-[40px] leading-[1.08] tracking-[-0.02em] text-ink">
              Built to be used by a regulator
            </h2>
            <div className="mt-9 rounded-lg border border-amber-200 bg-amber-50 p-5">
              <p className="eyebrow text-amber-800">The rule</p>
              <p className="mt-2 font-serif text-[19px] leading-[27px] text-ink">
                No figure leaves the app without its year, its source and its range.
              </p>
            </div>
          </div>

          <div className="divide-y divide-line border-y border-line">
            {REGULATOR_POINTS.map((point) => (
              <div key={point.title} className="py-5 first:pt-5">
                <p className="text-[13px] font-semibold leading-[18px] text-ink">{point.title}</p>
                <p className="mt-1.5 text-[12px] leading-[18px] text-ink-2">{point.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-navy-800">
          <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-12 px-10 py-12">
            <div>
              <h2 className="font-serif-display text-[34px] leading-[1.1] text-white">
                Open the account for your kab/kota
              </h2>
              <p className="mt-2 text-[13px] leading-[19px] text-blue-100/70">
                Public view, no sign-in. Figures are ranges with their source and year.
              </p>
            </div>
            <Link href="/accounts" className="shrink-0">
              <Button
                variant="primary"
                size="md"
                icon={<Grid2x2 size={15} />}
                className="h-10 px-4 text-[13px] hover:opacity-90"
                style={{
                  backgroundColor: "#ee9b2f",
                  borderColor: "#ee9b2f",
                  color: "#0d1a33",
                }}
              >
                Open the accounts
              </Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-[1240px] px-10 py-10">
        <div className="grid grid-cols-[1.05fr_0.55fr_1.4fr] gap-12">
          <div>
            <Logo size="sm" />
            <p className="mt-3 text-[11px] leading-[17px] text-ink-2">
              ASEAN Geospatial Challenge 2027
              <br />
              National Level Indonesia
            </p>
            <p className="mt-2 max-w-[280px] text-[11px] leading-[17px] text-ink-3">
              Aligned with SDG 6.1, 6.4, 6.5, 11.5, 13.1, 16.6 and 17.1.
            </p>
          </div>

          <div>
            <p className="eyebrow text-ink-3">Explore</p>
            <div className="mt-3 flex flex-col gap-1.5 text-[11px] text-ink-2">
              <Link href="/accounts" className="hover:text-ink">
                Accounts
              </Link>
              <Link href="/leads" className="hover:text-ink">
                Leads
              </Link>
              <Link href="/pipes" className="hover:text-ink">
                Pipes
              </Link>
              <Link href="/methods" className="hover:text-ink">
                Methods
              </Link>
              <Link href="/accounts/asean" className="hover:text-ink">
                ASEAN comparison
              </Link>
            </div>
          </div>

          <div>
            <p className="eyebrow text-ink-3">Data</p>
            <ul className="mt-3 space-y-1.5 text-[11px] leading-[16px] text-ink-3">
              {CREDITS.map((credit) => (
                <li key={credit}>{credit}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-9 flex items-center justify-between border-t border-line pt-5 text-[11px] text-ink-3">
          <span>AquiFair · public view, no sign-in</span>
          <span className="inline-flex items-center gap-1.5">
            <Check size={12} /> Ranges, sources and years travel with every figure.
          </span>
        </div>
      </footer>
    </div>
  );
}
