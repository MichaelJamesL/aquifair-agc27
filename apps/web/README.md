# NERACA web

PC-only Next.js frontend for **NERACA: Groundwater Accounts**. It implements the Figma
`Ganesha Makara_Design` screens with real backend data from `apps/backend`.

## Run

Start the backend first (see `../backend/README.md`), then:

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>.

The API base URL is read from `NEXT_PUBLIC_API_URL` and defaults to
`http://localhost:8000/api/v1`. If you run the backend on another port, update `.env.local`.

## Routes

| Route | Screen |
|---|---|
| `/` | public landing |
| `/sign-in` | role picker (no login) |
| `/accounts` | Accounts · Jawa Tengah (A1) |
| `/accounts/[id]` | Account detail (A2) |
| `/accounts/asean` | ASEAN comparison (A3) |
| `/leads` | Inspection leads (B1) |
| `/leads/[id]` | Lead detail (B2) |
| `/leads/validation` | Hit rate and validation (B4) |
| `/pipes` | Pipe priority (C1) |
| `/pipes/spam` | SPAM Semarang Barat test (C2) |
| `/methods` | Methods and evidence (M) |

Older Groundtrace routes under `(workspace)` and `(other)` remain in the repository but are not
linked from the NERACA shell.

## Backend integration

- `src/lib/api.ts` contains typed fetchers for every endpoint used.
- `src/lib/use-api.ts` is the small fetch hook used by client screens.
- The role dropdown sends `X-Role: public|regulator|inspector|planner`.
- Every numeric value displays its provenance label through `LabelBadge`.
- Missing data is shown as `MISSING` / `not estimated` or an explicit empty state; it is never
  rendered as zero or a fabricated value.

## Design

- Tailwind CSS v4 tokens live in `src/app/globals.css`.
- Fonts: Plus Jakarta Sans, IBM Plex Mono, Manrope, Newsreader.
- Map component: MapLibre GL JS with a solid sea background and the backend
  `regions.geojson` source. Accounts are a polygon choropleth; leads use a circle layer when real
  leads exist; pipes use a raster/heatmap layer once real cells exist.
- Shared components: `src/components/neraca/ui.tsx`, `top-bar.tsx`, `region-map.tsx`.

## Checks

```bash
npm run build
```
