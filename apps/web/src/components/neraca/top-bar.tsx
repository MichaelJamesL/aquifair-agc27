"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  BookOpen,
  ChevronDown,
  Coins,
  Droplets,
  MapPin,
  UserRound,
} from "lucide-react";
import { ROLE_LABELS, ROLE_PEOPLE, useRole, type Role } from "@/components/neraca/role-context";
import { cn } from "@/components/neraca/ui";

const TABS = [
  { key: "accounts", label: "Accounts", href: "/accounts", icon: Coins },
  { key: "leads", label: "Leads", href: "/leads", icon: MapPin },
  { key: "pipes", label: "Pipes", href: "/pipes", icon: Droplets },
  { key: "methods", label: "Methods", href: "/methods", icon: BookOpen },
] as const;

type Scope = "jawa" | "semarang" | "asean";

function scopeForPath(pathname: string): Scope {
  if (pathname.startsWith("/accounts/asean")) return "asean";
  if (pathname.startsWith("/leads") || pathname.startsWith("/pipes")) return "semarang";
  return "jawa";
}

function activeTab(pathname: string): string {
  if (pathname.startsWith("/leads")) return "leads";
  if (pathname.startsWith("/pipes")) return "pipes";
  if (pathname.startsWith("/methods")) return "methods";
  return "accounts";
}

const SCOPE_COPY: Record<Scope, { title: string; meta: string }> = {
  jawa: { title: "Jawa Tengah", meta: "35 kab/kota · 2023" },
  semarang: { title: "Semarang–Demak", meta: "CAT zone map 2022" },
  asean: { title: "ASEAN cities", meta: "Accounts only · where totals exist" },
};

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { role, setRole } = useRole();
  const [scopeOpen, setScopeOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const scope = scopeForPath(pathname);
  const person = ROLE_PEOPLE[role];
  const tab = activeTab(pathname);

  const goScope = (next: Scope) => {
    setScopeOpen(false);
    if (next === "jawa") router.push("/accounts");
    else if (next === "asean") router.push("/accounts/asean");
    else router.push(tab === "pipes" ? "/pipes" : "/leads");
  };

  const changeRole = (next: Role) => {
    setRole(next);
    setUserOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center gap-5 border-b border-line bg-surface pl-5 pr-4">
      <Link href="/" className="flex shrink-0 items-center gap-2">
        <span className="flex size-7 items-center justify-center rounded-full bg-blue-700 text-white">
          <Droplets size={16} strokeWidth={2.4} />
        </span>
        <span className="font-display text-[20px] font-extrabold leading-[26px] tracking-[-0.3px] text-blue-700">
          NERACA
        </span>
      </Link>

      <div className="h-6 w-px bg-line" />

      <div className="relative shrink-0">
        <button
          onClick={() => setScopeOpen((value) => !value)}
          className="flex min-w-[150px] items-center gap-2.5 rounded-md border border-line px-2.5 py-1.5 text-left"
        >
          <span className="flex flex-col">
            <span className="text-[13px] font-medium leading-4 text-ink">
              {SCOPE_COPY[scope].title}
            </span>
            <span className="text-[11px] leading-[14px] text-ink-3">{SCOPE_COPY[scope].meta}</span>
          </span>
          <ChevronDown size={16} className="ml-auto text-ink-3" />
        </button>
        {scopeOpen && (
          <div className="absolute left-0 top-[calc(100%+6px)] z-50 w-[220px] rounded-lg border border-line bg-surface p-1 shadow-pop">
            {(Object.keys(SCOPE_COPY) as Scope[]).map((key) => (
              <button
                key={key}
                onClick={() => goScope(key)}
                className={cn(
                  "flex w-full flex-col rounded-md px-3 py-2 text-left hover:bg-bg",
                  key === scope && "bg-blue-50",
                )}
              >
                <span className="text-[12px] font-medium text-ink">{SCOPE_COPY[key].title}</span>
                <span className="text-[10px] text-ink-3">{SCOPE_COPY[key].meta}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <nav className="flex h-full items-end gap-1">
        {TABS.map((item) => {
          const Icon = item.icon;
          const isActive = tab === item.key;
          return (
            <Link
              key={item.key}
              href={item.href}
              className={cn(
                "flex h-[55px] items-center gap-[7px] border-b-2 px-3 text-[13px] font-medium transition-colors",
                isActive
                  ? "border-blue-700 text-ink"
                  : "border-transparent text-ink-2 hover:text-ink",
              )}
            >
              <Icon size={15} className={isActive ? "text-blue-700" : "text-ink-3"} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex-1" />

      <div className="relative shrink-0">
        <button
          onClick={() => setUserOpen((value) => !value)}
          className="flex items-center gap-2 rounded-md py-1 pl-1 pr-2 hover:bg-bg"
        >
          <span className="flex size-7 items-center justify-center rounded-full bg-blue-100 text-[11px] font-medium text-blue-700">
            {person.initials}
          </span>
          <span className="flex flex-col text-left">
            <span className="text-[12px] font-medium leading-4 text-ink">{person.name}</span>
            <span className="text-[11px] leading-4 text-ink-3">{person.org}</span>
          </span>
          <ChevronDown size={14} className="text-ink-3" />
        </button>
        {userOpen && (
          <div className="absolute right-0 top-[calc(100%+6px)] z-50 w-[260px] rounded-lg border border-line bg-surface p-1 shadow-pop">
            <p className="px-3 py-2 text-[10px] font-medium uppercase tracking-[0.6px] text-ink-3">
              View as
            </p>
            {(Object.keys(ROLE_LABELS) as Role[]).map((key) => (
              <button
                key={key}
                onClick={() => changeRole(key)}
                className={cn(
                  "flex w-full items-start gap-2 rounded-md px-3 py-2 text-left hover:bg-bg",
                  key === role && "bg-blue-50",
                )}
              >
                <UserRound size={14} className="mt-0.5 text-ink-3" />
                <span>
                  <span className="block text-[12px] font-medium text-ink">{ROLE_LABELS[key]}</span>
                  <span className="block text-[10px] text-ink-3">
                    {ROLE_PEOPLE[key].name} · {ROLE_PEOPLE[key].org}
                  </span>
                </span>
              </button>
            ))}
            <div className="my-1 h-px bg-line" />
            <Link
              href="/sign-in"
              className="block rounded-md px-3 py-2 text-[12px] text-blue-700 hover:bg-bg"
              onClick={() => setUserOpen(false)}
            >
              Choose a role or continue as public
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
