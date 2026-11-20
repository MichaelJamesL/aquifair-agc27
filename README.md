# agc-26

ASEAN Geospatial Challenge 2027 workspace.

## Apps

- `apps/backend` - NERACA FastAPI backend for `docs/groundwater-accounts-latex`:
  groundwater accounts, inspection leads, pipe priority, source register, and field feedback.
- `apps/web` - NERACA PC frontend (Next.js 16, Tailwind CSS v4, MapLibre GL) implementing the
  `Ganesha Makara_Design` screens against the backend.

### Run the backend

```bash
cd apps/backend
cp .env.example .env
docker compose up -d db
uv sync --dev
uv run alembic upgrade head
uv run uvicorn neraca.main:app --reload
```

### Run the frontend

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>. Set `NEXT_PUBLIC_API_URL` if the backend is not on
`http://localhost:8000/api/v1`.

## Docs

- [`apps/backend/README.md`](apps/backend/README.md) - API, data sources, architecture.
- [`apps/web/README.md`](apps/web/README.md) - routes, components, map layers.
- [`docs/neraca-backend-report.md`](docs/neraca-backend-report.md) - implementation report and
  frontend integration guide.
