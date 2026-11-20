"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, Coins, Droplets, Landmark, MapPin, ShieldCheck } from "lucide-react";
import { useRole, type Role } from "@/components/neraca/role-context";
import { Badge, Button, cn } from "@/components/neraca/ui";

const ROLES: {
  key: Role;
  title: string;
  sub: string;
  icon: typeof Coins;
  tone: string;
}[] = [
  {
    key: "regulator",
    title: "Revenue agency · city council",
    sub: "Groundwater accounts · Tax gap, NPA, first tax check",
    icon: Landmark,
    tone: "bg-amber-100 text-amber-800",
  },
  {
    key: "inspector",
    title: "ESDM office inspector",
    sub: "Inspection leads · Lead list, field results, permit registry",
    icon: MapPin,
    tone: "bg-blue-100 text-blue-700",
  },
  {
    key: "planner",
    title: "Water utility · planning · public works",
    sub: "Pipes instead of pumps · Priority map, SPAM test",
    icon: Droplets,
    tone: "bg-blue-100 text-blue-700",
  },
];

export default function SignInPage() {
  const router = useRouter();
  const { role, setRole } = useRole();

  const choose = (next: Role) => {
    setRole(next);
    router.push("/accounts");
  };

  return (
    <div className="grid min-h-screen grid-cols-[600px_minmax(0,1fr)] bg-bg">
      <section className="relative flex flex-col justify-between overflow-hidden bg-navy-900 px-16 py-12 text-white">
        <div className="relative z-10 flex items-center gap-2">
          <Image src="/AquiFair_mark_for_light_bg.png" alt="" width={30} height={30} priority />
          <span className="font-display text-[20px] font-extrabold tracking-[-0.3px]">
            Aqui<span className="text-[#e8892b]">Fair</span>
          </span>
        </div>

        <div className="relative z-10 max-w-[460px]">
          <h1 className="font-serif-display text-[44px] leading-[52px]">
            One account of groundwater, for the people who act on it.
          </h1>
          <p className="mt-5 text-[14px] leading-[22px] text-white/65">
            Each role sees the tool it needs. Permit and well records stay with the ESDM office;
            public views show areas, ranges and land-use classes only.
          </p>
        </div>

        <div className="relative z-10 flex items-center gap-5 text-[11px] text-white/60">
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-blue-400" /> Validated: checked against a true value
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-amber-500" /> Lead: a reason to look, not a verdict
          </span>
        </div>

        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[420px] opacity-40">
          <div className="absolute bottom-[-120px] left-[-80px] size-[420px] rotate-12 rounded-[30%] border border-blue-400/50 bg-blue-500/10" />
          <div className="absolute bottom-[-180px] left-[120px] size-[420px] rotate-45 rounded-[35%] border border-amber-500/50 bg-amber-500/10" />
          <div className="absolute bottom-[-220px] right-[-40px] size-[360px] -rotate-12 rounded-[32%] border border-blue-400/50" />
        </div>
      </section>

      <section className="flex items-center justify-center px-10 py-12">
        <div className="w-full max-w-[520px]">
          <h2 className="text-[30px] font-semibold leading-9 text-ink">Sign in</h2>
          <p className="mt-1 text-[13px] leading-5 text-ink-2">
            Choose a role. There is no login in this demo; the dropdown only changes the view.
          </p>

          <div className="mt-7 space-y-3">
            {ROLES.map((item) => {
              const Icon = item.icon;
              const active = role === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => setRole(item.key)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl border bg-surface px-4 py-3.5 text-left transition-colors",
                    active ? "border-blue-700 ring-1 ring-blue-700" : "border-line hover:bg-bg",
                  )}
                >
                  <span className={cn("flex size-9 items-center justify-center rounded-full", item.tone)}>
                    <Icon size={18} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[14px] font-semibold text-ink">{item.title}</span>
                    <span className="mt-0.5 block text-[12px] leading-4 text-ink-3">{item.sub}</span>
                  </span>
                  <span
                    className={cn(
                      "flex size-5 items-center justify-center rounded-full border",
                      active ? "border-blue-700 bg-blue-700 text-white" : "border-line-strong",
                    )}
                  >
                    {active && <Check size={12} />}
                  </span>
                </button>
              );
            })}
          </div>

          <Button
            variant="primary"
            size="md"
            className="mt-6 w-full"
            onClick={() => choose(role === "public" ? "regulator" : role)}
          >
            Continue as {role === "public" ? "regulator" : role}
            <ArrowRight size={16} />
          </Button>

          <div className="my-5 flex items-center gap-3 text-[11px] text-ink-3">
            <span className="h-px flex-1 bg-line" /> or <span className="h-px flex-1 bg-line" />
          </div>

          <button
            onClick={() => choose("public")}
            className="flex w-full items-center gap-3 rounded-xl border border-line bg-bg px-4 py-3.5 text-left hover:bg-subtle"
          >
            <span className="flex size-9 items-center justify-center rounded-full bg-surface text-ink-2">
              <ShieldCheck size={18} />
            </span>
            <span className="flex-1">
              <span className="block text-[13px] font-semibold text-ink">Continue as public viewer</span>
              <span className="mt-0.5 block text-[11px] leading-4 text-ink-3">
                Accounts and pipes by area, as ranges. Permits, wells and lead locations are hidden.
              </span>
            </span>
            <ArrowRight size={16} className="text-ink-3" />
          </button>

          <div className="mt-6 flex items-center justify-between text-[11px] text-ink-3">
            <span className="inline-flex items-center gap-1.5">
              <Badge tone="blue" dot>Validated</Badge> independent truth
            </span>
            <Link href="/accounts" className="text-blue-700">
              Skip to accounts
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
