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

No synthetic data is used in the API. Where a layer has not been obtained, the response says `MISSING` or `unavailable` and gives the reason. Leads and pipe-priority cells are empty until the zone map, PDAM coverage, and grid layers exist.

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
| GET | `/leads` | inspector-only lead list (`X-Role: inspector`) |
| GET | `/leads/public/summary` | district counts only |
| GET | `/leads/{id}` | inspector-only lead card |
| POST | `/leads/{id}/feedback` | record a field visit |
| GET | `/leads/{id}/feedback` | visit history |
| GET | `/leads/stats/hit-rate` | V6, per lead class |
| GET | `/pipes/periods` | subsidence periods |
| GET | `/pipes/priority?w_demand=&w_damage=&w_supply=` | weighted ranking |
| GET | `/pipes/spam-test` | V7/V8 status and wording |
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
