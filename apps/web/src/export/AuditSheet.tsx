import { Info, Lock } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/components/ui";
import { ranked } from "@/data/run";
import { CHECKS, SHEET_ROWS, SOURCES, type SheetLang } from "@/data/sheet";
import { MapThumb } from "@/map/MapThumb";

const TXT = {
  id: {
    kicker: "Lembar audit",
    restricted: "Hanya regulator",
    publicV: "Versi publik",
    title: "Audit pengambilan air tanah dari citra satelit",
    sub: "Semarang–Demak · Januari 2015 – Oktober 2026 · Sentinel-1 dua arah, terikat ke stasiun GNSS CSEM",
    meta: [
      ["Dibuat", "16 November 2026"],
      ["Disetujui oleh", "A. Wibowo, analis BIG"],
      ["Lebar kerucut B", "1,0 · 1,5 · 2,0 km"],
      ["Status", "Dipublikasikan"],
    ],
    mapNote: "Laju turun vertikal, mm/tahun · titik = titik panas (sel 500 m) · arsir = tanpa data",
    howTo:
      "Cara membaca. Volume adalah simpanan akuifer yang hilang per tahun, yaitu batas bawah air yang dipompa. Rentang 90% berasal dari bootstrap. Lebar kerucut B tidak bisa dipastikan dari radar saja, jadi volume diberikan untuk tiga nilai B. Urutan hampir tidak berubah.",
    cols: ["#", "Sel", "Lokasi", "B 1,0", "B 1,5", "B 2,0", "Rentang 90%", "Stab.", "Lahan", "Izin"],
    tableNote: (pub: boolean) =>
      `Volume dalam ribu m³ per tahun. * Stabilitas di bawah 0,8: muncul di kurang dari 80% pengulangan bootstrap, perlakukan dengan hati-hati.${pub ? "" : " Kolom izin hanya untuk regulator."}`,
    foot1: "Petunjuk, bukan putusan. Titik panas adalah alasan untuk memeriksa meteran, bukan bukti pelanggaran.",
    page: "hal.",
    checks: "Ringkasan pemeriksaan",
    checkCols: ["Kode", "Pemeriksaan", "Nilai", "Batas lulus", "Status"],
    pass: "Lulus",
    waiting: "Menunggu data",
    wellsNote:
      "Belum dicek dengan data sumur. Data muka air dan izin dari Badan Geologi dan Dinas ESDM Jawa Tengah belum diterima, jadi V5 dan V6 belum dijalankan.",
    sources: "Sumber data",
    limits: "Batasan yang diketahui",
    limitItems: [
      "Volume bergantung pada lebar kerucut B. Salah menebak B menggeser semua volume bersama-sama, tetapi urutan hampir tetap.",
      "Metode ini memisahkan lapangan sumur, bukan sumur satu per satu. Dua sumber yang lebih dekat dari sekitar 1,5 km dilaporkan sebagai satu.",
      "Radar kehilangan sinyal di tambak dan sawah. Area itu dibiarkan kosong, tidak diisi tebakan.",
      "Uji sintetis memakai model yang sama untuk membuat dan membaca data. Hasil nyata perlu dicek dengan sumur.",
    ],
    use: "Penggunaan yang bertanggung jawab",
    useItems: [
      ["Titik panas, bukan nama", "Peta publik hanya menampilkan sel 500 m dan kelas lahan."],
      ["Petunjuk, bukan putusan", "Lapangan sumur berizin juga membuat cekungan."],
      ["Sebutkan arti angkanya", "Selalu dengan rentang dan B yang dipakai."],
    ],
    identity: "Identitas run",
    idLines: ["commit kode  a3f9c21", "hash konfigurasi  7e1b42c9", "hash data  d1:5c0a… d4:91be… d8:20f7…", "seed tetap · 200 pengulangan bootstrap"],
    signed: "Disetujui oleh",
    signer: "A. Wibowo · analis geospasial, BIG",
    signDate: "16 November 2026",
    auto: "Dibuat otomatis dari run yang sama dengan peta web.",
  },
  en: {
    kicker: "Audit sheet",
    restricted: "Regulator only",
    publicV: "Public version",
    title: "Groundwater extraction audit from satellite images",
    sub: "Semarang–Demak · January 2015 – October 2026 · Sentinel-1 two directions, tied to GNSS station CSEM",
    meta: [
      ["Generated", "16 November 2026"],
      ["Signed off by", "A. Wibowo, BIG analyst"],
      ["Cone width B", "1.0 · 1.5 · 2.0 km"],
      ["Status", "Published"],
    ],
    mapNote: "Vertical sinking rate, mm/yr · dot = hot spot (500 m cell) · hatched = no data",
    howTo:
      "How to read. Volume is the aquifer storage lost per year, a lower bound on water pumped. 90% ranges come from a bootstrap. Radar alone cannot fix the cone width B, so volumes are given for three values of B. The order barely changes.",
    cols: ["#", "Cell", "Place", "B 1.0", "B 1.5", "B 2.0", "90% range", "Stab.", "Land", "Permit"],
    tableNote: (pub: boolean) =>
      `Volumes in thousand m³ per year. * Stability below 0.8: appears in fewer than 80% of bootstrap reruns, treat with care.${pub ? "" : " The permit column is for regulators only."}`,
    foot1: "A lead, not a verdict. A hot spot is a reason to inspect a meter, not proof of a violation.",
    page: "p.",
    checks: "Check summary",
    checkCols: ["Code", "Check", "Value", "Pass mark", "Status"],
    pass: "Passed",
    waiting: "Waiting for data",
    wellsNote:
      "Not yet checked against wells. Groundwater heads and permits from the Geological Agency and ESDM Central Java have not arrived, so V5 and V6 have not run.",
    sources: "Data sources",
    limits: "Known limits",
    limitItems: [
      "Volumes depend on the cone width B. Guessing B wrong shifts every volume together, but the order barely moves.",
      "The method separates well fields, not single wells. Two sources closer than about 1.5 km are reported as one.",
      "Radar loses signal over fish ponds and rice fields. Those areas stay empty, never filled with a guess.",
      "The synthetic test uses the same model to make and read the data. Real results need checking against wells.",
    ],
    use: "Responsible use",
    useItems: [
      ["Hot spots, not names", "Public maps show 500 m cells and land-use classes only."],
      ["A lead, not a verdict", "A permitted well field also makes a bowl."],
      ["Say what the number is", "Always with its range and the B assumed."],
    ],
    identity: "Run identity",
    idLines: ["code commit  a3f9c21", "config hash  7e1b42c9", "data hash  d1:5c0a… d4:91be… d8:20f7…", "fixed seed · 200 bootstrap reruns"],
    signed: "Signed off by",
    signer: "A. Wibowo · geospatial analyst, BIG",
    signDate: "16 November 2026",
    auto: "Generated automatically from the same run as the web map.",
  },
};

const dec = (lang: SheetLang, v: number) => (lang === "id" ? v.toFixed(2).replace(".", ",") : v.toFixed(2));

function Page({ children }: { children: ReactNode }) {
  return (
    <div className="sheet-page relative mx-auto flex h-[1123px] w-[794px] flex-col bg-white px-12 pb-10 pt-10 text-ink shadow-card print:shadow-none">
      {children}
    </div>
  );
}

function Head({ lang, pub }: { lang: SheetLang; pub: boolean }) {
  const T = TXT[lang];
  return (
    <div className="flex h-[30px] items-center border-b-2 border-ink pb-[18px] pt-0" style={{ boxSizing: "content-box" }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
      <span className="flex-1" />
      <span className="mr-3 text-[11px] uppercase tracking-[0.12em] text-ink-2">{T.kicker} · R-0007</span>
      {pub ? (
        <span className="inline-flex h-[22px] items-center rounded-full bg-subtle px-2.5 text-xs font-medium text-ink-2">{T.publicV}</span>
      ) : (
        <span className="inline-flex h-[22px] items-center gap-1.5 rounded-full bg-ink px-2.5 text-xs font-medium text-white">
          <Lock size={13} strokeWidth={2} />
          {T.restricted}
        </span>
      )}
    </div>
  );
}

function Foot({ left, page }: { left: ReactNode; page: string }) {
  return (
    <div className="mt-auto flex items-end gap-6 border-t border-line pt-3 text-xs leading-4 text-ink-2">
      <span className="max-w-[380px]">{left}</span>
      <span className="flex-1" />
      <span className="text-[11px] text-ink-3">{page}</span>
    </div>
  );
}

const H2 = "font-serif-display text-[22px] leading-7 text-ink";

export function AuditSheet({ lang, pub }: { lang: SheetLang; pub: boolean }) {
  const T = TXT[lang];
  const rows = ranked("mid");
  const cols = pub ? T.cols.slice(0, 9) : T.cols;
  const grid = pub
    ? "grid-cols-[20px_72px_1fr_40px_44px_44px_78px_48px_150px]"
    : "grid-cols-[20px_72px_118px_40px_44px_44px_78px_48px_100px_1fr]";
  return (
    <>
      <Page>
        <Head lang={lang} pub={pub} />
        <h1 className="font-serif-display mt-5 text-[34px] leading-10">{T.title}</h1>
        <p className="mt-2 text-[13px] leading-[19px] text-ink-2">{T.sub}</p>
        <div className="mt-4 grid grid-cols-4 rounded-lg border border-line">
          {T.meta.map(([k, v]) => (
            <div key={k} className="flex flex-col gap-0.5 px-2.5 py-2 [&+&]:border-l [&+&]:border-line">
              <span className="text-xs text-ink-3">{k}</span>
              <span className="text-[13px]">{v}</span>
            </div>
          ))}
        </div>

        <div className="relative mt-[18px]">
          <MapThumb width={698} height={250} numbered s={0.864} tx={-64} ty={-212} className="rounded-md" lang={lang} />
          <span className="absolute bottom-3 left-2.5 rounded bg-white px-2 py-1 text-xs text-ink-2">{T.mapNote}</span>
        </div>

        <div className="mt-[18px] flex gap-2.5 rounded-lg bg-bg px-3.5 py-2.5 text-xs leading-4">
          <Info size={15} strokeWidth={1.9} className="mt-px flex-none text-ink-2" />
          <span>{T.howTo}</span>
        </div>

        <div className="mt-6 text-[13px]">
          <div className={cn("grid border-b border-ink pb-2 font-mono text-[10px] uppercase tracking-[0.06em] text-ink-2", grid)}>
            {cols.map((c, i) => (
              <span key={c} className={cn("whitespace-nowrap", i >= 3 && i <= 7 && "text-right", i === 8 && "pl-2.5")}>
                {c}
              </span>
            ))}
          </div>
          {rows.map((h, i) => {
            const r = SHEET_ROWS[h.id];
            const low = h.stability < 0.8;
            return (
              <div key={h.id} className={cn("grid items-start border-b border-line py-[7px] leading-4", grid, i % 2 === 1 && "bg-bg")}>
                <span>{i + 1}</span>
                <span className="text-xs text-ink-2">{h.id}</span>
                <span>{h.place}</span>
                <span className="text-right text-xs text-ink-2">{h.volume.low.v}</span>
                <span className="text-right text-xs font-semibold">{h.volume.mid.v}</span>
                <span className="text-right text-xs text-ink-2">{h.volume.high.v}</span>
                <span className="text-right text-xs text-ink-2">
                  {h.volume.mid.lo}–{h.volume.mid.hi}
                </span>
                <span className="text-right text-xs text-ink-2">
                  {dec(lang, h.stability)}
                  {low && "*"}
                </span>
                <span className="pl-2.5">{r.land[lang]}</span>
                {!pub && <span>{r.permit[lang]}</span>}
              </div>
            );
          })}
          <p className="mt-3 text-xs leading-4 text-ink-3">{T.tableNote(pub)}</p>
        </div>

        <Foot left={T.foot1} page={`commit a3f9c21 · config 7e1b42 · ${T.page} 1/2`} />
      </Page>

      <Page>
        <Head lang={lang} pub={pub} />
        <h2 className={cn(H2, "mt-4")}>{T.checks}</h2>
        <div className="mt-3 text-xs">
          <div className="grid grid-cols-[48px_220px_170px_130px_1fr] border-b border-ink pb-2 font-mono text-[10px] uppercase tracking-[0.08em] text-ink-2">
            {T.checkCols.map((c) => (
              <span key={c}>{c}</span>
            ))}
          </div>
          {CHECKS.map((c) => (
            <div key={c.code} className="grid h-[30px] grid-cols-[48px_220px_170px_130px_1fr] items-center border-b border-line">
              <span>
                <span className="inline-flex h-[18px] items-center rounded-sm border border-line-strong px-1.5 text-[11px] text-ink-2">{c.code}</span>
              </span>
              <span className="text-[13px]">{c.name[lang]}</span>
              <span className="text-[11px] text-ink-2">{c.value[lang]}</span>
              <span className="text-[11px] text-ink-2">{c.mark[lang]}</span>
              <span>
                <span
                  className={cn(
                    "inline-flex h-[22px] items-center gap-1.5 rounded-full px-2 text-xs font-medium",
                    c.result === "pass" ? "bg-pass-tint text-pass" : "bg-warn-tint text-warn",
                  )}
                >
                  <i className={cn("size-1.5 rounded-full", c.result === "pass" ? "bg-pass" : "bg-warn")} />
                  {c.result === "pass" ? T.pass : T.waiting}
                </span>
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 rounded-md bg-warn-tint px-3 py-2.5 text-xs leading-4">{T.wellsNote}</div>

        <h2 className={cn(H2, "mt-4")}>{T.sources}</h2>
        <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-[13px]">
          {SOURCES.map((s) => (
            <div key={s.code} className="flex items-center gap-2">
              <span className="inline-flex h-[18px] items-center rounded-sm border border-line-strong px-1.5 text-[11px] text-ink-2">{s.code}</span>
              <span>{s.name[lang]}</span>
              <span className="flex-1" />
              <span className={cn("text-[11px]", s.warn ? "text-warn" : "text-ink-3")}>{s.status[lang]}</span>
            </div>
          ))}
        </div>

        <h2 className={cn(H2, "mt-4")}>{T.limits}</h2>
        <ul className="mt-3 flex flex-col gap-2.5 text-xs leading-4">
          {T.limitItems.map((l) => (
            <li key={l} className="flex gap-2.5">
              <i className="mt-1.5 size-[5px] flex-none bg-ink" />
              {l}
            </li>
          ))}
        </ul>

        <h2 className={cn(H2, "mt-4")}>{T.use}</h2>
        <div className="mt-3 grid grid-cols-3 gap-2.5">
          {T.useItems.map(([h, p]) => (
            <div key={h} className="flex flex-col gap-1 rounded-md border border-line px-2.5 py-2.5">
              <span className="text-xs font-medium">{h}</span>
              <span className="text-xs leading-4 text-ink-2">{p}</span>
            </div>
          ))}
        </div>

        <div className="mt-auto flex items-end gap-10 pb-3 pt-6">
          <div className="flex flex-1 flex-col gap-0.5 text-[11px] leading-4 text-ink-2">
            <span className="mb-0.5 uppercase tracking-[0.08em] text-ink-3">{T.identity}</span>
            {T.idLines.map((l) => (
              <span key={l} className="whitespace-pre">
                {l}
              </span>
            ))}
          </div>
          <div className="flex w-[240px] flex-col">
            <span className="mb-9 text-[11px] uppercase tracking-[0.12em] text-ink-3">{T.signed}</span>
            <span className="border-t border-ink pt-2 text-xs">{T.signer}</span>
            <span className="mt-1 text-[11px] text-ink-3">{T.signDate}</span>
          </div>
        </div>
        <Foot left={T.auto} page={`${T.page} 2/2`} />
      </Page>
    </>
  );
}
