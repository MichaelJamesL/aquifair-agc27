"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { ConeWidth } from "@/data/run";
import type { LayerKey } from "@/data/layers";
import type { AreaKey } from "@/data/runs";

export type Role = "regulator" | "analyst" | "planner" | "public";

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
  /** who is signed in; the demo switches by clicking the user in the top bar */
  role: Role;
  setRole: (r: Role) => void;
  area: AreaKey;
  setArea: (a: AreaKey) => void;
  /** the Export audit dialog (screen 11) */
  /** district picked on the planner screen (10) */
  district: string;
  setDistrict: (k: string) => void;
  exportOpen: boolean;
  setExportOpen: (v: boolean) => void;
  /** R-0008 after an analyst signs it off (screens 05 and Validation) */
  r8Published: boolean;
  setR8Published: (v: boolean) => void;
};

const Ctx = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [layer, setLayer] = useState<LayerKey>("vertical");
  const [b, setB] = useState<ConeWidth>("mid");
  const [lang, setLang] = useState<"ID" | "EN">("EN");
  const [stableOnly, setStableOnly] = useState(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const [role, setRole] = useState<Role>("regulator");
  const [area, setArea] = useState<AreaKey>("semarang-demak");
  const [exportOpen, setExportOpen] = useState(false);
  const [district, setDistrict] = useState("genuk");
  const [r8Published, setR8Published] = useState(false);
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
        role,
        setRole,
        area,
        setArea,
        district,
        setDistrict,
        exportOpen,
        setExportOpen,
        r8Published,
        setR8Published,
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
