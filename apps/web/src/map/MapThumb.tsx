import { HOT_SPOTS, rankOf } from "@/data/run";
import { cn } from "@/components/ui";
import { BASEMAP_SVG, INDUSTRIAL_SVG, LABELS_SVG, ROADS_SVG } from "./svg";

/**
 * Static map preview: the same layers as the main map, framed by a scale and offset.
 * Used on the Runs screen (dots), the story page and the audit sheet (numbered markers).
 */
export function MapThumb({
  width = 359,
  height = 220,
  dots = true,
  numbered = false,
  s = 0.5,
  tx = -90,
  ty = -90,
  raster = "/map/vertical.png",
  labels = true,
  className,
  rounded = true,
  lang = "en",
  marker = 18,
}: {
  width?: number | string;
  height?: number;
  dots?: boolean;
  numbered?: boolean;
  s?: number;
  tx?: number;
  ty?: number;
  raster?: string | null;
  labels?: boolean;
  className?: string;
  rounded?: boolean;
  lang?: "en" | "id";
  /** diameter of numbered markers, px */
  marker?: number;
}) {
  return (
    <div className={cn("relative overflow-hidden bg-water", rounded && "rounded-lg", className)} style={{ width, height }}>
      <div
        className="absolute left-0 top-0 h-[900px] w-[1200px] origin-top-left"
        style={{ transform: `translate(${tx}px, ${ty}px) scale(${s})` }}
      >
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: BASEMAP_SVG }} />
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: INDUSTRIAL_SVG }} />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {raster && <img src={raster} alt="" className="map-layer" />}
        <div className="map-layer" dangerouslySetInnerHTML={{ __html: ROADS_SVG }} />
        {labels && (
          <svg className="map-layer" viewBox="0 0 1200 900">
            <path d="M440 323L446 334H434L440 323Z" fill="#17191C" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
            <text fill="#17191C" fontFamily="IBM Plex Mono" fontSize="11" fontWeight="500" x="450" y="332.125">
              CSEM
            </text>
          </svg>
        )}
        {labels && (
          <div
            className="map-layer"
            dangerouslySetInnerHTML={{
              __html: lang === "id" ? LABELS_SVG.replace("Tanjung Emas port", "Pelabuhan Tanjung Emas") : LABELS_SVG,
            }}
          />
        )}
      </div>
      {dots &&
        !numbered &&
        HOT_SPOTS.map((h) => (
          <span
            key={h.id}
            className="absolute size-2.5 rounded-full bg-white shadow-[inset_0_0_0_1.5px_var(--color-ink)]"
            style={{ left: h.x * s + tx - 5, top: h.y * s + ty - 5 }}
          />
        ))}
      {numbered &&
        HOT_SPOTS.map((h) => {
          const r = rankOf(h.id, "mid");
          const weak = h.stability < 0.8;
          return (
            <span
              key={h.id}
              className={cn(
                "absolute grid place-items-center rounded-full bg-white font-mono font-medium leading-none",
                weak ? "border border-dashed border-ink-3 text-ink-3" : "border-[1.5px] border-ink text-ink",
              )}
              style={{ left: h.x * s + tx - marker / 2, top: h.y * s + ty - marker / 2, width: marker, height: marker, fontSize: marker > 20 ? 12 : 10 }}
            >
              {r}
            </span>
          );
        })}
    </div>
  );
}
