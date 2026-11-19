"use client";

import { ArrowRight, Globe, Lock, Map as MapIcon, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/components/ui";
import { useT } from "@/i18n";
import { MapThumb } from "@/map/MapThumb";
import { useStore, type Role } from "@/state";

const ROLES: { key: Role; title: Record<"EN" | "ID", string>; org: string; text: Record<"EN" | "ID", string>; email: string; home: string }[] = [
  {
    key: "regulator",
    title: { EN: "Groundwater regulator", ID: "Regulator air tanah" },
    org: "ESDM Jawa Tengah, Badan Geologi",
    text: { EN: "Permit matches, well records, full audit sheet", ID: "Kecocokan izin, catatan sumur, lembar audit lengkap" },
    email: "nama@esdm.jatengprov.go.id",
    home: "/audit",
  },
  {
    key: "analyst",
    title: { EN: "Geospatial analyst", ID: "Analis geospasial" },
    org: "BIG, universities",
    text: { EN: "Start runs, check every stage, sign off", ID: "Memulai run, memeriksa tiap tahap, menyetujui" },
    email: "nama@big.go.id",
    home: "/runs",
  },
  {
    key: "planner",
    title: { EN: "City planner", ID: "Perencana kota" },
    org: "Planning and public-works offices",
    text: { EN: "Background sinking by district", ID: "Penurunan latar per kecamatan" },
    email: "nama@semarangkota.go.id",
    home: "/planner",
  },
];

/** 02 · Sign in (S3). Picks the role the rest of the demo uses. */
export function SignIn() {
  const { setRole, lang, setLang } = useStore();
  const { pick } = useT();
  const router = useRouter();
  const [role, pickRole] = useState<Role>("regulator");
  const [email, setEmail] = useState("");
  const r = ROLES.find((x) => x.key === role)!;

  const go = () => {
    setRole(role);
    router.push(r.home);
  };

  return (
    <div className="flex h-full min-h-[760px]">
      <div className="relative w-[52.8%] min-w-[600px] overflow-hidden bg-water">
        <MapThumb width="100%" height={2000} dots={false} numbered s={1.245} tx={-377} ty={-278} rounded={false} marker={26} className="absolute inset-0" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[52%] bg-gradient-to-b from-transparent via-[rgba(23,25,28,0.35)] to-[rgba(23,25,28,0.78)]" />
        <div className="absolute bottom-[118px] left-12 right-12 flex flex-col gap-3 text-white">
          <p className="font-serif-display text-[28px] leading-9">
            {pick("“Which sites should my inspectors visit first?”", "“Lokasi mana yang harus diperiksa inspektur saya lebih dulu?”")}
          </p>
          <p className="text-[13px] leading-[19px] text-white/85">
            {pick("The question a groundwater regulator brings to Groundtrace", "Pertanyaan yang dibawa regulator air tanah ke Groundtrace")}
          </p>
        </div>
      </div>

      <div className="flex flex-1 flex-col px-20 pb-10 pt-10">
        <div className="flex items-center">
          <Link href="/story">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
          </Link>
          <span className="flex-1" />
          <button onClick={() => setLang(lang === "EN" ? "ID" : "EN")} className="flex items-center gap-1.5 text-[11px] text-ink-2 hover:text-ink">
            <Globe size={15} strokeWidth={1.8} />
            <span className={lang === "ID" ? "font-semibold text-ink" : ""}>ID</span>/<span className={lang === "EN" ? "font-semibold text-ink" : ""}>EN</span>
          </button>
        </div>

        <div className="mt-auto flex max-w-[520px] flex-col">
          <h1 className="font-display text-[44px] font-normal leading-[52px] tracking-[-0.02em]">{pick("Sign in", "Masuk")}</h1>
          <p className="mt-5 text-[15px] leading-[21px] text-ink-2">
            {pick(
              "Regulators, analysts and planners sign in to see restricted layers. Everyone else can open the public view.",
              "Regulator, analis, dan perencana masuk untuk melihat lapisan terbatas. Siapa pun bisa membuka tampilan publik.",
            )}
          </p>

          <div role="radiogroup" className="mt-5 overflow-hidden rounded-lg border border-line bg-surface">
            {ROLES.map((x) => (
              <button
                key={x.key}
                role="radio"
                aria-checked={role === x.key}
                onClick={() => pickRole(x.key)}
                className={cn(
                  "flex w-full gap-3.5 border-b border-line px-4 py-3 text-left last:border-b-0",
                  role === x.key ? "bg-primary-tint" : "hover:bg-bg",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 size-4 flex-none rounded-full bg-surface",
                    role === x.key ? "shadow-[inset_0_0_0_5px_var(--color-primary)]" : "shadow-[inset_0_0_0_1.5px_var(--color-line-strong)]",
                  )}
                />
                <span className="flex flex-col gap-0.5">
                  <span className="flex items-baseline gap-2 text-[13px] font-medium">
                    {x.title[lang]}
                    <span className="text-xs font-normal text-ink-3">{x.org}</span>
                  </span>
                  <span className="text-xs text-ink-2">{x.text[lang]}</span>
                </span>
              </button>
            ))}
          </div>

          <label className="mt-6 flex flex-col gap-1.5 text-xs">
            {pick("Work email", "Email kantor")}
            <span className="flex h-10 items-center gap-2 rounded-md border border-line-strong bg-surface px-3 focus-within:border-primary">
              <User size={15} strokeWidth={1.8} className="text-ink-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && go()}
                placeholder={r.email}
                className="w-full bg-transparent text-[13px] outline-none placeholder:text-ink-3"
              />
            </span>
          </label>
          <button
            onClick={go}
            className="mt-[18px] flex h-9 items-center justify-center gap-2 rounded-md bg-primary text-[13px] font-medium text-on-primary hover:bg-primary-hover"
          >
            <ArrowRight size={15} strokeWidth={2} />
            {pick("Continue", "Lanjut")}
          </button>

          <div className="my-[22px] flex items-center gap-3 text-xs text-ink-3">
            <span className="h-px flex-1 bg-line" />
            {pick("or", "atau")}
            <span className="h-px flex-1 bg-line" />
          </div>

          <button
            onClick={() => {
              setRole("public");
              router.push("/");
            }}
            className="flex gap-3 rounded-lg border border-line bg-surface px-4 py-4 text-left hover:bg-bg"
          >
            <MapIcon size={16} strokeWidth={1.8} className="mt-0.5 flex-none" />
            <span className="flex flex-1 flex-col gap-1.5">
              <span className="text-[13px] font-medium">{pick("Continue to the public view", "Lanjut ke tampilan publik")}</span>
              <span className="text-xs leading-4 text-ink-2">
                {pick(
                  "Sinking maps, hot-spot cells and land-use classes. No company names, permits or well records.",
                  "Peta penurunan, sel titik panas, dan kelas lahan. Tanpa nama perusahaan, izin, atau catatan sumur.",
                )}
              </span>
            </span>
            <ArrowRight size={16} strokeWidth={1.8} className="mt-0.5 text-ink-2" />
          </button>
        </div>

        <p className="mt-auto flex max-w-[520px] gap-2.5 pt-10 text-xs leading-4 text-ink-3">
          <Lock size={15} strokeWidth={1.8} className="flex-none" />
          {pick(
            "Well records and permit matches sit behind this sign-in. Public views show cells and classes only.",
            "Catatan sumur dan kecocokan izin ada di balik proses masuk ini. Tampilan publik hanya menampilkan sel dan kelas.",
          )}
        </p>
      </div>
    </div>
  );
}
