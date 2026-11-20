"use client";

import { useEffect, useRef } from "react";
import {
  Map as MlMap,
  NavigationControl,
  AttributionControl,
  setWorkerUrl,
  type GeoJSONSource,
  type LayerSpecification,
  type LngLatBoundsLike,
  type MapGeoJSONFeature,
} from "maplibre-gl";
import { cn } from "@/components/neraca/ui";

setWorkerUrl("/maplibre-gl-worker.mjs");

export type OverlayLayer = {
  id: string;
  data: GeoJSON.FeatureCollection | null;
  /** MapLibre layers drawn from this source; ids must be unique across the map. */
  layers: Omit<LayerSpecification, "source">[];
  visible?: boolean;
};

type Props = {
  overlays: OverlayLayer[];
  bounds: LngLatBoundsLike;
  onFeatureClick?: (layerId: string, feature: MapGeoJSONFeature) => void;
  clickableLayers?: string[];
  className?: string;
};

// Esri light-gray canvas: no API key (CARTO's free tiles now return an "API key required" watermark).
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas";
const BASEMAP = {
  type: "raster" as const,
  tiles: [`${ESRI}/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`],
  tileSize: 256,
  maxzoom: 16,
  attribution: "Esri, HERE, Garmin, © OpenStreetMap contributors",
};
const LABELS = { ...BASEMAP, tiles: [`${ESRI}/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}`] };

/** A light street basemap with GeoJSON overlays. Overlays are added in order (first = bottom). */
export function OverlayMap({ overlays, bounds, onFeatureClick, clickableLayers = [], className }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MlMap | null>(null);
  const readyRef = useRef(false);
  const overlaysRef = useRef(overlays);
  const clickRef = useRef(onFeatureClick);
  overlaysRef.current = overlays;
  clickRef.current = onFeatureClick;

  const sync = (map: MlMap) => {
    for (const overlay of overlaysRef.current) {
      const empty: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };
      const source = map.getSource(overlay.id) as GeoJSONSource | undefined;
      if (source) source.setData(overlay.data ?? empty);
      else map.addSource(overlay.id, { type: "geojson", data: overlay.data ?? empty });
      for (const layer of overlay.layers) {
        if (!map.getLayer(layer.id)) map.addLayer({ ...layer, source: overlay.id } as LayerSpecification);
        map.setLayoutProperty(layer.id, "visibility", overlay.visible === false ? "none" : "visible");
      }
    }
  };

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new MlMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: { basemap: BASEMAP, labels: LABELS },
        layers: [
          { id: "basemap", type: "raster", source: "basemap" },
          { id: "labels", type: "raster", source: "labels" },
        ],
      },
      bounds,
      fitBoundsOptions: { padding: 24 },
      attributionControl: false,
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new AttributionControl({ compact: true }), "bottom-right");
    mapRef.current = map;
    map.on("load", () => {
      readyRef.current = true;
      sync(map);
      for (const id of clickableLayers) {
        map.on("click", id, (event) => {
          const feature = event.features?.[0];
          if (feature) clickRef.current?.(id, feature);
        });
        map.on("mouseenter", id, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", id, () => (map.getCanvas().style.cursor = ""));
      }
    });
    return () => {
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
    };
    // The map is created once; overlay changes go through the effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (mapRef.current && readyRef.current) sync(mapRef.current);
  }, [overlays]);

  return (
    <div className={cn("relative h-full w-full overflow-hidden bg-sea", className)}>
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}
