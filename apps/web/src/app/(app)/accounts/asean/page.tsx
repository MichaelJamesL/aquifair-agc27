import Link from "next/link";
import { ArrowRight, Check, Info } from "lucide-react";
import { Badge, Button, Card, cn, type BadgeTone } from "@/components/neraca/ui";

type CityRow = {
  name: string;
  sub: string;
  sinking: string;
  declared: string;
  piped: string;
  policy: string;
  status: string;
  tone: BadgeTone;
  note: string;
  link?: boolean;
};

const CITIES: CityRow[] = [
  {
    name: "Central Java",
    sub: "35 regencies and cities",
    sinking: "LiCSAR frames 076D and 127A, processed for Semarang",
    declared: "ESDM open XLSX 2020–23, every regency and city",
    piped: "Piped coverage per district (BPS 2024, Demak 2025); 4 km priority grid for Semarang–Demak",
    policy: "Governor Regulation 7/2025 price table; 2022 conservation-zone map",
    status: "Full",
    tone: "green",
    note: "Accounts for all 35 regencies and cities · Leads and Pipes for Semarang–Demak",
    link: true,
  },
  {
    name: "Jakarta",
    sub: "DKI",
    sinking: "LiCSAR (free)",
    declared: "Source pending",
    piped: "PAM Jaya coverage 66–82%, 100% target by 2030",
    policy:
      "Governor Regulation 93/2021: no groundwater for large buildings in 9 zones and 12 road segments from 1 Aug 2023",
    status: "Waiting for data",
    tone: "amber",
    note: "Account opens when totals are found",
  },
  {
    name: "Ho Chi Minh City",
    sub: "Vietnam",
    sinking: "LiCSAR (free)",
    declared:
      "City totals in the news: 716,581 → 252,528 m³/day by end 2024, target 100,000",
    piped: "SAWACO seals wells as piped supply arrives",
    policy: "Reduction target: 100,000 m³/day",
    status: "Accounts only",
    tone: "blue",
    note: "Totals only, no regency or city split",
  },
  {
    name: "Bangkok",
    sub: "Thailand",
    sinking: "LiCSAR (free)",
    declared: "DGR records, to add",
    piped: "Piped-water expansion where mains reach",
    policy: "Groundwater charge; pumping ban where pipes exist",
    status: "Reference case",
    tone: "green",
    note: "Shown as the success story",
  },
  {
    name: "Manila",
    sub: "Philippines",
    sinking: "LiCSAR (free)",
    declared: "Source pending",
    piped: "Source pending",
    policy: "Source pending",
    status: "Planned",
    tone: "gray",
    note: "Radar ready, totals pending",
  },
];

const HCMC_BARS = [
  { label: "Before", value: "716,581", width: 100, colour: "bg-navy-800" },
  { label: "End 2024", value: "252,528", width: 35.24, colour: "bg-blue-700" },
  { label: "Target", value: "100,000", width: 13.95, colour: "bg-blue-400" },
];

const BANGKOK_POINTS = [
  "A groundwater charge makes wells cost more than pipes.",
  "Piped water reaches the users first, then pumping is banned there.",
  "Sinking fell to about 0–1 cm/yr in most areas.",
  "The gaps were enforcement and household wells, where groundwater stayed cheaper.",
];

export default function AseanComparisonPage() {
  return (
    <div className="mx-auto w-full max-w-[1440px] px-10 py-8">
      <div className="flex items-start justify-between gap-8">
        <div>
          <h1 className="font-display text-[32px] font-semibold leading-10 tracking-[-0.4px] text-ink">
            The same account, other cities
          </h1>
          <p className="mt-2 max-w-[880px] text-[13px] leading-[20px] text-ink-2">
            Sinking is measurable everywhere with free radar. What limits the account is whether
            a city publishes its declared abstraction. Central Java is the full case; other cities
            appear where totals exist.
          </p>
        </div>
        <Link href="/accounts" className="mt-1 shrink-0">
          <Button variant="secondary" size="md" icon={<ArrowRight size={15} />}>
            Open Central Java accounts
          </Button>
        </Link>
      </div>

      <div className="mt-7 overflow-hidden rounded-xl border border-line bg-surface">
        <div className="grid grid-cols-[1fr_1.05fr_1.35fr_1.15fr_1.35fr_1fr] gap-5 border-b border-line bg-bg px-5 py-2.5 font-mono text-[10px] leading-4 tracking-[0.6px] text-ink-3">
          <span>CITY</span>
          <span>SINKING DATA</span>
          <span>DECLARED ABSTRACTION</span>
          <span>PIPED-WATER</span>
          <span>POLICY HOOK</span>
          <span>IN THE APP</span>
        </div>

        {CITIES.map((city) => (
          <div
            key={city.name}
            className="grid grid-cols-[1fr_1.05fr_1.35fr_1.15fr_1.35fr_1fr] gap-5 border-b border-line px-5 py-5 transition-colors last:border-b-0 hover:bg-bg/50"
          >
            <div>
              <p className="text-[15px] font-semibold leading-5 text-ink">{city.name}</p>
              <p className="mt-0.5 text-[12px] leading-4 text-ink-3">{city.sub}</p>
            </div>

            <p className="text-[13px] leading-[19px] text-ink-2">{city.sinking}</p>

            <p
              className={cn(
                "text-[13px] leading-[19px]",
                city.declared === "Source pending" ? "text-ink-3" : "text-ink-2",
              )}
            >
              {city.declared}
            </p>

            <p
              className={cn(
                "text-[13px] leading-[19px]",
                city.piped === "Source pending" ? "text-ink-3" : "text-ink-2",
              )}
            >
              {city.piped}
            </p>

            <p
              className={cn(
                "text-[13px] leading-[19px]",
                city.policy === "Source pending" ? "text-ink-3" : "text-ink-2",
              )}
            >
              {city.policy}
            </p>

            <div>
              <Badge tone={city.tone} dot>
                {city.status}
              </Badge>
              <p className="mt-1.5 text-[12px] leading-[17px] text-ink-2">{city.note}</p>
              {city.link && (
                <Link
                  href="/accounts"
                  className="mt-2 inline-flex items-center gap-1 text-[12px] font-medium text-blue-700 hover:text-primary-hover"
                >
                  Open accounts <ArrowRight size={13} />
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid grid-cols-2 items-stretch gap-5">
        <Card>
          <h2 className="text-[16px] font-semibold leading-5 text-ink">
            Ho Chi Minh City: extraction, m³ per day
          </h2>

          <div className="mt-6 space-y-3">
            {HCMC_BARS.map((bar) => (
              <div
                key={bar.label}
                className="grid grid-cols-[64px_minmax(0,1fr)_74px] items-center gap-3"
              >
                <span className="text-[12px] leading-4 text-ink-2">{bar.label}</span>
                <div className="h-2 overflow-hidden rounded-full bg-subtle">
                  <div
                    className={cn("h-full rounded-full", bar.colour)}
                    style={{ width: `${bar.width}%` }}
                  />
                </div>
                <span className="text-right font-mono text-[11px] leading-4 text-ink-2">
                  {bar.value}
                </span>
              </div>
            ))}
          </div>

          <p className="mt-5 text-[11px] leading-[16px] text-ink-3">
            Source: Tuoi Tre. SAWACO sealed wells as piped supply reached them.
          </p>
        </Card>

        <section className="rounded-xl border border-blue-200 bg-blue-50 p-5">
          <div className="flex items-center gap-2">
            <span className="flex size-5 items-center justify-center rounded bg-blue-700 text-white">
              <Info size={12} />
            </span>
            <h2 className="text-[15px] font-semibold leading-5 text-ink">What Bangkok shows</h2>
          </div>

          <ul className="mt-4 space-y-2.5">
            {BANGKOK_POINTS.map((point) => (
              <li key={point} className="flex gap-2 text-[13px] leading-[19px] text-ink-2">
                <Check size={14} className="mt-[3px] shrink-0 text-blue-700" strokeWidth={2.4} />
                <span>{point}</span>
              </li>
            ))}
          </ul>

          <p className="mt-5 text-[11px] leading-[16px] text-ink-3">
            Sources: Mekong–US Partnership 2020, IGES 2009, World Bank GW-MATE.
          </p>
        </section>
      </div>
    </div>
  );
}
