# NERACA backend

FastAPI service for **NERACA: Groundwater Accounts** (`docs/groundwater-accounts-latex`).

It serves the three modules of the report and owns the one write path:

- **A. Groundwater accounts** - declared vs estimated use per kabupaten/kota, the gap range, the official NPA/tax, and the undeclared-use scenario.
- **B. Inspection leads** - lead list and cards, public district counts, field feedback, and hit rate per lead class.
- **C. Pipes instead of pumps** - subsidence periods, pipe-priority weights, and the SPAM Semarang Barat test status.
- **O5. Source register** - every number carries a label (`OFFICIAL`, `MEASURED`, `TESTED`, `CALCULATED`, `WEAK`, `SCENARIO`, `MISSING`) and source ids.

The heavy geospatial work stays offline. This service reads precomputed results; it does not process Sentinel-1 at request time.

## Real data only

The seed files in `data/` are generated from real public sources:

- **ESDM Jateng** CKAN API: declared abstraction and NPA value for all 35 kabupaten/kota, 2020-2023.
- **Pergub Jateng 7/2025**: HAB and BAT components. The service computes `NPA = HAB x (0.6 S + 0.4 P)` instead of transcribing the printed table.
- **Perda Kota Semarang 2024**: PDAM sales and registered abstraction.
- **Sentinel-1 LiCSAR** processed results: subsidence period medians.
- **SPAM Semarang Barat** official/news sources: capacity, uptake, connections.
- **geoBoundaries ADM2**: the 35 Central Java boundaries.
- **2022 CAT Semarang-Demak zone map** (Dinas ESDM Jateng, Permen ESDM 31/2018): zone polygons and the 467 "Sumur Bor" markers, digitised from the vector PDF (`data/zones.geojson`, `data/zone_wells.json`).
- **Realised groundwater tax** Kota Semarang 2022-2024 (Perda Kota Semarang 2/2024, Kepgub Jateng 100.3.3.1/211/2025) and the pre-2025 HDA tables (Pergub Jateng 19/2017 + 54/2018) for check V1.
- **Piped coverage per kecamatan**: BPS Kota Semarang Dalam Angka 2024, Portal Data Demak 2025 (proxy for lead filter 4).
- **Lead layers**: Sentinel-2 L2A dry-season composites 2021-2026, Microsoft building footprints, IO land cover, OpenStreetMap classes, Overture Maps places (class when OSM has none), GADM kecamatan.
- **Regency model** (estimated use outside Kota Semarang, `CALCULATED`, not validated): BPS Jateng population 2020-2023 and households by drinking-water source (Susenas 2020, 2021, 2023), OpenStreetMap industrial land.

No synthetic data is used in the API. Where a layer has not been obtained, the response says `MISSING` or `unavailable` and gives the reason.

## Stack

- Python 3.12, FastAPI, Pydantic v2, pydantic-settings
- SQLAlchemy 2.0 + PostgreSQL (`psycopg` 3) for the feedback store
- Alembic migrations
- uv, ruff, mypy, pytest

## Run locally

```bash
cd apps/backend
cp .env.example .env
docker compose up -d db

uv sync --dev
uv run alembic upgrade head
uv run uvicorn neraca.main:app --reload
```

The compose file publishes Postgres on **55432** to avoid the common 5432 conflict. Internal containers still use 5432.

Open <http://localhost:8000/docs>.

### Database without Docker

Set `NERACA_DATABASE_URL` to any PostgreSQL instance, then run `uv run alembic upgrade head`.

For a quick local schema without Alembic, set `NERACA_AUTO_CREATE_TABLES=true`. Migrations are still the supported path.

## Tests and checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Tests use an in-memory SQLite database so they do not need Postgres. The application itself always uses Postgres. Set `NERACA_TEST_DATABASE_URL` to run the same tests against Postgres.

## API

Base path: `/api/v1`

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | service and database status |
| GET | `/meta/config` | labels, roles, units |
| GET | `/regions` | 35 kabupaten/kota |
| GET | `/regions/geojson` | filtered ADM2 boundaries |
| GET | `/accounts?year=2023` | module A, all regions |
| GET | `/accounts/{region_id}` | one account |
| GET | `/accounts/{region_id}/history` | declared and NPA value, 2020-2023 |
| GET | `/accounts/{region_id}/scenario?undeclared_m3=5000000` | the user-set slider |
| GET | `/accounts/{region_id}/billing-check` | V1 |
| GET | `/tariffs?wilayah=C` | the 25-row NPA table, computed from the Pergub formula |
| GET | `/leads?stage=1-4` | inspector-only list (`X-Role: inspector`); `stage` = funnel step `1`, `1-2`, `1-3`, `1-4` (leads, default) or `unknown` (site checks) |
| GET | `/leads/public/summary` | district counts only |
| GET | `/leads/{id}` | inspector-only lead card |
| GET | `/leads/{id}/image/{2022\|2026}` | inspector-only Sentinel-2 before/after chip (PNG) |
| POST | `/leads/{id}/feedback` | record a field visit |
| GET | `/leads/{id}/feedback` | visit history |
| GET | `/leads/stats/hit-rate` | V6, per lead class |
| GET | `/pipes/periods` | subsidence periods |
| GET | `/pipes/priority?w_demand=&w_damage=&w_supply=` | weighted ranking |
| GET | `/pipes/spam-test` | V7/V8 status and wording |
| GET | `/maps/zones` | 2022 CAT zone polygons (GeoJSON) |
| GET | `/maps/zone-wells` | the 467 "Sumur Bor" markers of the zone map |
| GET | `/maps/pdam-coverage` | piped coverage per kecamatan, with outlines (filter 4 proxy) |
| GET | `/sources` | O5 source register |
| GET | `/validation` | V1-V8 |

### Roles

There is no login. The UI dropdown sends `X-Role: public|regulator|inspector|planner` (or `?role=`). It only gates views:

- `public` sees district counts, never lead addresses.
- `inspector` sees leads and can post feedback.
- `regulator` and `planner` use the accounts, validation, and pipes views.

This is a demo gate, not security. Do not treat it as authentication.

## Provenance shape

```json
{
  "value": 10069814,
  "unit": "m3/yr",
  "label": "OFFICIAL",
  "source_ids": ["ESDM-NPA-2023"],
  "note": null
}
```

Ranges have `low`, `central`, `high`, `unit`, `label`, and `source_ids`.

## Architecture

```text
src/neraca/
  api/            FastAPI routers, dependencies, error mapping
  schemas/        Pydantic request/response models
  services/       use cases and business rules
  domain/         entities, enums, value objects, NPA formula
  repositories/   seed loader, seed-file models, feedback protocol, SQL implementation
  infrastructure/ database engine, ORM, migrations
data/             curated real-data seed files
scripts/          build_seed.py and raw ESDM API responses
tests/            unit, API, and data-integrity tests
```

Dependency direction: `api -> services -> domain`, with repositories behind protocols. Routers do not contain business logic; services do not import FastAPI or SQLAlchemy.

## Rebuild seed data

```bash
uv run python scripts/build_seed.py
```

The script reads `scripts/raw/esdm_*.json` and `realdata/semarang/admin/idn_adm2.geojson`, then rewrites `data/`. The raw CKAN responses are checked in so the build is reproducible without the network.

The B and C layers have their own offline builders. They read raw downloads under `realdata/` (not in git) and
write the files in `data/` that the API serves:

| Script | Writes | Inputs |
|---|---|---|
| `digitise_zones.py <pdf>` | `zones.geojson`, `zone_wells.json` | ESDM 2022 zone map PDF |
| `build_pdam_coverage.py` | `pdam_coverage.json` | BPS Kota Semarang 2024, Demak CKAN, GADM |
| `build_pipe_cells.py` | `pipe_cells.json` | file 07 demand blocks, clay and Sentinel-1 bundle, GADM |
| `fetch_s2_composites.py <years>` | `realdata/semarang/leads/s2_<year>.npz` | Planetary Computer Sentinel-2 L2A |
| `fetch_s1_composites.py 2022 2026` | `realdata/semarang/leads/s1_<year>.npz` | Planetary Computer Sentinel-1 RTC |
| `fetch_az_v4.py` | `realdata/arizona/v4/` | ADWR Wells 55 + CWS areas, IO land cover |
| `fetch_overture_places.py` | `realdata/semarang/leads/overture/places.json` | Overture Maps places (run with `uv run --no-project --with duckdb`) |
| `build_leads.py` | `leads.json`, `lead_chips/` | S2 and S1 composites, footprints, OSM, Overture places, zones, coverage |
| `build_regency_estimates.py [--fetch]` | `estimates.json`, `account_terms.json` (method `regency_model`) | BPS population and water source, OSM industrial land; see the script docstring |
| `run_checks.py [--only=V4,V5,V7,V8]` | `check_results.json`, `pipes.json` (spam), `validation.json` | see `prereg_v5_v7_v8.md` |
