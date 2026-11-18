"use client";

import { ChevronDown, Download, GitCompareArrows, Globe, List, Map as MapIcon, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { RUN } from "@/data/run";
import { useStore } from "@/state";
import { Badge, Button, cn } from "./ui";

const TABS = [
  { label: "Map", icon: MapIcon, href: "/", match: (p: string) => p === "/" || p.startsWith("/audit") },
  { label: "Runs", icon: List, href: "/runs", match: (p: string) => p.startsWith("/runs") },
  { label: "Compare", icon: GitCompareArrows, href: "/compare", match: (p: string) => p.startsWith("/compare") },
  { label: "Validation", icon: ShieldCheck, href: "/validation", match: (p: string) => p.startsWith("/validation") },
];

export function TopBar() {
  const { lang, setLang } = useStore();
  const pathname = usePathname();
  return (
    <header className="relative z-10 flex h-14 flex-none items-center gap-5 border-b border-line bg-surface pl-5 pr-4">
      <Link href="/" aria-label="Groundtrace home" className="flex h-[27px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
      </Link>
      <span className="h-6 w-px flex-none bg-line" />

      <button
        title="Switch run"
        className="flex h-11 items-center gap-2.5 rounded-md border border-line px-2.5 py-1.5 text-left hover:bg-bg"
      >
        <span className="flex w-[154px] flex-col">
          <span className="text-[13px] font-medium leading-4">{RUN.area}</span>
          <span className="text-[11px] leading-[14px] text-ink-3">
            {RUN.id} · {RUN.period}
          </span>
        </span>
        <Badge tone="pass">{RUN.status}</Badge>
        <ChevronDown size={16} strokeWidth={1.75} className="text-ink-2" />
      </button>

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
              {label}
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

      <Button icon={<Download size={14} strokeWidth={1.9} />}>Export</Button>

      <div className="flex items-center gap-2">
        <span className="grid size-7 place-items-center rounded-full bg-primary-tint text-xs font-medium text-primary">
          RS
        </span>
        <span className="flex flex-col text-xs leading-4">
          <span className="font-medium">Rina S.</span>
          <span className="text-ink-3">Regulator · ESDM Jateng</span>
        </span>
      </div>
    </header>
  );
}
