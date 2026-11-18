"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { ConeWidth } from "@/data/run";
import type { LayerKey } from "@/data/layers";

export type ContextLayers = {
  hotspots: boolean;
  gnss: boolean;
  industrial: boolean;
  buildings: boolean;
  permits: boolean;
};

type Store = {
  layer: LayerKey;
  setLayer: (k: LayerKey) => void;
  b: ConeWidth;
  setB: (b: ConeWidth) => void;
  ctx: ContextLayers;
  toggleCtx: (k: keyof ContextLayers) => void;
  lang: "ID" | "EN";
  setLang: (l: "ID" | "EN") => void;
  stableOnly: boolean;
  setStableOnly: (v: boolean) => void;
  /** hot spot under the pointer, shared by the map markers and the audit list rows */
  hovered: string | null;
  setHovered: (id: string | null) => void;
};

const Ctx = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [layer, setLayer] = useState<LayerKey>("vertical");
  const [b, setB] = useState<ConeWidth>("mid");
  const [lang, setLang] = useState<"ID" | "EN">("EN");
  const [stableOnly, setStableOnly] = useState(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const [ctx, setCtx] = useState<ContextLayers>({
    hotspots: true,
    gnss: true,
    industrial: true,
    buildings: false,
    permits: false,
  });
  const toggleCtx = (k: keyof ContextLayers) => setCtx((c) => ({ ...c, [k]: !c[k] }));
  return (
    <Ctx.Provider
      value={{
        layer,
        setLayer,
        b,
        setB,
        ctx,
        toggleCtx,
        lang,
        setLang,
        stableOnly,
        setStableOnly,
        hovered,
        setHovered,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useStore() {
  const s = useContext(Ctx);
  if (!s) throw new Error("useStore outside StoreProvider");
  return s;
}
