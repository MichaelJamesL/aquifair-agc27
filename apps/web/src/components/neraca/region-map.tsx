"use client";

import { useEffect, useRef } from "react";
import {
  Map as MlMap,
  NavigationControl,
  setWorkerUrl,
  type GeoJSONSource,
  type LngLatBoundsLike,
} from "maplibre-gl";
import type { RegionFeatureCollection } from "@/lib/api";
import { cn } from "@/components/neraca/ui";

setWorkerUrl("/maplibre-gl-worker.mjs");

type Props = {
  data: RegionFeatureCollection | null;
  fills: Record<string, string>;
  selectedId?: string | null;
  onSelect?: (regionId: string) => void;
  className?: string;
  showControls?: boolean;
  fitPadding?: number;
};

function collectCoordinates(value: unknown, lon: number[], lat: number[]) {
  if (!Array.isArray(value)) return;
  if (typeof value[0] === "number" && typeof value[1] === "number") {
    lon.push(value[0]);
    lat.push(value[1]);
    return;
  }
  for (const child of value) collectCoordinates(child, lon, lat);
}

function boundsOf(data: RegionFeatureCollection): LngLatBoundsLike | null {
  const lon: number[] = [];
  const lat: number[] = [];
  for (const feature of data.features) {
    const geometry = feature.geometry as { coordinates?: unknown } | null;
    if (geometry?.coordinates) collectCoordinates(geometry.coordinates, lon, lat);
  }
  if (!lon.length || !lat.length) return null;
  return [
    [Math.min(...lon), Math.min(...lat)],
    [Math.max(...lon), Math.max(...lat)],
  ];
}

function styledData(data: RegionFeatureCollection, fills: Record<string, string>) {
  return {
    type: "FeatureCollection" as const,
    features: data.features.map((feature) => {
      const regionId = String(feature.properties.region_id ?? "");
      return {
        ...feature,
        properties: {
          ...feature.properties,
          region_id: regionId,
          fill: fills[regionId] ?? "#e8e5dd",
        },
      };
    }),
  };
}

export function RegionMap({
  data,
  fills,
  selectedId,
  onSelect,
  className,
  showControls = true,
  fitPadding = 36,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MlMap | null>(null);
  const selectRef = useRef(onSelect);
  const selectedRef = useRef(selectedId);
  const dataRef = useRef(data);
  const fillsRef = useRef(fills);
  const fittedRef = useRef(false);
  const interactionsBoundRef = useRef(false);

  selectRef.current = onSelect;
  selectedRef.current = selectedId;
  dataRef.current = data;
  fillsRef.current = fills;

  const bindInteractions = (map: MlMap) => {
    if (interactionsBoundRef.current || !map.getLayer("regions-fill")) return;
    interactionsBoundRef.current = true;
    map.on("click", "regions-fill", (event) => {
      const id = event.features?.[0]?.properties?.region_id;
      if (id) selectRef.current?.(String(id));
    });
    map.on("mouseenter", "regions-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "regions-fill", () => {
      map.getCanvas().style.cursor = "";
    });
  };

  const applySelection = (map: MlMap) => {
    if (!map.getLayer("regions-line")) return;
    const selected = selectedRef.current ?? "";
    map.setPaintProperty("regions-line", "line-color", [
      "case",
      ["==", ["get", "region_id"], selected],
      "#14202b",
      "#ffffff",
    ]);
    map.setPaintProperty("regions-line", "line-width", [
      "case",
      ["==", ["get", "region_id"], selected],
      1.8,
      0.8,
    ]);
  };

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new MlMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#d7e6f2" },
          },
        ],
      },
      center: [110.2, -7.0],
      zoom: 6.6,
      attributionControl: false,
      interactive: true,
    });
    mapRef.current = map;

    if (showControls) {
      map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    }

    map.on("load", () => {
      const initialData = dataRef.current;
      if (!initialData) return;
      map.addSource("regions", {
        type: "geojson",
        data: styledData(initialData, fillsRef.current),
      });
      map.addLayer({
        id: "regions-fill",
        type: "fill",
        source: "regions",
        paint: { "fill-color": ["get", "fill"], "fill-opacity": 1 },
      });
      map.addLayer({
        id: "regions-line",
        type: "line",
        source: "regions",
        paint: {
          "line-color": "#ffffff",
          "line-width": 0.8,
        },
      });

      bindInteractions(map);
      applySelection(map);

      const bounds = boundsOf(initialData);
      if (bounds && !fittedRef.current) {
        map.fitBounds(bounds, { padding: fitPadding, duration: 0 });
        fittedRef.current = true;
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
      fittedRef.current = false;
      interactionsBoundRef.current = false;
    };
    // The map is created once; later updates go through the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;
    const source = map.getSource("regions") as GeoJSONSource | undefined;
    if (source) {
      source.setData(styledData(data, fills) as never);
    } else if (map.isStyleLoaded()) {
      map.addSource("regions", { type: "geojson", data: styledData(data, fills) as never });
      map.addLayer({
        id: "regions-fill",
        type: "fill",
        source: "regions",
        paint: { "fill-color": ["get", "fill"], "fill-opacity": 1 },
      });
      map.addLayer({
        id: "regions-line",
        type: "line",
        source: "regions",
        paint: { "line-color": "#ffffff", "line-width": 0.8 },
      });
      bindInteractions(map);
      applySelection(map);
    }
    if (!fittedRef.current) {
      const bounds = boundsOf(data);
      if (bounds) {
        map.fitBounds(bounds, { padding: fitPadding, duration: 0 });
        fittedRef.current = true;
      }
    }
  }, [data, fills, fitPadding]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    applySelection(map);
  }, [selectedId]);

  return (
    <div className={cn("relative h-full w-full overflow-hidden bg-sea", className)}>
      <div ref={containerRef} className="h-full w-full" />
      {!data && (
        <div className="absolute inset-0 flex items-center justify-center text-[12px] text-ink-2">
          Loading boundaries…
        </div>
      )}
    </div>
  );
}
