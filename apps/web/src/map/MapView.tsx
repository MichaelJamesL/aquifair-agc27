"use client";

import { Check, Info, List, Minus, Plus, Search } from "lucide-react";
import { DISTRICTS, districtByKey } from "@/data/planner";
import { useT } from "@/i18n";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button, TraceTag, cn } from "@/components/ui";
import { LAYERS, layerByKey } from "@/data/layers";
import { CONE_WIDTHS, HOT_SPOTS, isLowStability, rankOf, RUN, toLonLat, type HotSpot } from "@/data/run";
import { useStore } from "@/state";
import { Legend } from "./Legend";
import { Marker, type MarkerState } from "./Marker";
import { loadRasters, samplePixel, type PixelInfo } from "./sampler";
import { BASEMAP_SVG, INDUSTRIAL_SVG, LABELS_SVG, ROADS_SVG } from "./svg";

/** map canvas units per km (the design's 2 km scale bar is 61 units long) */
const UNITS_PER_KM = 30.5;

type View = { s: number; tx: number; ty: number };
type Pt = { x: number; y: number };

// Default framing per screen, taken from the Figma frames: the scale, and where the focus point
// (the Semarang–Demak sinking zone) sits as a fraction of the map viewport. On a bigger screen the
// map scales up so it always covers the viewport, and the focus point keeps the same place.
// Vertically the canvas stays top-aligned as in Figma, so the sea and its labels stay clear of
// the cards in the top-left corner on tall screens.
const FOCUS = { x: 640, y: 420 };
const FRAME_FULL = { s: 1, rx: 0.535, ty: -20 }; // 1140×844 viewport, translate (−30, −20)
const FRAME_PANEL = { s: 0.94, rx: 0.691, ty: -2 }; // 740×844 viewport, translate (−90, −2)

/** smallest scale at which the 1200×900 canvas still covers the viewport */
const coverScale = (vw: number, vh: number) => Math.max(vw / 1200, vh / 900);

/** keep the canvas covering the viewport: no empty edges while panning or zooming out */
function clampView(v: View, vw: number, vh: number): View {
  const s = Math.min(4, Math.max(v.s, coverScale(vw, vh)));
  const tx = Math.min(0, Math.max(vw - 1200 * s, v.tx));
  const ty = Math.min(0, Math.max(vh - 900 * s, v.ty));
  return { s, tx, ty };
}

function frameView(panel: boolean, vw: number, vh: number): View {
  const f = panel ? FRAME_PANEL : FRAME_FULL;
  const s = Math.max(f.s, coverScale(vw, vh));
  return clampView({ s, tx: f.rx * vw - FOCUS.x * s, ty: f.ty * s }, vw, vh);
}

export type MapMode = "explore" | "audit" | "evidence" | "planner";

type Hover = { mx: number; my: number; info: PixelInfo } | null;

const EASE = "duration-300 ease-map";
const CARD = "rounded-md border border-line bg-surface";

/** Stops pointer events from reaching the pan handler. */
const stop = { onPointerDown: (e: React.PointerEvent) => e.stopPropagation() };

export function MapView() {
  const pathname = usePathname();
  const mode: MapMode =
    pathname === "/" ? "explore" : pathname === "/audit" ? "audit" : pathname === "/planner" ? "planner" : "evidence";
  const selectedId = mode === "evidence" ? decodeURIComponent(pathname.split("/")[2] ?? "") : undefined;

  const { layer, ctx, b, hovered, setHovered, district, setDistrict, role } = useStore();
  const { t, pick, n, lang } = useT();
  const labelsSvg = useMemo(
    () => (lang === "ID" ? LABELS_SVG.replace("Tanjung Emas port", "Pelabuhan Tanjung Emas") : LABELS_SVG),
    [lang],
  );
  const [query, setQuery] = useState("");
  const [hoverDistrict, setHoverDistrict] = useState<string | null>(null);
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);
  const panelOpen = mode !== "explore";
  // first paint uses the Figma viewport size; the effect below refits to the real size
  const [size, setSize] = useState({ w: panelOpen ? 740 : 1140, h: 844 });
  const [view, setViewRaw] = useState<View>(() => frameView(panelOpen, panelOpen ? 740 : 1140, 844));
  const setView = (next: View | ((v: View) => View)) =>
    setViewRaw((v) => clampView(typeof next === "function" ? next(v) : next, size.w, size.h));
  const [dragging, setDragging] = useState(false);
  const drag = useRef<{ x: number; y: number; v: View; moved: boolean } | null>(null);
  const [hover, setHover] = useState<Hover>(null);
  const [cursor, setCursor] = useState({ lon: 110.471, lat: 6.962 });
  const [pinned, setPinned] = useState(mode === "explore");

  useEffect(() => {
    loadRasters();
  }, []);

  // Track the viewport size (window resize, side panel opening or closing).
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Reframe when the right-hand panel opens or closes, or the viewport changes size.
  // The first fit happens without animation so the map does not slide in on page load.
  const [fitted, setFitted] = useState(false);
  useEffect(() => {
    setViewRaw(frameView(panelOpen, size.w, size.h));
    const id = requestAnimationFrame(() => setFitted(true));
    return () => cancelAnimationFrame(id);
  }, [panelOpen, size.w, size.h]);

  useEffect(() => {
    setPinned(!panelOpen);
    setHover(null);
  }, [panelOpen]);

  const toScreen = (x: number, y: number): Pt => ({ x: x * view.s + view.tx, y: y * view.s + view.ty });
  const toMap = (sx: number, sy: number): Pt => ({ x: (sx - view.tx) / view.s, y: (sy - view.ty) / view.s });

  const zoomAt = (f: number, cx: number, cy: number) =>
    setView((v) => {
      const s = Math.min(4, Math.max(0.6, v.s * f));
      const k = s / v.s;
      return { s, tx: cx - (cx - v.tx) * k, ty: cy - (cy - v.ty) * k };
    });

  const zoom = (f: number) => {
    const el = ref.current;
    if (el) zoomAt(f, el.clientWidth / 2, el.clientHeight / 2);
  };

  const onPointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    (e.currentTarget as Element).setPointerCapture?.(e.pointerId);
    drag.current = { x: e.clientX, y: e.clientY, v: view, moved: false };
  };

  const onPointerMove = (e: React.PointerEvent) => {
    const r = ref.current!.getBoundingClientRect();
    const sx = e.clientX - r.left;
    const sy = e.clientY - r.top;
    const d = drag.current;
    if (d) {
      const dx = e.clientX - d.x;
      const dy = e.clientY - d.y;
      if (!d.moved && Math.hypot(dx, dy) > 3) {
        d.moved = true;
        setDragging(true);
        setHover(null);
      }
      if (d.moved) {
        setView({ ...d.v, tx: d.v.tx + dx, ty: d.v.ty + dy });
        return;
      }
    }
    const m = toMap(sx, sy);
    const { lon, lat } = toLonLat(m.x, m.y);
    setCursor({ lon, lat });
    if (mode !== "explore") return;
    const info = samplePixel(m.x, m.y);
    if (info && info.kind !== "sea") {
      setPinned(false);
      setHover({ mx: m.x, my: m.y, info });
    } else setHover(null);
  };

  const onPointerUp = () => {
    drag.current = null;
    setDragging(false);
  };

  const onWheel = (e: React.WheelEvent) => {
    const r = ref.current!.getBoundingClientRect();
    zoomAt(e.deltaY < 0 ? 1.1 : 1 / 1.1, e.clientX - r.left, e.clientY - r.top);
  };

  const selected = HOT_SPOTS.find((h) => h.id === selectedId);
  const bKm = CONE_WIDTHS.find((c) => c.key === b)!.km;
  const animate = !dragging && fitted;

  const markerState = (h: HotSpot): MarkerState => {
    if (mode === "evidence") return h.id === selectedId ? "selected" : "muted";
    if (h.id === hovered) return "selected";
    return isLowStability(h) ? "low" : "default";
  };

  const buildings = useMemo(() => makeBuildings(), []);
  const stableCount = HOT_SPOTS.filter((h) => !isLowStability(h)).length;

  return (
    <div
      ref={ref}
      className={cn(
        "relative flex-1 touch-none select-none overflow-hidden bg-water",
        dragging ? "cursor-grabbing" : "cursor-grab",
      )}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerLeave={() => {
        onPointerUp();
        setHover(null);
      }}
      onWheel={onWheel}
    >
      {/* the map canvas: one 1200×900 world, panned and zoomed with a transform */}
      <div
        className={cn("absolute left-0 top-0 h-[900px] w-[1200px] origin-top-left", animate && `transition-transform ${EASE}`)}
        style={{ transform: `translate(${view.tx}px, ${view.ty}px) scale(${view.s})` }}
      >
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: BASEMAP_SVG }} />
        <div
          className="map-layer transition-opacity duration-200"
          style={{ opacity: ctx.industrial ? 1 : 0 }}
          dangerouslySetInnerHTML={{ __html: INDUSTRIAL_SVG }}
        />
        {LAYERS.map((l) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={l.key}
            src={l.src}
            alt=""
            draggable={false}
            className="map-layer transition-opacity duration-200"
            style={{ opacity: l.key === (mode === "planner" ? "background" : layer) ? 1 : 0 }}
          />
        ))}
        {ctx.buildings && (
          <svg className="map-layer" viewBox="0 0 1200 900">
            {buildings.map((r, i) => (
              <rect key={i} x={r[0]} y={r[1]} width={r[2]} height={r[3]} fill="rgba(74,79,85,0.16)" stroke="rgba(74,79,85,0.45)" strokeWidth={0.5} />
            ))}
          </svg>
        )}
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: ROADS_SVG }} />
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: labelsSvg }} />
        {ctx.gnss && (
          <svg className="map-layer" viewBox="0 0 1200 900">
            <path d="M440 323L446 334H434L440 323Z" fill="#17191C" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
            <text fill="#17191C" fontFamily="IBM Plex Mono" fontSize="11" fontWeight="500" x="450" y="332.125">
              CSEM
            </text>
          </svg>
        )}
        {ctx.permits && (
          <svg className="map-layer" viewBox="0 0 1200 900">
            {PERMITS.map(([x, y], i) => (
              <g key={i} transform={`translate(${x} ${y})`}>
                <rect x="-6" y="-6" width="12" height="12" rx="2" fill="white" stroke="#0f4c5c" strokeWidth="1.5" />
                <text y="3.5" textAnchor="middle" fontFamily="IBM Plex Mono" fontSize="9" fontWeight="500" fill="#0f4c5c">
                  P
                </text>
              </g>
            ))}
          </svg>
        )}
      </div>

      {/* cone-width ring around the selected hot spot */}
      {mode === "evidence" && selected && ctx.hotspots && (
        <ConeRing c={toScreen(selected.x, selected.y)} r={bKm * UNITS_PER_KM * view.s} km={bKm} animate={animate} />
      )}

      {mode === "planner" && (
        <Districts
          toScreen={toScreen}
          selected={district}
          hovered={hoverDistrict}
          onHover={setHoverDistrict}
          onPick={setDistrict}
          label={(d) => `${d.name} · ${d.bg} ${t("mm/yr")} ${t("would remain")}`}
          width={size.w}
        />
      )}

      {mode !== "explore" &&
        mode !== "planner" &&
        ctx.hotspots &&
        HOT_SPOTS.map((h) => {
          const p = toScreen(h.x, h.y);
          const rank = rankOf(h.id, b);
          return (
            <Marker
              key={h.id}
              rank={rank}
              state={markerState(h)}
              x={p.x}
              y={p.y}
              animate={animate}
              label={`#${rank} ${h.id} · ${h.place}`}
              onClick={() => router.push(`/audit/${h.id}`)}
              onHover={(on) => setHovered(on ? h.id : null)}
            />
          );
        })}

      {mode === "explore" && pinned && <PinnedTooltips toScreen={toScreen} />}
      {mode === "explore" && hover && (
        <HoverTooltip hover={hover} toScreen={toScreen} width={size.w} height={size.h} />
      )}

      {/* controls */}
      <div className="absolute left-4 top-4 flex cursor-default items-start gap-4" {...stop}>
        <SearchBox
          query={query}
          setQuery={setQuery}
          placeholder={t("Search cell ID or place")}
          empty={t("No match")}
          onPick={(id) => {
            setQuery("");
            if (id.startsWith("district:")) {
              setDistrict(id.slice(9));
              router.push("/planner");
            } else router.push(`/audit/${id}`);
          }}
        />
        <div className={cn(CARD, "flex h-8 items-center gap-1.5 whitespace-nowrap px-2.5 py-1.5 text-xs font-medium text-ink-2")}>
          <Check size={13} strokeWidth={2.2} className="text-pass" />
          <span>{pick(`Tied to GNSS · ${RUN.gnssMisfit} mm/yr vs GNSS`, `Terikat GNSS · selisih ${n(RUN.gnssMisfit)} mm/thn`)}</span>
          <TraceTag code="V1" />
        </div>
      </div>

      {mode === "explore" && (
        <div className={cn(CARD, "absolute left-4 top-[62px] flex h-[34px] cursor-default items-center gap-2 px-3 py-[7px] text-[13px] font-medium")} {...stop}>
          <span>{t("Where and how fast the ground sinks")}</span>
          <TraceTag code="U1" />
          <TraceTag code="O1" />
          <TraceTag code="Q1" />
        </div>
      )}

      <div className={cn(CARD, "absolute right-3.5 top-4 flex w-9 cursor-default flex-col overflow-hidden")} {...stop}>
        <button aria-label={t("Zoom in")} onClick={() => zoom(1.25)} className="grid size-[34px] place-items-center hover:bg-bg">
          <Plus size={16} strokeWidth={2} />
        </button>
        <button aria-label={t("Zoom out")} onClick={() => zoom(0.8)} className="grid size-[34px] place-items-center hover:bg-bg">
          <Minus size={16} strokeWidth={2.2} />
        </button>
      </div>

      <div className="absolute bottom-4 left-4 cursor-default" {...stop}>
        <Legend
          legend={
            mode === "planner"
              ? { kind: "ramp", title: "Background (non-pumping) · mm/yr", stops: layerByKey("background").legend.kind === "ramp" ? (layerByKey("background").legend as { stops: string[] }).stops : [], ticks: ["0", "15", "35", "60+"] }
              : layerByKey(layer).legend
          }
        />
      </div>
      <div className="pointer-events-none absolute bottom-[18px] right-[216px] h-[22px] whitespace-pre rounded bg-white/85 px-2 py-1 text-[11px] leading-[14px] tabular-nums text-ink-2">
        {`${n(cursor.lon, 3)} ${t("E")}  ${n(cursor.lat, 3)} ${t("S")}`}
      </div>
      <ScaleBar s={view.s} />

      {/* "8 hot spots found" card (screen 06) */}
      {mode === "explore" && (
        <div
          className="absolute bottom-[177px] right-4 z-[3] flex w-[300px] cursor-default flex-col gap-2.5 rounded-[10px] border border-line bg-surface p-4 shadow-card"
          {...stop}
        >
          <div className="flex items-center gap-2 text-[15px] font-semibold leading-5">
            {pick(`${HOT_SPOTS.length} hot spots found`, `${HOT_SPOTS.length} titik panas ditemukan`)}
            <span className="flex-1" />
            <TraceTag code="U2" />
          </div>
          <p className="text-[13px] leading-[19px] text-ink-2">
            {pick(
              `Sparse inversion of the pumping part of this map. ${stableCount} of ${HOT_SPOTS.length} reappear in at least 80% of bootstrap reruns.`,
              `Inversi jarang dari bagian pemompaan di peta ini. ${stableCount} dari ${HOT_SPOTS.length} muncul lagi di sedikitnya 80% pengulangan bootstrap.`,
            )}
          </p>
          <Button variant="primary" size="md" icon={<List size={16} strokeWidth={2} />} onClick={() => router.push("/audit")}>
            {t("Open audit list")}
          </Button>
        </div>
      )}
    </div>
  );
}

function ConeRing({ c, r, km, animate }: { c: Pt; r: number; km: number; animate: boolean }) {
  const t = animate ? "transition-all duration-300 ease-map" : "";
  return (
    <>
      <svg
        className={cn("pointer-events-none absolute overflow-visible", t)}
        style={{ left: c.x - r - 2, top: c.y - r - 2, width: 2 * r + 4, height: 2 * r + 4 }}
        viewBox={`0 0 ${2 * r + 4} ${2 * r + 4}`}
      >
        <circle cx={r + 2} cy={r + 2} r={r} fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeDasharray="5 4" />
      </svg>
      <span
        className={cn("pointer-events-none absolute h-[18px] whitespace-nowrap rounded-sm bg-white px-1.5 py-0.5 text-[11px] leading-[14px] text-primary", t)}
        style={{ left: c.x + r * 0.7, top: c.y - r - 13 }}
      >
        B = {km.toFixed(1)} km
      </span>
    </>
  );
}

function ScaleBar({ s }: { s: number }) {
  const perKm = UNITS_PER_KM * s;
  const km = [0.5, 1, 2, 5].find((k) => k * perKm >= 45) ?? 5;
  const w = Math.round(km * perKm);
  return (
    <div className="pointer-events-none absolute bottom-4 right-4 flex h-7 items-center gap-2.5 rounded bg-white/88 px-2.5 py-1.5 text-[11px] leading-[14px]">
      <svg width={w + 2} height="8" viewBox={`0 0 ${w + 2} 8`}>
        <path d={`M1 1V7H${w + 1}V1`} stroke="#17191c" strokeWidth="1.5" fill="none" />
        <path d={`M${w / 2 + 1} 4V7`} stroke="#17191c" strokeWidth="1.2" />
      </svg>
      <span>{km} km</span>
      <svg width="12" height="16" viewBox="0 0 12 16" aria-hidden>
        <path d="M6 1L11 15L6 11.5L1 15Z" fill="#17191c" />
      </svg>
      <span>N</span>
    </div>
  );
}

/* ---------- hover read-outs (screen 06) ---------- */

const TT = "pointer-events-none absolute flex w-[262px] flex-col gap-1.5 rounded-lg border border-line bg-surface px-3 py-2.5 shadow-pop";
const GAP_TT = "pointer-events-none absolute flex w-[242px] items-center gap-2 rounded-md bg-ink px-2.5 py-2 text-xs leading-4 text-bg";
const GAP_TEXT = "No data. Radar lost signal over fish ponds. Not interpolated.";
function GapText() {
  const { t } = useT();
  return <span>{t(GAP_TEXT)}</span>;
}

function PixelCard({ lon, lat, rows }: { lon: number; lat: number; rows: [string, string][] }) {
  const { t, n, pick } = useT();
  return (
    <>
      <div className="text-[11px] leading-[14px] text-ink-3">
        {pick("Pixel", "Piksel")} {n(lon, 3)} {t("E")} · {n(lat, 3)} {t("S")}
      </div>
      {rows.map(([k, v]) => (
        <div key={k} className="flex h-[18px] items-center justify-between text-xs leading-4 text-ink-2">
          <span>{t(k)}</span>
          <span className="text-[11px] leading-[14px] text-ink">{pick(v, v.replace("mm/yr", "mm/thn").replace(/(\d)\.(\d)/g, "$1,$2"))}</span>
        </div>
      ))}
      <div className="text-xs leading-4 text-ink-3">{t("412 images, Jan 2015 – Oct 2026. Seasons removed from the rate.")}</div>
    </>
  );
}

function PixelCursor({ p }: { p: Pt }) {
  return (
    <span
      className="pointer-events-none absolute size-3.5 rounded-full shadow-[inset_0_0_0_1.5px_var(--color-ink),0_0_0_1px_rgba(255,255,255,0.8)]"
      style={{ left: p.x - 7, top: p.y - 7 }}
    />
  );
}

function PinnedTooltips({ toScreen }: { toScreen: (x: number, y: number) => Pt }) {
  // The state drawn in the Figma frame: one pixel read-out and one gap note.
  const p = toScreen(700, 420);
  const g = toScreen(900, 230);
  return (
    <>
      <PixelCursor p={p} />
      <div className={cn(TT, "z-[2]")} style={{ left: p.x + 14, top: p.y + 12 }}>
        <PixelCard
          lon={110.505}
          lat={6.963}
          rows={[
            ["Vertical", "104 ± 4 mm/yr"],
            ["East–west", "+3 ± 5 mm/yr"],
            ["Seasonal amplitude", "9 mm"],
            ["Last change", "Mar 2018, sped up"],
          ]}
        />
      </div>
      <div className={cn(GAP_TT, "z-[2]")} style={{ left: g.x, top: g.y }}>
        <Info size={14} strokeWidth={1.9} className="flex-none" />
        <span>{GAP_TEXT}</span>
      </div>
    </>
  );
}

function HoverTooltip({
  hover,
  toScreen,
  width,
  height,
}: {
  hover: NonNullable<Hover>;
  toScreen: (x: number, y: number) => Pt;
  width: number;
  height: number;
}) {
  const p = toScreen(hover.mx, hover.my);
  const { lon, lat } = toLonLat(hover.mx, hover.my);
  const info = hover.info;
  // keep the card inside the map: flip to the left of the cursor near the right edge
  const flip = p.x + 14 + 262 > width - 16;
  const cardH = info.kind === "gap" ? 52 : 214;
  const up = p.y + 12 + cardH > height - 16;
  const pos = { left: flip ? p.x - 14 - 262 : p.x + 14, top: up ? p.y - 12 - cardH : p.y + 12 };
  return (
    <>
      <PixelCursor p={p} />
      {info.kind === "gap" ? (
        <div className={cn(GAP_TT, "z-[4]")} style={pos}>
          <Info size={14} strokeWidth={1.9} className="flex-none" />
          <GapText />
        </div>
      ) : info.kind === "pixel" ? (
        <div className={cn(TT, "z-[4]")} style={pos}>
          <PixelCard
            lon={lon}
            lat={lat}
            rows={[
              ["Vertical", `${info.vertical} ± ${info.sigma} mm/yr`],
              ["East–west", `${info.eastwest >= 0 ? "+" : "−"}${Math.abs(info.eastwest)} ± 5 mm/yr`],
              ["Seasonal amplitude", `${info.seasonal} mm`],
              ["Last change", info.change],
            ]}
          />
        </div>
      ) : null}
    </>
  );
}

const PERMITS: [number, number][] = [
  [690, 330],
  [775, 392],
  [486, 360],
  [150, 372],
  [930, 470],
];

/** Deterministic building footprints inside the built-up area. */
function makeBuildings() {
  let seed = 7;
  const rnd = () => {
    seed = (seed * 16807) % 2147483647;
    return seed / 2147483647;
  };
  const out: [number, number, number, number][] = [];
  for (let i = 0; i < 900; i++) {
    const x = 40 + rnd() * 740;
    const y = 345 + rnd() * 330;
    if (y > 560 - (x - 400) * 0.25 && x > 640) continue;
    if (y > 520 + Math.abs(x - 420) * -0.4 + 140) continue;
    out.push([x, y, 3 + rnd() * 5, 3 + rnd() * 4]);
  }
  return out;
}

/* ---------- search ---------- */

function SearchBox({
  query,
  setQuery,
  placeholder,
  empty,
  onPick,
}: {
  query: string;
  setQuery: (q: string) => void;
  placeholder: string;
  empty: string;
  onPick: (id: string) => void;
}) {
  const [focus, setFocus] = useState(false);
  const [sel, setSel] = useState(0);
  const q = query.trim().toLowerCase();
  const results = q
    ? [
        ...HOT_SPOTS.filter((h) => h.id.toLowerCase().includes(q) || h.place.toLowerCase().includes(q)).map((h) => ({
          id: h.id,
          title: h.id,
          sub: h.place,
        })),
        ...DISTRICTS.filter((d) => d.name.toLowerCase().includes(q)).map((d) => ({
          id: `district:${d.key}`,
          title: d.name,
          sub: "District · background sinking",
        })),
      ].slice(0, 6)
    : [];
  return (
    <div className="relative">
      <label className={cn(CARD, "flex h-[34px] w-60 items-center gap-2 px-3 py-2")}>
        <Search size={15} strokeWidth={1.9} className="text-ink-3" />
        <input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSel(0);
          }}
          onFocus={() => setFocus(true)}
          onBlur={() => setTimeout(() => setFocus(false), 120)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") setSel((i) => Math.min(results.length - 1, i + 1));
            if (e.key === "ArrowUp") setSel((i) => Math.max(0, i - 1));
            if (e.key === "Enter" && results[sel]) onPick(results[sel].id);
            if (e.key === "Escape") setQuery("");
          }}
          placeholder={placeholder}
          className="w-full bg-transparent text-[13px] leading-[19px] outline-none placeholder:text-ink-3"
        />
      </label>
      {focus && q && (
        <div className="absolute left-0 top-10 z-10 flex w-60 flex-col rounded-md border border-line bg-surface p-1 shadow-pop">
          {results.length === 0 && <span className="px-2.5 py-2 text-xs text-ink-3">{empty}</span>}
          {results.map((r, i) => (
            <button
              key={r.id}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => onPick(r.id)}
              onMouseEnter={() => setSel(i)}
              className={cn("flex flex-col rounded px-2.5 py-1.5 text-left", i === sel && "bg-bg")}
            >
              <span className="font-mono text-xs font-medium">{r.title}</span>
              <span className="text-[11px] leading-[14px] text-ink-3">{r.sub}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- planner districts (screen 10) ---------- */

function Districts({
  toScreen,
  selected,
  hovered,
  onHover,
  onPick,
  label,
  width,
}: {
  toScreen: (x: number, y: number) => Pt;
  selected: string;
  hovered: string | null;
  onHover: (k: string | null) => void;
  onPick: (k: string) => void;
  label: (d: (typeof DISTRICTS)[number]) => string;
  width: number;
}) {
  const sel = districtByKey(selected);
  const pts = (poly: [number, number][]) => poly.map(([x, y]) => toScreen(x, y)).map((p) => `${p.x},${p.y}`).join(" ");
  const corner = sel.poly.map(([x, y]) => toScreen(x, y)).reduce((a, p) => (p.x + p.y > a.x + a.y ? p : a));
  return (
    <>
      <svg className="pointer-events-none absolute inset-0 h-full w-full overflow-visible">
        {DISTRICTS.map((d) => (
          <polygon
            key={d.key}
            points={pts(d.poly)}
            onPointerDown={(e) => e.stopPropagation()}
            onClick={() => onPick(d.key)}
            onMouseEnter={() => onHover(d.key)}
            onMouseLeave={() => onHover(null)}
            className="pointer-events-auto cursor-pointer transition-[fill,stroke] duration-150"
            fill={d.key === selected ? "rgba(23,25,28,0.06)" : hovered === d.key ? "rgba(23,25,28,0.05)" : "transparent"}
            stroke={d.key === selected ? "#17191c" : hovered === d.key ? "rgba(23,25,28,0.5)" : "transparent"}
            strokeWidth={d.key === selected ? 2 : 1.25}
            strokeLinejoin="round"
          />
        ))}
      </svg>
      <span
        className="pointer-events-none absolute h-6 whitespace-nowrap rounded bg-ink px-2 text-xs leading-6 text-bg"
        style={{ left: Math.max(8, Math.min(corner.x - 64, width - 240)), top: corner.y + 8 }}
      >
        {label(sel)}
      </span>
    </>
  );
}
