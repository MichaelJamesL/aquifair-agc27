"use client";

import { ArrowRight, Check, Clock, Globe, Map as MapIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/components/ui";
import { HOT_SPOTS, ranked, rankOf } from "@/data/run";
import { MapThumb } from "@/map/MapThumb";
import { Marker } from "@/map/Marker";
import { useStore } from "@/state";

type L = "EN" | "ID";
const tx = (en: string, id: string) => ({ EN: en, ID: id });

const C = {
  nav: [
    ["#problem", tx("The problem", "Masalahnya")],
    ["#how", tx("How it works", "Cara kerja")],
    ["#evidence", tx("Evidence", "Bukti")],
    ["#limits", tx("Limits", "Batasan")],
    ["#data", tx("Data", "Data")],
  ] as const,
  signIn: tx("Sign in", "Masuk"),
  openMap: tx("Open the map", "Buka peta"),
  howBtn: tx("How it works", "Cara kerja"),
  kicker: tx("ASEAN Geospatial Challenge 2027 · Semarang–Demak", "ASEAN Geospatial Challenge 2027 · Semarang–Demak"),
  h1: tx("Semarang is sinking. The ground shows where the pumping is.", "Semarang tenggelam. Tanahnya menunjukkan di mana air dipompa."),
  lede: tx(
    "Satellites already show where the coast of Central Java is sinking. Groundtrace works out which pumping causes it, and how much: a ranked list of groundwater extraction hot spots, each with a volume and an error bar, made without a well registry.",
    "Satelit sudah menunjukkan di mana pesisir Jawa Tengah turun. Groundtrace mencari pemompaan mana penyebabnya, dan seberapa besar: daftar berurutan titik panas pengambilan air tanah, masing-masing dengan volume dan rentang galat, tanpa daftar sumur.",
  ),
  heroTip: { place: "#1 · Terboyo, Genuk", vol: "286k m³/yr", range: tx("90% range 212–351k · lower bound", "rentang 90% 212–351k · batas bawah") },
  heroCap: tx("Vertical sinking 2015–2026, mm/yr. Hatched: no radar signal.", "Penurunan vertikal 2015–2026, mm/thn. Arsir: tanpa sinyal radar."),
  problem: [
    ["14 cm", tx("a year", "per tahun"), tx("The fastest sinking measured in Semarang and Demak, 2020–2023. Tidal floods (rob) keep getting worse.", "Penurunan tercepat yang terukur di Semarang dan Demak, 2020–2023. Banjir rob makin parah.")],
    ["2010", tx("", ""), tx("The last year with usable well records. By then more than 1,000 deep wells were pumping.", "Tahun terakhir dengan catatan sumur yang bisa dipakai. Saat itu lebih dari 1.000 sumur dalam sudah memompa.")],
    [tx("Which wells?", "Sumur yang mana?"), tx("", ""), tx("Permits exist, but nobody can say which pumping does the damage. Inspectors have no list to start from.", "Izin ada, tetapi tidak ada yang bisa bilang pemompaan mana yang merusak. Inspektur tidak punya daftar untuk mulai.")],
  ] as const,
  idea: {
    kicker: tx("The idea", "Gagasannya"),
    h: tx("Pumping leaves a fingerprint on the ground", "Pemompaan meninggalkan sidik jari di tanah"),
    p: tx(
      "We read the chain backwards, from 4 to 1. The shape of each bowl tells us where the pumping sits and how much storage is lost there.",
      "Kami membaca rantainya dari belakang, dari 4 ke 1. Bentuk tiap cekungan memberi tahu di mana pemompaan berada dan berapa simpanan yang hilang di sana.",
    ),
    labels: [tx("Pumping", "Pemompaan"), tx("Pressure cone", "Kerucut tekanan"), tx("Clay compacts", "Lempung memadat"), tx("Ground sinks", "Tanah turun")],
    side: {
      sat: tx("radar satellite, two viewing directions", "satelit radar, dua arah pandang"),
      pre: tx("pressure before pumping", "tekanan sebelum pemompaan"),
      clay: tx("clay", "lempung"),
      aq: tx("aquifer: sand and water", "akuifer: pasir dan air"),
    },
    steps: [
      tx("A deep well pumps water out.", "Sumur dalam memompa air keluar."),
      tx("Water pressure falls in a cone several kilometres wide.", "Tekanan air turun membentuk kerucut selebar beberapa kilometer."),
      tx("Clay drains and compacts. Most of this is permanent.", "Air lempung terkuras dan lempung memadat. Sebagian besar permanen."),
      tx("The ground sinks in the same cone shape. Radar measures it from space.", "Tanah turun dengan bentuk kerucut yang sama. Radar mengukurnya dari angkasa."),
    ],
  },
  solution: {
    kicker: tx("The solution", "Solusinya"),
    h: tx("From a sinking map to an audit list", "Dari peta penurunan ke daftar audit"),
    cards: [
      [tx("Input: the sinking map", "Masukan: peta penurunan"), "O1", tx("Ten years of radar, two directions, 100 m pixels.", "Sepuluh tahun radar, dua arah, piksel 100 m.")],
      [tx("Sources located", "Sumber ditemukan"), "M6", tx("The fewest pumping cones that explain the sinking. Dot size is volume.", "Jumlah kerucut pemompaan paling sedikit yang menjelaskan penurunan. Ukuran titik = volume.")],
      [tx("Output: the audit list", "Keluaran: daftar audit"), "O3", tx("Thousand m³ per year of lost storage, a lower bound on water pumped. Line: 90% range.", "Ribu m³ per tahun simpanan yang hilang, batas bawah air yang dipompa. Garis: rentang 90%.")],
    ] as const,
    note: tx(
      "One of 20 simulated test maps, with the noise and data gaps of real radar. Eight sources were hidden; the method found all eight and ranked them. A run on real Semarang data is the next step.",
      "Salah satu dari 20 peta uji simulasi, dengan noise dan celah data seperti radar asli. Delapan sumber disembunyikan; metode menemukan kedelapannya dan mengurutkannya. Run dengan data asli Semarang adalah langkah berikutnya.",
    ),
  },
  method: {
    kicker: tx("The method in three moves", "Metode dalam tiga langkah"),
    h: tx("Measure, separate, invert", "Ukur, pisahkan, balikkan"),
    moves: [
      ["1", tx("Measure", "Ukur"), "M1–M3", tx("Ten years of Sentinel-1 radar from two directions. Result: vertical motion for every 100 m pixel, tied to BIG’s own GNSS stations.", "Sepuluh tahun radar Sentinel-1 dari dua arah. Hasil: gerak vertikal tiap piksel 100 m, terikat ke stasiun GNSS milik BIG.")],
      ["2", tx("Separate", "Pisahkan"), "M4–M5", tx("Remove what is not pumping: natural clay settling, building load, seasons. Learned by boosted trees on quiet pixels only.", "Buang yang bukan pemompaan: pemadatan alami lempung, beban bangunan, musim. Dipelajari boosted trees hanya dari piksel tenang.")],
      ["3", tx("Invert", "Balikkan"), "M6–M9", tx("Find the fewest pumping cones that explain the rest. A bootstrap gives every source a range and a stability score.", "Cari kerucut pemompaan paling sedikit yang menjelaskan sisanya. Bootstrap memberi tiap sumber rentang dan skor stabilitas.")],
    ] as const,
  },
  evidence: {
    kicker: tx("Evidence so far", "Bukti sejauh ini"),
    h: tx("Only the sparse inversion finds the sources and avoids false alarms", "Hanya inversi jarang yang menemukan sumber sekaligus menghindari alarm palsu"),
    box: tx("20 simulated maps, 146 hidden sources", "20 peta simulasi, 146 sumber tersembunyi"),
    rows: [
      [tx("Add up each bowl by hand", "Jumlahkan tiap cekungan secara manual"), 28, 89],
      [tx("Smooth inversion, closest earlier work", "Inversi halus, karya terdekat sebelumnya"), 90, 35],
      [tx("Sparse inversion, this project", "Inversi jarang, proyek ini"), 89, 80],
    ] as const,
    found: tx("sources found", "sumber ditemukan"),
    real: tx("detections that are real", "deteksi yang nyata"),
    stats: [
      ["7%", tx("median volume error, when the cone width is known", "galat volume median, bila lebar kerucut diketahui")],
      ["59 m", tx("median position error", "galat posisi median")],
      ["85%", tx("of true volumes fall inside the stated 90% range", "volume sebenarnya masuk ke rentang 90% yang dinyatakan")],
    ] as const,
    limitKicker: tx("Honest limit", "Batasan yang jujur"),
    limitH: tx("One number we cannot see from space", "Satu angka yang tidak terlihat dari angkasa"),
    limitP: tx(
      "Volumes depend on the width of a pumping cone. Guess it wrong and every volume shifts together. The order of the list barely moves.",
      "Volume bergantung pada lebar kerucut pemompaan. Salah menebaknya membuat semua volume bergeser bersama. Urutan daftar hampir tidak berubah.",
    ),
    total: tx("Total volume, as a multiple of the truth", "Total volume, sebagai kelipatan nilai sebenarnya"),
    truth: tx("1 = truth", "1 = sebenarnya"),
    rank: tx("Ranking kept (rank correlation, 1 = perfect)", "Urutan terjaga (korelasi peringkat, 1 = sempurna)"),
    rankRange: tx("0.86 to 0.94", "0,86 sampai 0,94"),
  },
  diff: {
    kicker: tx("What makes it different", "Apa bedanya"),
    h: tx("A short list with volumes and error bars, without a well registry", "Daftar pendek dengan volume dan rentang galat, tanpa daftar sumur"),
    cols: [tx("No registry needed", "Tanpa daftar sumur"), tx("Short list of sources", "Daftar sumber pendek"), tx("Volume per source", "Volume per sumber"), tx("Error bar per source", "Rentang galat per sumber"), tx("Natural part removed", "Bagian alami dibuang")],
    rows: [
      [tx("Subsidence maps", "Peta penurunan tanah"), ["y", "", "", "", ""]],
      [tx("Groundwater flow model", "Model aliran air tanah"), ["", "", "", "", "p"]],
      [tx("Smooth inversion, Semarang 2025", "Inversi halus, Semarang 2025"), ["y", "", "p", "", ""]],
      [tx("This project", "Proyek ini"), ["y", "y", "y", "y", "y"]],
    ] as const,
    partly: tx("partly", "sebagian"),
    note: tx(
      "Closest precedent abroad: a California study guided by a public well registry. Our ticks are shown in simulation so far.",
      "Contoh terdekat di luar negeri: studi di California yang dipandu daftar sumur publik. Centang kami sejauh ini dari simulasi.",
    ),
  },
  stands: {
    kicker: tx("Where it stands", "Posisinya sekarang"),
    h: tx("Proven parts, simulated parts, and what is next", "Bagian yang terbukti, bagian yang disimulasikan, dan langkah berikutnya"),
    cards: [
      ["ok", tx("Proven by others", "Dibuktikan pihak lain"), tx("Measuring Semarang’s sinking with this satellite: four published studies.", "Mengukur penurunan Semarang dengan satelit ini: empat studi terbit.")],
      ["ok", tx("Works in simulation", "Berhasil di simulasi"), tx("Finding, ranking and sizing sources, with ranges that hold up.", "Menemukan, mengurutkan, dan mengukur sumber, dengan rentang yang tepat.")],
      ["next", tx("Not done yet", "Belum selesai"), tx("A run on real Semarang data: one week, four pass marks.", "Run dengan data asli Semarang: satu minggu, empat batas lulus.")],
    ] as const,
  },
  use: {
    kicker: tx("Responsible use", "Penggunaan yang bertanggung jawab"),
    h: tx("Places have owners. Three rules keep it fair.", "Tempat punya pemilik. Tiga aturan menjaganya adil."),
    rules: [
      [tx("Hot spots, not names", "Titik panas, bukan nama"), tx("Public maps show 500 m cells and land-use classes. Any link to a permit holder is for the regulator only.", "Peta publik menampilkan sel 500 m dan kelas lahan. Kaitan ke pemegang izin hanya untuk regulator.")],
      [tx("A lead, not a verdict", "Petunjuk, bukan putusan"), tx("A detected source is a reason to inspect a meter, not proof of a violation. A permitted well field also makes a bowl.", "Sumber yang terdeteksi adalah alasan memeriksa meteran, bukan bukti pelanggaran. Lapangan sumur berizin juga membuat cekungan.")],
      [tx("Say what the number is", "Sebutkan arti angkanya"), tx("Every volume is labelled as lost storage and as a lower bound on extraction, with its range and the assumed cone width.", "Setiap volume diberi label simpanan yang hilang dan batas bawah pengambilan, dengan rentang dan lebar kerucut yang dipakai.")],
    ] as const,
  },
  closing: tx("See the hot spots for yourself", "Lihat sendiri titik panasnya"),
  readMethod: tx("Read the method", "Baca metodenya"),
  footer: [
    tx("Team Ganesha Makara · ASEAN Geospatial Challenge 2027, National Level: Indonesia", "Tim Ganesha Makara · ASEAN Geospatial Challenge 2027, Tingkat Nasional: Indonesia"),
    tx("Data: Copernicus Sentinel-1, LiCSAR, GACOS, InaCORS and DEMNAS (BIG), OpenStreetMap", "Data: Copernicus Sentinel-1, LiCSAR, GACOS, InaCORS dan DEMNAS (BIG), OpenStreetMap"),
  ],
};

const WRAP = "mx-auto w-full max-w-[1200px]";
const H2 = "font-display text-[40px] font-normal leading-[46px] tracking-[-0.02em]";

/** 01 · Story page (public landing) */
export function StoryPage() {
  const { lang, setLang } = useStore();
  const l = lang as L;

  return (
    <div className="h-full overflow-y-auto scroll-smooth bg-bg">
      {/* nav */}
      <nav className="sticky top-0 z-20 border-b border-transparent bg-bg/92 backdrop-blur">
        <div className={cn(WRAP, "flex h-[72px] items-center gap-6")}>
          <Link href="/story">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
          </Link>
          <span className="w-1" />
          {C.nav.map(([href, t]) => (
            <a key={href} href={href} className="text-[13px] font-medium text-ink-2 hover:text-ink">
              {t[l]}
            </a>
          ))}
          <span className="flex-1" />
          <button onClick={() => setLang(lang === "EN" ? "ID" : "EN")} className="flex items-center gap-1.5 text-[11px] text-ink-2">
            <Globe size={15} strokeWidth={1.8} />
            <span className={lang === "ID" ? "font-semibold text-ink" : ""}>ID</span>
            <span>/</span>
            <span className={lang === "EN" ? "font-semibold text-ink" : ""}>EN</span>
          </button>
          <Link href="/sign-in" className="flex h-9 items-center rounded-md px-3.5 text-[13px] font-medium hover:bg-subtle">
            {C.signIn[l]}
          </Link>
          <PrimaryLink href="/">{C.openMap[l]}</PrimaryLink>
        </div>
      </nav>

      {/* hero */}
      <section className={cn(WRAP, "flex h-[640px] items-center gap-14")}>
        <div className="flex w-[500px] flex-none flex-col">
          <span className="eyebrow text-primary">{C.kicker[l]}</span>
          <h1 className="font-serif-display mt-5 text-[54px] leading-[58px]">{C.h1[l]}</h1>
          <p className="mt-6 max-w-[480px] text-sm leading-[21px] text-ink-2">{C.lede[l]}</p>
          <div className="mt-6 flex gap-2.5">
            <PrimaryLink href="/">{C.openMap[l]}</PrimaryLink>
            <a href="#how" className="flex h-9 items-center gap-2 rounded-md border border-line-strong bg-surface px-3.5 text-[13px] font-medium hover:bg-subtle">
              <ArrowRight size={15} strokeWidth={1.9} />
              {C.howBtn[l]}
            </a>
          </div>
        </div>
        <HeroMap l={l} />
      </section>

      {/* the problem */}
      <section id="problem" className="scroll-mt-[72px] border-y border-line">
        <div className={cn(WRAP, "grid grid-cols-[382px_409px_1fr]")}>
          {C.problem.map(([big, small, text], i) => (
            <div key={i} className={cn("flex flex-col gap-3 py-7", i > 0 && "border-l border-line pl-7")}>
              <span className="flex items-baseline gap-2">
                <span className="font-display text-[40px] leading-[48px] tracking-[-0.02em]">{typeof big === "string" ? big : big[l]}</span>
                {small[l] && <span className="text-sm text-ink-2">{small[l]}</span>}
              </span>
              <p className="max-w-[330px] text-[13px] leading-[19px] text-ink-2">{text[l]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* how it works */}
      <section id="how" className={cn(WRAP, "scroll-mt-[72px] pb-10 pt-20")}>
        <div className="flex items-end">
          <SectionHead kicker={C.idea.kicker[l]} h={C.idea.h[l]} width={560} />
          <span className="flex-1" />
          <p className="w-[440px] pb-1 text-sm leading-[21px] text-ink-2">{C.idea.p[l]}</p>
        </div>
        <CrossSection l={l} />
        <div className="mt-7 grid grid-cols-4 gap-5">
          {C.idea.steps.map((s, i) => (
            <div key={i} className="flex gap-3">
              <Num n={i + 1} />
              <p className="max-w-[240px] text-[13px] leading-[19px]">{s[l]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* solution */}
      <section id="method" className={cn(WRAP, "scroll-mt-[72px] pb-10 pt-20")}>
        <SectionHead kicker={C.solution.kicker[l]} h={C.solution.h[l]} width={760} />
        <div className="mt-7 grid grid-cols-3 items-start gap-5">
          {C.solution.cards.map(([title, code, cap], i) => (
            <div key={code} className="flex flex-col gap-3 rounded-[10px] border border-line bg-surface p-4">
              <div className="flex items-center text-[13px] font-medium">
                {title[l]}
                <span className="flex-1" />
                <span className="text-[11px] font-normal text-ink-3">{code}</span>
              </div>
              {i === 0 && <MapThumb width={353} height={250} dots={false} s={0.449} tx={-23.5} ty={-76.4} />}
              {i === 1 && <SourcesThumb />}
              {i === 2 && <AuditBars />}
              <p className="text-xs leading-4 text-ink-2">{cap[l]}</p>
            </div>
          ))}
        </div>
        <p className="mt-7 max-w-[900px] text-[13px] leading-[19px] text-ink-3">{C.solution.note[l]}</p>
      </section>

      {/* method */}
      <section className={cn(WRAP, "pb-0 pt-20")}>
        <SectionHead kicker={C.method.kicker[l]} h={C.method.h[l]} width={760} />
        <div className="mt-7 grid grid-cols-3 gap-5">
          {C.method.moves.map(([n, name, codes, text]) => (
            <div key={n} className="flex flex-col gap-3 pt-5">
              <span className="flex items-baseline gap-2.5">
                <span className="font-display text-[40px] leading-[44px] text-primary">{n}</span>
                <span className="text-lg font-semibold">{name[l]}</span>
                <span className="rounded-sm border border-line-strong px-1 text-[10px] leading-[14px] text-ink-2">{codes}</span>
              </span>
              <p className="max-w-[360px] text-[13px] leading-[19px] text-ink-2">{text[l]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* evidence */}
      <section id="evidence" className={cn(WRAP, "scroll-mt-[72px] pt-20")}>
        <SectionHead kicker={C.evidence.kicker[l]} h={C.evidence.h[l]} width={760} />
        <div className="mt-7 flex gap-10">
          <div className="flex w-[800px] flex-none flex-col gap-3 rounded-[10px] border border-line bg-surface px-5 py-5">
            <span className="text-[13px] font-medium">{C.evidence.box[l]}</span>
            {C.evidence.rows.map(([name, found, real]) => (
              <div key={name.EN} className="flex flex-col gap-1.5 pt-1">
                <span className="text-[13px] text-ink-2">{name[l]}</span>
                <EvBar pct={found} tone="bg-primary" text={`${found}% ${C.evidence.found[l]}`} />
                <EvBar pct={real} tone="bg-range" text={`${real}% ${C.evidence.real[l]}`} />
              </div>
            ))}
          </div>
          <div className="flex flex-1 flex-col">
            {C.evidence.stats.map(([v, t]) => (
              <div key={v} className="flex flex-col gap-1 border-b border-line py-4 first:pt-3">
                <span className="font-display text-[40px] leading-[48px] tracking-[-0.02em]">{l === "ID" ? v.replace(".", ",") : v}</span>
                <span className="text-[13px] text-ink-2">{t[l]}</span>
              </div>
            ))}
          </div>
        </div>

        <div id="limits" className="mt-7 flex scroll-mt-[90px] gap-10 rounded-xl bg-ink px-7 py-7 text-bg">
          <div className="flex w-[460px] flex-col gap-2">
            <span className="eyebrow text-bg/80">{C.evidence.limitKicker[l]}</span>
            <h3 className="font-display text-[28px] leading-[35px] tracking-[-0.01em]">{C.evidence.limitH[l]}</h3>
            <p className="text-[13px] leading-[19px] text-bg/80">{C.evidence.limitP[l]}</p>
          </div>
          <span className="flex-1" />
          <div className="flex w-[460px] flex-col gap-3 text-xs">
            <span>{C.evidence.total[l]}</span>
            <span className="h-2 rounded bg-[#e9b46c]" />
            <span className="flex justify-between text-[11px] text-bg/80">
              <span>{l === "ID" ? "0,43" : "0.43"}</span>
              <span>{C.evidence.truth[l]}</span>
              <span>{l === "ID" ? "2,08" : "2.08"}</span>
            </span>
            <span className="mt-2">{C.evidence.rank[l]}</span>
            <span className="relative h-2">
              <span className="absolute inset-x-0 top-[3px] h-0.5 bg-bg/35" />
              <span className="absolute top-0 h-2 rounded bg-[#e9b46c]" style={{ left: "86%", width: "8%" }} />
            </span>
            <span className="flex justify-between text-[11px] text-bg/80">
              <span>0</span>
              <span>{C.evidence.rankRange[l]}</span>
              <span>1</span>
            </span>
          </div>
        </div>
      </section>

      {/* what makes it different */}
      <section className={cn(WRAP, "pt-20")}>
        <SectionHead kicker={C.diff.kicker[l]} h={C.diff.h[l]} width={767} />
        <div className="mt-7 overflow-hidden rounded-[10px] border border-line bg-surface">
          <div className="grid h-10 grid-cols-[380px_repeat(5,150px)] items-center bg-bg text-center text-xs font-medium text-ink-2">
            <span />
            {C.diff.cols.map((c) => (
              <span key={c.EN}>{c[l]}</span>
            ))}
          </div>
          {C.diff.rows.map(([name, cells], i) => (
            <div
              key={name.EN}
              className={cn("grid h-12 grid-cols-[380px_repeat(5,150px)] items-center border-t border-line text-center", i === 3 && "bg-primary-tint")}
            >
              <span className={cn("pl-5 text-left text-[13px]", i === 3 ? "font-medium" : "text-ink-2")}>{name[l]}</span>
              {cells.map((c, k) => (
                <span key={k} className="flex justify-center text-xs text-ink-3">
                  {c === "y" ? <Check size={16} strokeWidth={1.8} className={i === 3 ? "text-primary" : "text-ink-2"} /> : c === "p" ? C.diff.partly[l] : ""}
                </span>
              ))}
            </div>
          ))}
        </div>
        <p className="mt-7 max-w-[900px] text-[13px] leading-[19px] text-ink-3">{C.diff.note[l]}</p>
      </section>

      {/* where it stands */}
      <section className={cn(WRAP, "pt-20")}>
        <SectionHead kicker={C.stands.kicker[l]} h={C.stands.h[l]} width={760} />
        <div className="mt-7 grid grid-cols-3 gap-5">
          {C.stands.cards.map(([k, h, p]) => (
            <div key={h.EN} className="flex flex-col gap-2 rounded-[10px] border border-line bg-surface px-5 py-5">
              <span className="flex items-center gap-2.5 text-[15px] font-semibold">
                {k === "ok" ? <Check size={16} strokeWidth={2} className="text-pass" /> : <Clock size={16} strokeWidth={2} className="text-warn" />}
                {h[l]}
              </span>
              <p className="text-[13px] leading-[19px] text-ink-2">{p[l]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* responsible use */}
      <section className={cn(WRAP, "pt-20")}>
        <SectionHead kicker={C.use.kicker[l]} h={C.use.h[l]} width={760} />
        <div className="mt-7 grid grid-cols-3 gap-5">
          {C.use.rules.map(([h, p]) => (
            <div key={h.EN} className="flex flex-col gap-2.5 border-t border-ink pt-4">
              <span className="text-[15px] font-semibold">{h[l]}</span>
              <p className="max-w-[360px] text-[13px] leading-[19px] text-ink-2">{p[l]}</p>
            </div>
          ))}
        </div>
      </section>

      {/* closing */}
      <section className="flex flex-col items-center gap-7 pb-16 pt-24">
        <h2 className={cn(H2, "text-center")}>{C.closing[l]}</h2>
        <div className="flex gap-2.5">
          <PrimaryLink href="/">{C.openMap[l]}</PrimaryLink>
          <a href="#how" className="flex h-9 items-center gap-2 rounded-md border border-line-strong bg-surface px-3.5 text-[13px] font-medium hover:bg-subtle">
            <ArrowRight size={15} strokeWidth={1.9} />
            {C.readMethod[l]}
          </a>
        </div>
      </section>

      <footer id="data" className="border-t border-line">
        <div className={cn(WRAP, "flex h-[75px] items-center gap-5 text-xs text-ink-2")}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.svg" width={138} height={27} alt="Groundtrace" />
          <span>{C.footer[0][l]}</span>
          <span className="flex-1" />
          <span>{C.footer[1][l]}</span>
        </div>
      </footer>
    </div>
  );
}

function PrimaryLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="flex h-9 items-center gap-2 rounded-md bg-primary px-3.5 text-[13px] font-medium text-on-primary hover:bg-primary-hover">
      <MapIcon size={15} strokeWidth={1.9} />
      {children}
    </Link>
  );
}

function SectionHead({ kicker, h, width }: { kicker: string; h: string; width: number }) {
  return (
    <div className="flex flex-col gap-2.5" style={{ maxWidth: width }}>
      <span className="eyebrow text-primary">{kicker}</span>
      <h2 className={H2}>{h}</h2>
    </div>
  );
}

function Num({ n }: { n: number }) {
  return <span className="grid size-6 flex-none place-items-center rounded-full bg-ink text-[11px] text-bg">{n}</span>;
}

function HeroMap({ l }: { l: L }) {
  // framing of the 644 × 520 hero map, from the Figma frame
  const s = 0.864;
  const ox = -133.3;
  const oy = -171.7;
  return (
    <div className="relative h-[520px] flex-1 overflow-hidden rounded-xl">
      <MapThumb width="100%" height={520} dots={false} s={s} tx={ox} ty={oy} rounded={false} />
      {HOT_SPOTS.filter((h) => !["SMG-2408", "SMG-2619"].includes(h.id)).map((h) => {
        const r = rankOf(h.id, "mid");
        return (
          <Link key={h.id} href={`/audit/${h.id}`}>
            <Marker
              rank={r}
              x={h.x * s + ox}
              y={h.y * s + oy}
              animate={false}
              label={`#${r} ${h.id} · ${h.place}`}
              state={r === 1 ? "selected" : h.stability < 0.8 ? "low" : "default"}
            />
          </Link>
        );
      })}
      <div className="absolute flex w-[203px] flex-col gap-1 rounded-lg bg-surface px-3 py-2.5 shadow-pop" style={{ left: 156, top: 188 }}>
        <span className="text-xs font-medium">{C.heroTip.place}</span>
        <span className="text-[15px] font-medium">{l === "ID" ? "286k m³/thn" : C.heroTip.vol}</span>
        <span className="text-[11px] text-ink-3">{C.heroTip.range[l]}</span>
      </div>
      <span className="absolute bottom-4 left-3.5 rounded-md bg-surface px-2.5 py-1 text-xs text-ink-2">{C.heroCap[l]}</span>
    </div>
  );
}

function SourcesThumb() {
  const s = 0.449;
  const ox = -23.5;
  const oy = -76.4;
  return (
    <div className="relative">
      <MapThumb width={353} height={250} dots={false} raster={null} s={s} tx={ox} ty={oy} />
      {HOT_SPOTS.map((h) => {
        const r = 4 + Math.sqrt(h.volume.mid.v) * 0.5;
        return (
          <span
            key={h.id}
            className="absolute rounded-full bg-ink shadow-[0_0_0_1.5px_#fff]"
            style={{ left: h.x * s + ox - r, top: h.y * s + oy - r, width: 2 * r, height: 2 * r }}
          />
        );
      })}
    </div>
  );
}

function AuditBars() {
  const k = 0.64;
  return (
    <div className="flex flex-col gap-[7px]">
      {ranked("mid").map((h, i) => {
        const v = h.volume.mid;
        return (
          <div key={h.id} className="flex h-3.5 items-center gap-3 text-[11px] text-ink-2">
            <span className="w-2.5">{i + 1}</span>
            <span className="relative h-3.5 flex-1">
              <span className="absolute top-[3px] h-2 bg-pump/85" style={{ left: 0, width: v.v * k }} />
              <span className="absolute top-[6.5px] h-px bg-ink" style={{ left: v.lo * k, width: (v.hi - v.lo) * k }} />
              <span className="absolute top-[3px] h-2 w-px bg-ink" style={{ left: v.lo * k }} />
              <span className="absolute top-[3px] h-2 w-px bg-ink" style={{ left: v.hi * k }} />
            </span>
            <span className="w-7 text-right">{v.v}k</span>
          </div>
        );
      })}
    </div>
  );
}

function EvBar({ pct, tone, text }: { pct: number; tone: string; text: string }) {
  return (
    <span className="flex h-3.5 items-center gap-2.5 text-[11px] text-ink-2">
      <span className="relative h-2 w-[420px] rounded bg-subtle">
        <span className={cn("absolute inset-y-0 left-0 rounded", tone)} style={{ width: `${pct}%` }} />
      </span>
      {text}
    </span>
  );
}

function CrossSection({ l }: { l: L }) {
  const S = C.idea.side;
  const lab = C.idea.labels;
  return (
    <div className="relative mt-7 h-[300px] overflow-hidden rounded-xl bg-surface">
      <svg viewBox="0 0 1200 300" className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
        {/* layers */}
        <path d="M0 92H330C420 118 520 126 606 126C700 126 790 112 870 92H1200V150H0Z" fill="#eeebe3" />
        <rect y="150" width="1200" height="46" fill="#d9cdb4" />
        <rect y="196" width="1200" height="70" fill="#dce5e6" />
        <path d="M0 92H330C420 118 520 126 606 126C700 126 790 112 870 92H1200" fill="none" stroke="#17191c" strokeWidth="1" />
        <path d="M0 70H1200" stroke="#bdb6a8" strokeDasharray="5 4" />
        <path d="M120 214H1080" stroke="#7c8b99" strokeDasharray="4 4" />
        <path d="M120 214C260 216 360 228 450 240C520 248 560 252 600 252C660 252 720 244 780 232C860 220 960 215 1080 214" fill="none" stroke="#2e5f7e" strokeWidth="2" />
        {/* satellite view lines */}
        <path d="M240 8L380 62M300 8L420 62" stroke="#9aa0a6" strokeDasharray="3 3" />
        {/* well */}
        <rect x="594" y="20" width="12" height="232" fill="#0f4c5c" />
        <rect x="574" y="18" width="52" height="4" fill="#0f4c5c" />
        {/* compaction arrows */}
        {[470, 520, 680, 730].map((x) => (
          <g key={x} stroke="#857a65" strokeWidth="1.4" fill="none">
            <path d={`M${x} 164V186`} />
            <path d={`M${x - 5} 180L${x} 186L${x + 5} 180`} />
          </g>
        ))}
      </svg>
      <span className="absolute left-[150px] top-4 text-xs text-ink-3">{S.sat[l]}</span>
      <span className="absolute left-6 top-[53px] text-xs text-ink-3">{S.pre[l]}</span>
      <span className="absolute left-6 top-[167px] text-xs text-ink-3">{S.clay[l]}</span>
      <span className="absolute bottom-3 left-6 text-xs text-ink-3">{S.aq[l]}</span>
      <Lbl n={1} x={626} y={26} text={lab[0][l]} />
      <Lbl n={4} x={690} y={126} text={lab[3][l]} />
      <Lbl n={3} x={800} y={160} text={lab[2][l]} />
      <Lbl n={2} x={760} y={234} text={lab[1][l]} />
    </div>
  );
}

function Lbl({ n, x, y, text }: { n: number; x: number; y: number; text: string }) {
  return (
    <span className="absolute flex items-center gap-2 text-xs font-medium" style={{ left: x, top: y }}>
      <span className="grid size-5 place-items-center rounded-full bg-ink text-[11px] font-normal text-bg">{n}</span>
      {text}
    </span>
  );
}
