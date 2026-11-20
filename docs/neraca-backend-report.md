# NERACA backend - implementation report

Status: **implemented and verified**, 19 November 2026.

This report describes what was actually built in `apps/backend`, which parts use real data,
which parts are still empty by design, and what the frontend should render and call.

- Backend: FastAPI + Pydantic v2 + PostgreSQL + Alembic.
- Tests: 40 passing, also run against PostgreSQL.
- Data: 35 kabupaten/kota, 2020-2023, 31 sources, 8 validation checks.
- No synthetic data in the API.
- The existing `apps/web` is the earlier Groundtrace design and is **not** wired to this API.

---

## 1. What was really created

### 1.1 Application

| Area | Implemented |
|---|---|
| API | 25 OpenAPI paths under `/api/v1`, plus `/health` |
| Accounts | declared volume, validated estimate, demand estimate, gap range, tax bands, scenario slider, history, billing check |
| Tariffs | 25-row NPA table per wilayah, computed from the Pergub formula |
| Leads | list, card, public district summary, field feedback, hit rate with 90 % interval |
| Pipes | subsidence periods, weighted priority, SPAM test status and wording |
| Provenance | every numeric field has `unit`, `label`, `source_ids`, optional `note` |
| Sources | 31-entry register with links and labels |
| Validation | V1-V8 with pass marks and real status |
| Feedback store | PostgreSQL table `lead_feedback`, one Alembic migration |
| Roles | `public`, `regulator`, `inspector`, `planner` via dropdown header/query, no login |

### 1.2 Seed data

| Data | Count | Source |
|---|---:|---|
| Kabupaten/kota | 35 | BPS codes + Pergub 7/2025 wilayah assignment |
| Declared + NPA value rows | 140 | ESDM Jateng CKAN API, 2020-2023 |
| Sources | 31 | official, measured, tested, weak, missing |
| Validation checks | 8 | report section V1-V8 |
| Tariff rows per wilayah | 25 | Pergub Jateng 7/2025 |
| Boundary features | 35 | geoBoundaries ADM2, filtered to Central Java |
| Subsidence periods | 3 | Sentinel-1 LiCSAR processed results |
| Leads | see `data/leads.json` funnel | four filters on Sentinel-2 2021-26, the digitised 2022 zone map and a kecamatan coverage proxy (update 2026-11-20) |
| Pipe-priority cells | 22 | 4 km blocks with demand range, clay, sinking and piped supply (update 2026-11-20) |

### 1.3 Verified numbers

Kota Semarang, 2023:

```text
declared volume       10,069,814 m3/yr          OFFICIAL
estimated 16 km       27.9 / 43.8 / 54.7 Mm3/yr  TESTED
gap                   -17,169,814 to 44,630,186 m3/yr  CALCULATED
tax per 1 Mm3         8,854 - 13,429 Rp/m3      CALCULATED
declared tax base     112.18 - 135.23 bn Rp/yr  CALCULATED
scenario, 5 Mm3       44.269 - 67.143 bn Rp/yr  CALCULATED
```

NPA check:

```text
K1, 0-50 m3, Wilayah C   37,277 Rp/m3
K2, >2,500 m3, Wilayah C 67,143 Rp/m3
```

Subsidence fast-area medians:

```text
2014-2017  112.777 mm/yr
2018-2022  103.102 mm/yr
2023-2026   88.667 mm/yr
```

---

## 2. Real data flow

```mermaid
flowchart LR
    subgraph Offline["Offline / existing research code"]
        S1["Sentinel-1 LiCSAR<br/>076D + 127A"]
        P1["InSAR / SBAS processing"]
        S1 --> P1
        P1 --> O1["Subsidence rate maps<br/>and period medians"]

        E1["ESDM Jateng CKAN API"]
        E1 --> O2["Declared volume +<br/>NPA value, 2020-2023"]

        G1["Pergub Jateng 7/2025"]
        G1 --> O3["HAB, S, P components"]

        R1["Perda Semarang 2024<br/>PDAM / SPAM releases"]
        R1 --> O4["PDAM sales, SPAM<br/>capacity and uptake"]

        B1["geoBoundaries ADM2"]
        B1 --> O5["35 Central Java<br/>boundaries"]
    end

    O1 --> SEED["apps/backend/data/*.json<br/>+ regions.geojson"]
    O2 --> SEED
    O3 --> SEED
    O4 --> SEED
    O5 --> SEED

    SEED --> API["FastAPI service<br/>apps/backend"]
    API --> FE["Next.js frontend<br/>new NERACA screens"]
```

The backend does **not** process Sentinel-1 at request time. It serves precomputed results.

---

## 3. Backend architecture

```mermaid
flowchart TB
    FE["Frontend<br/>Next.js"]

    subgraph API["API layer - FastAPI"]
        R1["accounts / tariffs"]
        R2["leads / feedback"]
        R3["pipes"]
        R4["sources / validation / regions"]
    end

    subgraph SVC["Service layer - use cases"]
        A["AccountService"]
        L["LeadService"]
        P["PipeService"]
        T["TariffService"]
        S["SourceService"]
        V["ValidationService"]
    end

    subgraph DOM["Domain layer"]
        D1["Account, Range, Number"]
        D2["Lead, Feedback, HitRate"]
        D3["NpaTable formula"]
        D4["Provenance labels"]
    end

    subgraph REPO["Repository layer"]
        J["SeedStore<br/>read-only JSON"]
        F["SqlFeedbackRepository"]
    end

    PG[("PostgreSQL<br/>lead_feedback")]
    JSON[("data/*.json<br/>data/regions.geojson")]

    FE --> API
    API --> SVC
    SVC --> DOM
    SVC --> REPO
    J --> JSON
    F --> PG
```

Dependency direction is `api -> services -> domain`. Routers contain no business logic.
Services do not import FastAPI or SQLAlchemy.

### 3.1 One account request

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant SVC as AccountService
    participant SEED as SeedStore
    participant NPA as NpaTable

    FE->>API: GET /api/v1/accounts/3374?year=2023
    API->>SVC: get_account("3374", 2023)
    SVC->>SEED: declared + estimate + terms
    SEED-->>SVC: real seed records
    SVC->>NPA: K4-K2 and K3-K2 tax bands
    NPA-->>SVC: NPA and tax per m3
    SVC-->>API: Account with labels + source ids
    API-->>FE: JSON
```

### 3.2 One feedback write

```mermaid
sequenceDiagram
    participant FE as Inspector UI
    participant API as FastAPI
    participant SVC as LeadService
    participant DB as PostgreSQL

    FE->>API: POST /leads/{id}/feedback<br/>X-Role: inspector
    API->>SVC: add_feedback(...)
    SVC->>SVC: check role and lead id
    SVC->>DB: INSERT lead_feedback
    DB-->>SVC: row
    SVC-->>API: Feedback
    API-->>FE: 201 Created
```

---

## 4. API contract

Base URL: `http://localhost:8000`
Base path: `/api/v1`

### 4.1 Module A - accounts

| Method | Path | FE use |
|---|---|---|
| GET | `/accounts?year=2023` | list all 35 regions for the map and table |
| GET | `/accounts/{region_id}` | side panel for the selected region |
| GET | `/accounts/{region_id}/history` | declared volume and NPA value, 2020-2023 |
| GET | `/accounts/{region_id}/scenario?undeclared_m3=5000000` | slider result |
| GET | `/accounts/{region_id}/billing-check` | V1 card |
| GET | `/tariffs?wilayah=C` | tariff drawer/table |
| GET | `/accounts/years` | year selector |

Example account payload, abbreviated:

```json
{
  "region": {
    "id": "3374",
    "name": "Kota Semarang",
    "type": "kota",
    "wilayah": "C"
  },
  "year": 2023,
  "declared": {
    "value": 10069814,
    "unit": "m3/yr",
    "label": "OFFICIAL",
    "source_ids": ["ESDM-NPA-2023"]
  },
  "estimated_validated": {
    "low": 27900000,
    "central": 43800000,
    "high": 54700000,
    "unit": "m3/yr",
    "label": "TESTED",
    "source_ids": ["EXP09"]
  },
  "estimate": { "...": "the estimate the gap uses: estimated_validated here, the regency model elsewhere" },
  "estimate_method": "validated_16km_split",
  "gap": {
    "low": -17169814,
    "central": 16230186,
    "high": 44630186,
    "unit": "m3/yr",
    "label": "CALCULATED",
    "source_ids": ["ESDM-NPA-2023", "EXP09", "PERDA-SMG-2024"]
  },
  "tax_per_m3": {
    "low": 8854,
    "high": 13429,
    "unit": "IDR/m3",
    "label": "CALCULATED"
  }
}
```

### 4.2 Module B - leads

| Method | Path | FE use |
|---|---|---|
| GET | `/leads?role=inspector` | inspector lead table/map |
| GET | `/leads/{id}` | lead card |
| GET | `/leads/public/summary` | public district counts |
| POST | `/leads/{id}/feedback` | field visit form |
| GET | `/leads/{id}/feedback` | visit history |
| GET | `/leads/stats/hit-rate` | V6 table with 90 % interval |

State (2026-11-20): `status` is `available`. The collection carries `method` (detector accuracy on a
spatial hold-out, per-year consistency, the Sentinel-1 radar rule, dropped patches), a four-step `funnel` (new building >= 1,000 m2 ->
use class -> critical/damaged zone -> piped coverage < 50 %) and the leads that pass all four.
`GET /leads/{id}/image/{2022|2026}` returns the Sentinel-2 before/after chip (inspector only).
`GET /maps/zones`, `/maps/zone-wells` and `/maps/pdam-coverage` serve the map layers.
If the build ever finds nothing, the API returns `unavailable` with the reason, never an empty map.

### 4.3 Module C - pipes

| Method | Path | FE use |
|---|---|---|
| GET | `/pipes/periods` | period selector and subsidence legend |
| GET | `/pipes/priority?w_demand=&w_damage=&w_supply=` | weighted priority map |
| GET | `/pipes/spam-test` | SPAM result card |

Current SPAM state:

```json
{
  "name": "SPAM Semarang Barat",
  "status": "not_run",
  "design_capacity_lps": 1000,
  "uptake_lps_2024_01": 605,
  "connections_target": 70000,
  "connections_actual_2024_09": 47261,
  "commercial_operation_date": "2021-05-22",
  "districts": ["Semarang Barat", "Ngaliyan", "Tugu"],
  "outcome_wording": "The SPAM Semarang Barat before/after test has not been run. The app shows the design and the data on disk, but makes no claim."
}
```

### 4.4 Shared

| Method | Path | FE use |
|---|---|---|
| GET | `/health` | deployment check |
| GET | `/meta/config` | label meanings, roles, units |
| GET | `/regions` | region selector |
| GET | `/regions/geojson` | choropleth source |
| GET | `/sources` | source drawer/list |
| GET | `/sources/{id}` | one citation |
| GET | `/validation` | validation table |
| GET | `/validation/{code}` | one check |

---

## 5. Frontend components

### 5.1 Library choice

Use **MapLibre GL JS** for the maps. The current `apps/web/src/map/MapView.tsx` is a custom
SVG/PNG viewer built for the earlier design; it is not geographic and should not be reused for
NERACA.

Recommended:

| Need | Library |
|---|---|
| maps | `maplibre-gl` or `react-map-gl` |
| data fetching | `swr` or `@tanstack/react-query` |
| range bars and hit-rate charts | `recharts` or `visx` |
| sliders | existing Tailwind/Radix components or `shadcn/ui` |
| state | existing `state.tsx` or `zustand` |
| GeoJSON helpers | `@turf/turf` if point-in-polygon joins are needed |

### 5.2 Map layer decision

| Layer | Geometry | MapLibre layer | Endpoint | Note |
|---|---|---|---|---|
| Region choropleth | Polygon | `fill` + `line` | `/regions/geojson` + `/accounts` | Accounts map. This is a choropleth, not a heatmap. |
| Lead points | Point | `circle` | `/leads` | Inspector only. Empty until data exists. |
| Lead density | Point | `heatmap` | `/leads` | Optional; only after leads exist. |
| Conservation zone | Polygon | `fill` + `line` | not available | Missing. Do not fabricate. |
| PDAM coverage | Polygon/point | `fill` or `circle` | not available | Missing. Proxy must be labelled. |
| Subsidence | Raster | `raster` | static tiles/COG | Use precomputed raster, not heatmap. |
| Pipe priority | Polygon/point | `fill` or `heatmap` | `/pipes/priority` | Empty until cells exist. |
| SPAM service area | Polygon | `fill-outline` | not available | Missing. |

Rule: **heatmap is for point density**, **choropleth is for polygons**, **raster is for continuous
pixel values**. Do not use a heatmap for the 35 regency polygons.

### 5.3 Shared components

| Component | Purpose | Data |
|---|---|---|
| `ProvenanceBadge` | coloured badge for `OFFICIAL`, `MEASURED`, `TESTED`, `CALCULATED`, `WEAK`, `SCENARIO`, `MISSING` | `label` on every number |
| `NumberWithSource` | value + badge + click target | `value`, `unit`, `source_ids` |
| `SourceDrawer` | side panel with publisher, URL, note | `/sources/{id}` |
| `RangeBar` | low-central-high visual for a `Range` | `low`, `central`, `high` |
| `MissingDataBanner` | explains hidden/missing layers | `MISSING` or `unavailable` reason |
| `RoleSwitcher` | dropdown that sets the role | `X-Role` header or `?role=` |
| `ValidationTable` | V1-V8 status and pass marks | `/validation` |
| `YearSelector` | 2020-2023 | `/accounts/years` |

Label colours suggestion:

| Label | Colour |
|---|---|
| `OFFICIAL` | green |
| `MEASURED` | blue |
| `TESTED` | teal |
| `CALCULATED` | slate |
| `WEAK` | amber |
| `SCENARIO` | purple |
| `MISSING` | red / hidden |

### 5.4 Screen A - Accounts

```mermaid
flowchart LR
    A["Accounts screen"] --> B["RegionChoropleth<br/>MapLibre fill layer"]
    A --> C["AccountPanel<br/>declared, estimate, gap"]
    A --> D["ScenarioSlider<br/>undeclared m3"]
    A --> E["TariffTable<br/>Pergub 7/2025"]
    A --> F["BillingCheckCard<br/>V1"]
    B --> G["GET /accounts?year="]
    C --> H["GET /accounts/{id}"]
    D --> I["GET /accounts/{id}/scenario"]
    E --> J["GET /tariffs?wilayah="]
    F --> K["GET /accounts/{id}/billing-check"]
```

Components:

| Component | Behaviour |
|---|---|
| `RegionChoropleth` | join `region_id` from `regions.geojson` to `accounts`; colour by declared volume or declared tax base; click opens `AccountPanel` |
| `AccountPanel` | shows declared, validated estimate, demand estimate, gap range, tax per 1 Mm3, declared tax base; each value uses `NumberWithSource` |
| `ScenarioSlider` | 0 to 50,000,000 m3/yr, debounced; calls scenario endpoint; shows `SCENARIO` badge because the user sets it |
| `TariffTable` | 25 rows; grouped by K1-K5; show NPA and 20 % tax |
| `BillingCheckCard` | V1 per year: realised tax (Perda 2/2024, Kepgub 211/2025) / declared volume vs the HDA band of the regime in force; `planned` where no realised figure exists |
| `HistoryChart` | 2020-2023 declared volume and NPA value |

Important: the panel must show the gap as a **range**, including negative lower bound. Do not
render a single "lost revenue" number.

### 5.5 Screen B - Leads

```mermaid
flowchart LR
    B["Leads screen"] --> M["LeadMap<br/>circle layer"]
    B --> C["LeadCard<br/>footprint, zone, PDAM"]
    B --> F["FeedbackForm<br/>registered / unregistered / none / PDAM"]
    B --> P["DistrictCounts<br/>public view"]
    B --> H["HitRateTable<br/>90 % interval"]
    M --> E1["GET /leads?role=inspector"]
    C --> E1
    F --> E2["POST /leads/{id}/feedback"]
    P --> E3["GET /leads/public/summary"]
    H --> E4["GET /leads/stats/hit-rate"]
```

Components:

| Component | Behaviour |
|---|---|
| `LeadMap` | point/circle layer for leads; optional `heatmap` for density; zone and PDAM layers are missing and must show `MissingDataBanner` |
| `LeadCard` | satellite image, footprint, zone, PDAM status; inspector only |
| `FeedbackForm` | outcome select (`registered_well`, `unregistered_well`, `no_well`, `pdam_customer`), note, inspector name, visit date; role must be `inspector` |
| `DistrictCounts` | public view; counts only, no coordinates |
| `HitRateTable` | visits, unregistered count, rate, 90 % Wilson interval |

Current UI state: show an empty state with the backend `reason`, not a map with zero leads that
looks like a finding.

### 5.6 Screen C - Pipes

```mermaid
flowchart LR
    C["Pipes screen"] --> S["SubsidenceRaster<br/>MapLibre raster"]
    C --> P["PriorityLayer<br/>fill or heatmap"]
    C --> W["WeightPanel<br/>demand, damage, supply"]
    C --> R["SpamTestCard<br/>V7/V8"]
    C --> T["PeriodSelector"]
    S --> E1["static tiles / COG"]
    P --> E2["GET /pipes/priority"]
    W --> E2
    R --> E3["GET /pipes/spam-test"]
    T --> E4["GET /pipes/periods"]
```

Components:

| Component | Behaviour |
|---|---|
| `SubsidenceRaster` | `raster` layer with the existing colour ramp; periods 2014-17, 2018-22, 2023-26 |
| `PriorityLayer` | `fill` for grid polygons or `heatmap` for points; show the weights used |
| `WeightPanel` | three sliders; sum must be > 0; calls priority endpoint; `SCENARIO` badge because the ranking failed validation |
| `SpamTestCard` | capacity, uptake, connections, status, outcome wording; show `not_run` as no claim |
| `PeriodSelector` | switches the subsidence raster and legend |

State (2026-11-20): priority ranks the 22 real 4 km blocks; damage = clay thickness, supply = piped
water already allocated (SPAM Semarang Barat). The ranking stays `SCENARIO` because V7 failed.

### 5.7 Public vs inspector

| View | Role | What it sees |
|---|---|---|
| Public | `public` | district counts, region accounts, validation, source register |
| Regulator | `regulator` | accounts, tariffs, validation, source register |
| Inspector | `inspector` | lead list/cards, feedback form, hit rate |
| Planner | `planner` | accounts, pipe priority, subsidence, SPAM status |

The role is sent as `X-Role` or `?role=`. It is a UI gate, not authentication. Do not treat it as
security.

---

## 6. What is missing, and what the UI must do

| Missing | Effect | UI behaviour |
|---|---|---|
| ~~2022 CAT conservation zone map~~ | digitised 2026-11-20 from the official vector PDF | zones + Sumur Bor layers |
| PDAM coverage per kelurahan | filter 4 uses kecamatan coverage (BPS 2024, Demak 2025), for hotels, malls and hospitals only; factories skip it (PDAM sold industry 0.22 Mm3 in 2022, Perda Kota Semarang 4/2024 table 2-5) | proxy label on hotel/mall/hospital leads; "not checked" on factories |
| SPAM service-area map | no precise served area | three named kecamatan; label |
| ~~Realised PAT revenue~~ | Kota Semarang 2022-2024 found; other regions still missing | V1 done for 3374, `planned` elsewhere |
| ~~Pipe-priority grid~~ | 22 blocks built 2026-11-20 | ranked, `SCENARIO` |
| ~~SPAM before/after test~~ | V7 and V8 run 2026-11-20, both fail | C2 `inconclusive`, no claim |
| Kendal and Kab. Semarang piped coverage | hotels, malls and hospitals there cannot pass filter 4 | counted in the funnel, not listed |
| Use class of most new roofs | OSM has no tag; Overture places (2026-11-18) fill a few (`WEAK`) | roofs with no class in either, inside a critical/damaged zone, are listed as `unknown` for a site check, not counted as leads |
| Lead checks V4, V5 | run 2026-11-20 (pre-registered): V4 ratio 1.38 below the 1.5x bar (p = 0.0001); V5 25 % vs 14 %, p = 0.15; both fail | numbers shown on the validation page, no claim |
| ~~Estimates for other 34 regions~~ | regency model added 2026-11-20 (BPS population and water source, OSM industrial land), `CALCULATED`, not validated | `estimate_method: regency_model`; UI marks it "model" |

The backend returns this information explicitly. The frontend should not fill gaps with zero,
interpolation, or a fabricated polygon.

---

## 7. Run and verify

```bash
cd apps/backend
cp .env.example .env
docker compose up -d db

uv sync --dev
uv run alembic upgrade head
uv run uvicorn neraca.main:app --reload
```

- API docs: <http://localhost:8000/docs>
- Postgres in compose: `localhost:55432`
- Health: `GET /health`

Checks:

```bash
uv run pytest -q          # 40 passed
uv run ruff check .       # clean
uv run mypy src           # clean
```

PostgreSQL test run:

```bash
$env:NERACA_TEST_DATABASE_URL="postgresql+psycopg://neraca:neraca@localhost:55432/neraca_test"
uv run pytest -q
```

---

## 8. Commits

```text
8500737 docs(backend): document backend setup and API
68dbaf4 test(backend): add unit, API and seed-integrity tests
42c4529 feat(pipes): add pipe priority and SPAM test API
9a4f1a8 feat(leads): add inspection leads and field feedback API
83aeec3 feat(accounts): add groundwater accounts and tariffs API
7bfeec0 feat(backend): add backend scaffold and real seed data
e9d3f6b docs(groundwater-accounts): add NERACA groundwater accounts report
```

---

## 9. Honest limits

- The backend is not a satellite processor. It serves precomputed results.
- The only validated volume estimate is the Kota Semarang 16 km split (applied to 2020-2023; the city
  total it splits is from 2000-2010 studies). The other 34 regions use the regency model: households
  = population x 80-150 L/day x share on wells (BPS drinking-water source, bottled water as the
  range); business = OSM industrial land x Kota Semarang's 2003-06 registered rate, never below
  declared use. Its gap is business minus declared, so household wells cancel. It is not validated;
  on Kota Semarang it gives 24.6-102.7 Mm3 against the validated 27.9-54.7, and moving pumping
  models between places has been off by 5-27x elsewhere (file 08). Industry that uses rivers, the
  sea or PDAM (Cilacap's refinery, for one) makes the gap too high; patchy OSM mapping makes it too
  low. 2022 has no BPS water-source table, so its share spans 2021 and 2023.
- B and C now carry real data (2026-11-20), with two proxies: piped coverage is per kecamatan, not
  kelurahan, and the SPAM served area is three whole kecamatan. Lead use classes come from OSM tags;
  where only an industrial land-use area is tagged, the class is labelled `WEAK`.
- The 20 % tax rate is seeded from Perda 10/2023 plus secondary sources; the Perda clause itself
  was not read.
- The NPA table is computed from the Pergub formula, not transcribed cell by cell. The printed
  K1 0-50 and K2 >2,500 values match.
- The role dropdown is not authentication.
