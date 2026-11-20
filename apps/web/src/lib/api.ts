export type ProvenanceLabel =
  | "OFFICIAL"
  | "MEASURED"
  | "TESTED"
  | "CALCULATED"
  | "WEAK"
  | "SCENARIO"
  | "MISSING";

export type NumberValue = {
  value: number | null;
  unit: string;
  label: ProvenanceLabel;
  source_ids: string[];
  note?: string | null;
};

export type RangeValue = {
  low: number | null;
  central: number | null;
  high: number | null;
  unit: string;
  label: ProvenanceLabel;
  source_ids: string[];
  note?: string | null;
};

export type Region = {
  id: string;
  name: string;
  type: "kabupaten" | "kota";
  wilayah: "A" | "B" | "C";
  source_ids: string[];
};

export type Account = {
  region: Region;
  year: number;
  declared: NumberValue;
  estimated_validated: RangeValue;
  estimated_demand: RangeValue | null;
  /** The estimate the gap uses: the validated 16 km split where it exists, else the regency model. */
  estimate: RangeValue;
  estimate_method: "validated_16km_split" | "regency_model" | null;
  gap: RangeValue;
  tax_per_m3: RangeValue;
  declared_tax_base: RangeValue;
  npa_value_total: NumberValue;
  checks: { code: string; status: string; result: string }[];
};

export type AccountYear = {
  year: number;
  declared: NumberValue;
  npa_value_total: NumberValue;
};

export type ScenarioResult = {
  region: Region;
  undeclared_m3: number;
  npa: RangeValue;
  tax: RangeValue;
  tax_rate: number;
  note: string;
};

export type BillingCheck = {
  region: Region;
  year: number;
  check: { code: string; status: string; result: string };
  realised_tax: NumberValue;
  declared_volume: NumberValue;
  implied_tax_per_m3: NumberValue;
  expected_band: RangeValue;
  note: string;
  history: BillingYear[];
};

export type BillingYear = {
  year: number;
  result: string;
  realised_tax: NumberValue;
  declared_volume: NumberValue;
  implied_tax_per_m3: NumberValue;
  expected_band: RangeValue;
  regulation: string;
  outcome: string;
};

export type TariffRow = {
  group: number;
  group_name: string;
  tier_key: string;
  tier_label: string;
  npa_idr: NumberValue;
  tax_idr: NumberValue;
};

export type TariffTable = {
  regulation: string;
  in_force: string;
  tax_rate: number;
  wilayah: string;
  quality: string;
  alternative: boolean;
  rows: TariffRow[];
  source_ids: string[];
};

export type Lead = {
  id: string;
  district: string;
  regency: string | null;
  lon: number;
  lat: number;
  footprint_m2: number;
  polygon: number[][];
  built_year: number;
  use_class: string;
  use_class_basis: string | null;
  zone: string | null;
  /** filter number -> passed; null = not applied to this class (filter 4 for factories) */
  filters: Record<string, boolean | null>;
  pdam_status: string;
  pdam_coverage: number | null;
  sinking_mm_yr: number | null;
  source_ids: string[];
  labels: Record<string, ProvenanceLabel>;
};

/** Filters 2-4 a candidate fails; filter 1 holds for every candidate. */
export const failedFilters = (lead: Lead) => ["2", "3", "4"].filter((key) => lead.filters[key] === false);

export type FunnelStep = { step: string; label: string; count: number };

export type LeadCollection = {
  status: "available" | "unavailable";
  reason: string | null;
  funnel: FunnelStep[];
  method: {
    detector?: { holdout: string; accuracy: number; roof_recall: number; non_roof_specificity: number };
    dropped?: Record<string, number>;
    [key: string]: unknown;
  };
  items: Lead[];
};

export type LeadSummary = {
  district: string;
  leads: number;
  by_use_class: Record<string, number>;
  note: string | null;
};

export type LeadSummaryCollection = {
  status: "available" | "unavailable";
  reason: string | null;
  funnel: FunnelStep[];
  items: LeadSummary[];
};

export type HitRate = {
  lead_class: string;
  visits: number;
  unregistered: number;
  unregistered_rate: number | null;
  interval_90_low: number | null;
  interval_90_high: number | null;
  confirmed_water_user: number;
  confirmed_rate: number | null;
  note: string | null;
};

export type SubsidencePeriod = {
  key: string;
  label: string;
  fast_mm_yr: number;
  land_mm_yr: number;
  source_ids: string[];
};

export type PipePriority = {
  cell: {
    id: string;
    lon: number;
    lat: number;
    polygon: number[][];
    demand_m3_yr: number;
    demand_low_m3_yr: number | null;
    demand_high_m3_yr: number | null;
    clay_m: number;
    sinking_mm_yr: number | null;
    supply_m3_yr: number;
    land_share: number | null;
    districts: string[];
    source_ids: string[];
  };
  score: number;
  demand_share: number;
  damage_share: number;
  supply_share: number;
};

export type PipePriorityCollection = {
  status: "available" | "unavailable";
  reason: string | null;
  note: string | null;
  weights: Record<string, number>;
  items: PipePriority[];
};

export type SpamTest = {
  name: string;
  status: string;
  design_capacity_lps: number | null;
  uptake_lps_2024_01: number | null;
  uptake_m3_yr_2024: number | null;
  connections_target: number | null;
  connections_actual_2024_09: number | null;
  commercial_operation_date: string | null;
  districts: string[];
  delta_mm_yr: number | null;
  shift_null_p05: number | null;
  shift_null_p95: number | null;
  p_lower: number | null;
  placebo_year_clean: boolean | null;
  placebo_area_clean: boolean | null;
  placebo_years_delta_mm_yr: number | null;
  placebo_area_delta_mm_yr: number | null;
  served_mean_mm_yr: Record<string, number>;
  control_mean_mm_yr: Record<string, number>;
  served_cells: number | null;
  positive_control_passed: boolean | null;
  positive_control_delta_mm_yr: number | null;
  positive_control_null_p05: number | null;
  positive_control_note: string | null;
  preregistration: string | null;
  run_date: string | null;
  outcome_code: string | null;
  outcome_wording: string;
  source_ids: string[];
};

export type Source = {
  id: string;
  name: string;
  publisher: string;
  url: string | null;
  label: ProvenanceLabel;
  accessed: string | null;
  note: string | null;
};

export type ValidationCheck = {
  code: string;
  name: string;
  module: "A" | "B" | "C";
  pass_mark: string;
  status: string;
  result: string;
  detail: string | null;
  source_ids: string[];
};

export type GeoFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{ type: "Feature"; properties: Record<string, any>; geometry: any }>;
};

export type ZoneWells = { items: { lon: number; lat: number }[] };

export type PdamCoverageRow = {
  regency: string;
  kecamatan: string;
  year: number;
  coverage: number;
  customers: number;
  population: number | null;
  method: string;
  source_ids: string[];
};

export type RegionFeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, unknown> & {
      region_id?: string;
      shapeName?: string;
    };
    geometry: any;
  }>;
};

const configuredBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const API_BASE = configuredBase.replace(/\/$/, "");

async function apiGet<T>(path: string, role?: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: role ? { "X-Role": role } : undefined,
    signal,
    cache: "no-store",
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      if (body.error?.message) message = body.error.message;
    } catch {
      // Keep the HTTP status when the body is not JSON.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  accounts: (year: number, role: string, signal?: AbortSignal) =>
    apiGet<Account[]>(`/accounts?year=${year}`, role, signal),
  account: (regionId: string, role: string, signal?: AbortSignal) =>
    apiGet<Account>(`/accounts/${regionId}`, role, signal),
  accountHistory: (regionId: string, role: string, signal?: AbortSignal) =>
    apiGet<AccountYear[]>(`/accounts/${regionId}/history`, role, signal),
  scenario: (regionId: string, undeclaredM3: number, role: string, signal?: AbortSignal) =>
    apiGet<ScenarioResult>(
      `/accounts/${regionId}/scenario?undeclared_m3=${undeclaredM3}`,
      role,
      signal,
    ),
  billingCheck: (regionId: string, role: string, signal?: AbortSignal) =>
    apiGet<BillingCheck>(`/accounts/${regionId}/billing-check`, role, signal),
  tariffs: (wilayah: string, role: string, signal?: AbortSignal) =>
    apiGet<TariffTable>(`/tariffs?wilayah=${wilayah}`, role, signal),
  regions: (role: string, signal?: AbortSignal) =>
    apiGet<Region[]>("/regions", role, signal),
  regionGeoJson: (role: string, signal?: AbortSignal) =>
    apiGet<RegionFeatureCollection>("/regions/geojson", role, signal),
  sources: (role: string, signal?: AbortSignal) => apiGet<Source[]>("/sources", role, signal),
  validation: (role: string, signal?: AbortSignal) =>
    apiGet<ValidationCheck[]>("/validation", role, signal),
  leads: (role: string, signal?: AbortSignal, stage = "1-4") =>
    apiGet<LeadCollection>(`/leads?stage=${encodeURIComponent(stage)}`, role, signal),
  leadSummary: (signal?: AbortSignal) =>
    apiGet<LeadSummaryCollection>("/leads/public/summary", undefined, signal),
  hitRate: (role: string, signal?: AbortSignal) =>
    apiGet<HitRate[]>("/leads/stats/hit-rate", role, signal),
  pipePeriods: (role: string, signal?: AbortSignal) =>
    apiGet<SubsidencePeriod[]>("/pipes/periods", role, signal),
  pipePriority: (weights: Record<string, number>, role: string, signal?: AbortSignal) => {
    const query = new URLSearchParams({
      w_demand: String(weights.demand),
      w_damage: String(weights.damage),
      w_supply: String(weights.supply),
    });
    return apiGet<PipePriorityCollection>(`/pipes/priority?${query}`, role, signal);
  },
  spamTest: (role: string, signal?: AbortSignal) =>
    apiGet<SpamTest>("/pipes/spam-test", role, signal),
  leadFeedback: (id: string, role: string, signal?: AbortSignal) =>
    apiGet<Feedback[]>(`/leads/${encodeURIComponent(id)}/feedback`, role, signal),
  lead: (id: string, role: string, signal?: AbortSignal) =>
    apiGet<Lead>(`/leads/${encodeURIComponent(id)}`, role, signal),
  zones: (signal?: AbortSignal) => apiGet<GeoFeatureCollection>("/maps/zones", undefined, signal),
  zoneWells: (signal?: AbortSignal) => apiGet<ZoneWells>("/maps/zone-wells", undefined, signal),
  pdamCoverage: (signal?: AbortSignal) =>
    apiGet<{ note: string; items: PdamCoverageRow[]; geojson: GeoFeatureCollection }>("/maps/pdam-coverage", undefined, signal),
};

export type Feedback = {
  id: string;
  lead_id: string;
  inspector: string;
  outcome: "registered_well" | "unregistered_well" | "no_well" | "pdam_customer";
  note: string | null;
  visited_at: string;
  created_at: string;
};

export async function postFeedback(
  leadId: string,
  body: { inspector: string; outcome: Feedback["outcome"]; note: string | null; visited_at: string | null },
): Promise<Feedback> {
  const response = await fetch(`${API_BASE}/leads/${encodeURIComponent(leadId)}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Role": "inspector" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: { message?: string } } | null;
    throw new Error(payload?.error?.message ?? `${response.status} ${response.statusText}`);
  }
  return (await response.json()) as Feedback;
}

export const leadImageUrl = (id: string, year: 2022 | 2026) =>
  `${API_BASE}/leads/${encodeURIComponent(id)}/image/${year}?role=inspector`;
