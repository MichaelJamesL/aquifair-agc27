# agc-26

ASEAN Geospatial Challenge 2027 workspace.

## Apps

- `apps/backend` — NERACA FastAPI backend for `docs/groundwater-accounts-latex`:
  groundwater accounts, inspection leads, pipe priority, source register, and field feedback.
- `apps/web` — the existing Groundtrace Next.js frontend (earlier design; not wired to the new API).

Run the backend:

```bash
cd apps/backend
cp .env.example .env
docker compose up -d db
uv sync --dev
uv run alembic upgrade head
uv run uvicorn neraca.main:app --reload
```

See [`apps/backend/README.md`](apps/backend/README.md) for endpoints, data sources, and architecture.
