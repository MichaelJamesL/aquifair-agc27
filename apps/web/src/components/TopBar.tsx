"use client";

import { Check, ChevronDown, Download, GitCompareArrows, Globe, List, Map as MapIcon, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { RUN } from "@/data/run";
import { AREAS, RUNS, runsFor, type Run } from "@/data/runs";
import { ExportDialog } from "@/export/ExportDialog";
import { useT } from "@/i18n";
import { useStore, type Role } from "@/state";
import { Badge, Button, cn } from "./ui";

const TABS = [
  { label: "Map", icon: MapIcon, href: "/", match: (p: string) => p === "/" || p.startsWith("/audit") || p === "/planner" },
  { label: "Runs", icon: List, href: "/runs", match: (p: string) => p.startsWith("/runs") },
  { label: "Compare", icon: GitCompareArrows, href: "/compare", match: (p: string) => p.startsWith("/compare") },
  { label: "Validation", icon: ShieldCheck, href: "/validation", match: (p: string) => p.startsWith("/validation") },
];

export const USERS: Record<Role, { initials: string; name: string; role: string }> = {
  regulator: { initials: "RS", name: "Rina S.", role: "Regulator · ESDM Jateng" },
  analyst: { initials: "AW", name: "A. Wibowo", role: "Analyst · BIG" },
  planner: { initials: "DL", name: "D. Lestari", role: "Planner · Bappeda Semarang" },
  public: { initials: "–", name: "Public view", role: "Not signed in · Sign in" },
};

export function TopBar() {
  const { lang, setLang, role, area, setExportOpen } = useStore();
  const { t } = useT();
  const pathname = usePathname();
  const router = useRouter();
  const u = USERS[role];
  return (
    <header className="relative z-20 flex h-14 flex-none items-center gap-5 border-b border-line bg-surface pl-5 pr-4">
      <Link href="/story" aria-label="Groundtrace home" className="flex h-[27px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
      </Link>
      <span className="h-6 w-px flex-none bg-line" />

      <RunSwitcher pathname={pathname} area={area} />

      <nav className="flex gap-1 self-stretch">
        {TABS.map(({ label, icon: Icon, href, match }) => {
          const on = match(pathname);
          return (
            <Link
              key={label}
              href={href}
              className={cn(
                "group -mb-px flex h-[55px] items-center gap-[7px] border-b-2 px-3 text-[13px] font-medium",
                on ? "border-primary text-ink" : "border-transparent text-ink-2 hover:text-ink",
              )}
            >
              <Icon size={15} strokeWidth={2} className={on ? "text-primary" : "text-ink-3"} />
              {t(label)}
            </Link>
          );
        })}
      </nav>

      <span className="flex-1" />

      <div className="flex h-6 items-center rounded-md bg-subtle p-0.5">
        <Globe size={14} strokeWidth={1.9} className="text-ink-3" />
        <span className="flex pl-1.5">
          {(["ID", "EN"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={cn(
                "h-5 w-[30px] rounded font-mono text-[11px] font-medium leading-[14px]",
                lang === l ? "bg-surface text-ink" : "text-ink-3",
              )}
            >
              {l}
            </button>
          ))}
        </span>
      </div>

      <Button icon={<Download size={14} strokeWidth={1.9} />} onClick={() => setExportOpen(true)}>
        {t("Export")}
      </Button>

      <button
        onClick={() => router.push("/sign-in")}
        title={role === "public" ? "Sign in" : "Switch user"}
        className="-mx-1.5 flex items-center gap-2 rounded-md px-1.5 py-0.5 text-left hover:bg-bg"
      >
        <span
          className={cn(
            "grid size-7 place-items-center rounded-full text-xs font-medium",
            role === "public" ? "bg-subtle text-ink-3" : "bg-primary-tint text-primary",
          )}
        >
          {u.initials}
        </span>
        <span className="flex flex-col whitespace-nowrap text-xs leading-4">
          <span className="font-medium">{t(u.name)}</span>
          <span className="text-ink-3">{t(u.role)}</span>
        </span>
      </button>

      <ExportDialog />
    </header>
  );
}

/** Run chip plus a dropdown of the runs this user may open for the current area. */
function RunSwitcher({ pathname, area }: { pathname: string; area: string }) {
  const { role, r8Published } = useStore();
  const { t } = useT();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const close = (e: PointerEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [open]);
  useEffect(() => setOpen(false), [pathname]);

  const visible = runsFor(r8Published).filter((r) => r.area === "semarang-demak" && (role === "analyst" || !r.private));
  const go = (r: Run) => {
    setOpen(false);
    if (r.id === "R-0007") router.push("/");
    else if (r.id === "R-0008") router.push(r8Published ? "/validation" : "/runs/R-0008");
    else if (r.id === "R-0009") router.push("/runs/R-0009");
    else router.push("/runs");
  };
  const current = pathname.match(/R-\d+/)?.[0] ?? (pathname.startsWith("/validation") ? "R-0008" : "R-0007");

  return (
    <div ref={ref} className="relative">
      <button
        title={t("Switch run")}
        onClick={() => setOpen((o) => !o)}
        className="flex h-11 items-center gap-2.5 rounded-md border border-line px-2.5 py-1.5 text-left hover:bg-bg"
      >
        <RunChip pathname={pathname} area={area} />
        <ChevronDown size={16} strokeWidth={1.75} className={cn("text-ink-2 transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="absolute left-0 top-[50px] z-30 flex w-[300px] flex-col rounded-lg border border-line bg-surface p-1 shadow-pop">
          <div className="eyebrow px-2.5 pb-1 pt-2 text-ink-3">Semarang–Demak</div>
          {visible.map((r) => (
            <button
              key={r.id}
              onClick={() => go(r)}
              className="flex items-center gap-2.5 rounded-md px-2.5 py-2 text-left hover:bg-bg"
            >
              <span className="flex flex-1 flex-col">
                <span className="text-[13px] font-medium leading-4">{r.id}</span>
                <span className="text-[11px] leading-[14px] text-ink-3">
                  {r.period} · {r.images} images
                </span>
              </span>
              <StatusBadge run={r} />
              <span className="w-3.5">{r.id === current && <Check size={14} strokeWidth={2.2} className="text-primary" />}</span>
            </button>
          ))}
          <Link href="/runs" className="mt-1 border-t border-line px-2.5 pb-1.5 pt-2.5 text-xs font-medium text-primary hover:underline">
            {t("Runs")} →
          </Link>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ run }: { run: Run }) {
  const { t } = useT();
  switch (run.status) {
    case "published":
      return <Badge tone="pass">{t("Published")}</Badge>;
    case "running":
      return <Badge tone="running">{t("Running")}</Badge>;
    case "stopped":
      return <Badge tone="fail">{t("Stopped")}</Badge>;
    default:
      return <Badge tone="neutral">{t("Superseded")}</Badge>;
  }
}

/** The run chip names whatever the page is about: the open run, a draft, or an empty area. */
function RunChip({ pathname, area }: { pathname: string; area: string }) {
  const { r8Published } = useStore();
  const { t, pick } = useT();
  let title = RUN.area;
  let meta = `${RUN.id} · ${pick(RUN.period, RUN.period.replace("Oct", "Okt"))}`;
  let badge = <Badge tone="pass">{t(RUN.status)}</Badge>;
  const runId = pathname.match(/^\/runs\/(R-\d+)/)?.[1];
  const run = RUNS.find((r) => r.id === runId);
  const a = AREAS.find((x) => x.key === area)!;
  if (pathname === "/runs/new") {
    title = a.configured ? a.name : RUN.area;
    meta = "New run · Jan 2015 – Nov 2026";
    badge = <Badge tone="neutral">{t("Draft")}</Badge>;
  } else if (pathname.startsWith("/validation")) {
    meta = "R-0008 · Jan 2015 – Nov 2026";
    badge = r8Published ? <Badge tone="pass">{t("Published")}</Badge> : <Badge tone="neutral">{t("Private")}</Badge>;
  } else if (run) {
    meta = `${run.id} · ${run.period}`;
    badge =
      run.id === "R-0008" && r8Published ? (
        <Badge tone="pass">{t("Published")}</Badge>
      ) : run.status === "running" ? (
        <Badge tone="running">{t("Running")}</Badge>
      ) : (
        <Badge tone="fail">{t("Stopped")}</Badge>
      );
  } else if (pathname === "/runs" && area !== "semarang-demak") {
    title = a.name;
    meta = a.configured ? `No run yet · ${a.period[0]} – ${a.period[1]}` : "Not configured";
    badge = <Badge tone="neutral">{t("Empty")}</Badge>;
  }
  return (
    <>
      <span className="flex min-w-[154px] flex-col">
        <span className="text-[13px] font-medium leading-4">{title}</span>
        <span className="text-[11px] leading-[14px] text-ink-3">{meta}</span>
      </span>
      {badge}
    </>
  );
}
