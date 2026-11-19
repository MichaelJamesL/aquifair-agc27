"use client";

import { ChevronDown, Download, Info, MapPin } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button, TraceTags, cn } from "@/components/ui";
import { DISTRICTS, districtByKey } from "@/data/planner";
import { useT } from "@/i18n";
import { useStore } from "@/state";

/** 10 · Background for planners (Q3, O4): sinking that would remain without deep pumping. */
export function PlannerPanel() {
  const { district, setDistrict, setLayer } = useStore();
  const { t, pick } = useT();
  const d = districtByKey(district);
  const pump = d.now - d.bg;
  const share = Math.round((d.bg / d.now) * 100);
  const maxDriver = Math.max(...DISTRICTS.flatMap((x) => x.drivers.map((v) => v[1])));
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => setLayer("background"), [setLayer]);
  useEffect(() => {
    if (!open) return;
    const close = (e: PointerEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [open]);

  return (
    <>
      <div className="min-h-0 flex-1 overflow-y-auto pb-[53px]">
        <div className="flex flex-col gap-2 px-4 pb-2.5 pt-4">
          <div className="flex h-7 items-center gap-2">
            <h1 className="text-lg font-semibold leading-6 tracking-[-0.002em]">{t("Sinking that would remain")}</h1>
            <span className="flex-1" />
            <TraceTags codes={["Q3", "O4"]} />
          </div>
          <p className="text-[13px] leading-[19px] text-ink-2">
            {t("For planners: how much the ground keeps sinking even if deep pumping stops.")}
          </p>

          <div ref={ref} className="relative mt-1">
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex h-9 w-full items-center gap-2 rounded-md border border-line-strong px-3 text-[13px] hover:bg-bg"
            >
              <MapPin size={15} strokeWidth={1.9} className="text-ink-2" />
              <span className="text-ink-3">{t("District")}</span>
              <span>{d.name}</span>
              <span className="flex-1" />
              <ChevronDown size={16} strokeWidth={1.75} className={cn("text-ink-2 transition-transform", open && "rotate-180")} />
            </button>
            {open && (
              <div className="absolute inset-x-0 top-10 z-10 flex flex-col rounded-md border border-line bg-surface p-1 shadow-pop">
                {DISTRICTS.map((x) => (
                  <button
                    key={x.key}
                    onClick={() => {
                      setDistrict(x.key);
                      setOpen(false);
                    }}
                    className={cn("rounded px-2.5 py-1.5 text-left text-[13px] hover:bg-bg", x.key === d.key && "font-medium text-primary")}
                  >
                    {x.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 rounded-lg border border-line">
            {[
              [t("Sinking now"), `${d.now}`, t("mm/yr, median")],
              [t("Background"), `${d.bg}`, `${d.bgRange[0]}–${d.bgRange[1]} ${t("mm/yr")}`],
              [t("From pumping"), `${pump}`, t("mm/yr")],
            ].map(([k, v, sub]) => (
              <div key={k} className="flex flex-col gap-0.5 px-3 py-2.5 [&+&]:border-l [&+&]:border-line">
                <span className="text-xs leading-4 text-ink-3">{k}</span>
                <span className="text-2xl font-medium leading-7 tracking-[-0.01em]">{v}</span>
                <span className="text-xs leading-4 text-ink-2">{sub}</span>
              </div>
            ))}
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-[5px]">
            <span className="h-full bg-bg-share transition-[width] duration-300" style={{ width: `${share}%` }} />
            <span className="h-full flex-1 bg-pump" />
          </div>
        </div>

        <div className="mt-1 flex gap-2.5 bg-primary-tint px-4 py-3 text-[13px] leading-[19px]">
          <Info size={16} strokeWidth={1.9} className="mt-0.5 flex-none text-primary" />
          <span>
            {pick(
              `If all deep pumping stopped, about ${d.bg} mm/yr would remain in ${d.name} from natural settling of young clay and the weight of buildings. Compaction that already happened is mostly permanent: the ground will not come back up.`,
              `Jika semua sumur dalam berhenti, sekitar ${d.bg} mm/thn akan tetap terjadi di ${d.name} karena pemadatan alami lempung muda dan beban bangunan. Pemadatan yang sudah terjadi sebagian besar permanen: tanah tidak akan naik lagi.`,
            )}
          </span>
        </div>

        <section className="flex flex-col gap-2 px-4 py-3">
          <div className="flex h-[18px] items-center text-[13px] font-medium">
            {t("What drives the background here")}
            <span className="flex-1" />
            <TraceTags codes={["M5"]} />
          </div>
          {d.drivers.map(([k, v]) => (
            <div key={k} className="flex h-4 items-center gap-2 text-xs">
              <span className="w-[130px] text-ink-2">{t(k)}</span>
              <span className="h-2 rounded-[1px] bg-bg-share transition-[width] duration-300" style={{ width: (v / maxDriver) * 158 }} />
              <span className="text-[11px] text-ink-2">+{v.toFixed(1)}</span>
            </div>
          ))}
          <p className="text-[11px] leading-4 text-ink-3">
            {t(
              "mm/yr each driver adds (Shapley values). Boosted trees trained on quiet pixels only, more than 2B from industry and known wells. Never sees coordinates.",
            )}
          </p>
        </section>

        <div className="border-t border-line px-4 pt-2.5">
          <div className="eyebrow grid h-7 grid-cols-[1fr_76px_96px_52px] items-center border-b border-line text-ink">
            <span>{t("District")}</span>
            <span>{t("Now")}</span>
            <span>{t("Background")}</span>
            <span>{t("Share")}</span>
          </div>
          {DISTRICTS.map((x) => (
            <button
              key={x.key}
              onClick={() => setDistrict(x.key)}
              className={cn(
                "grid h-8 w-full grid-cols-[1fr_76px_96px_52px] items-center border-b border-line text-left text-xs hover:bg-bg",
                x.key === d.key && "bg-bg",
              )}
            >
              <span className="text-[13px]">{x.name}</span>
              <span className="text-[11px] text-ink-2">{x.now}</span>
              <span className="text-[11px] text-ink-2">{x.bg}</span>
              <span className="text-[11px] text-ink-2">{Math.round((x.bg / x.now) * 100)}%</span>
            </button>
          ))}
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 flex h-[53px] items-center gap-2 border-t border-line bg-bg px-4">
        <span className="text-xs text-ink-3">{t("mm/yr, 2015–2026")}</span>
        <span className="flex-1" />
        <Button
          icon={<Download size={14} strokeWidth={1.9} />}
          onClick={() => {
            const a = document.createElement("a");
            a.href = "/map/background.png";
            a.download = "R-0007_background_subsidence.png";
            a.click();
          }}
        >
          {t("Export background map")}
        </Button>
      </div>
    </>
  );
}
