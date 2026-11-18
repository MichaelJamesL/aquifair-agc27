# Groundtrace web

The frontend for Groundtrace (AGC 2027). It follows the Groundtrace Figma file (screens 06–09) and the
software section of `docs/groundwater-audit-latex-v2` (user needs U1–U4).

Stack: Next.js (App Router) + Tailwind CSS v4 + TypeScript. Fonts are self-hosted with Fontsource
(Plus Jakarta Sans, IBM Plex Mono, IBM Plex Sans, Newsreader), icons from lucide-react.

## Run

```bash
npm install
npm run dev     # http://localhost:3000
npm run build   # production build
```

## Screens

| Route | Figma screen | Need |
| --- | --- | --- |
| `/` | 06 · Sinking map | U1 |
| `/audit` | 07 · Audit list, and 09 · Cone width (slider state) | U2, U4 |
| `/audit/[id]` | 08 · Hot-spot evidence | U3 |
| `/runs`, `/compare`, `/validation` | placeholders for phase 2 | U6 |

The map, top bar and layers panel live in `src/app/(workspace)/layout.tsx`, so they stay mounted
while the right-hand panel changes. Opening the audit list reframes the map with an animation
instead of reloading it.

## Where things are

```
src/
  app/                  routes (App Router)
    globals.css         Tailwind theme: colours, fonts, radii from the Figma tokens
  components/           TopBar, LayersPanel, ui primitives (Button, Badge, TraceTag)
  map/                  MapView (pan, zoom, markers, tooltips), Legend, raster sampler, vector layers
  panels/               AuditList, ConeWidthSlider, Evidence, HistoryChart
  data/run.ts           demo data for run R-0007 (the numbers in the Figma screens)
  data/layers.ts        the six research-output layers and their legends
  state.tsx             client state: active layer, cone width B, context toggles, hover
public/map/*.png        raster layers exported from the Figma map component
```

## Demo data

`src/data/run.ts` holds the eight hot spots shown in the design, with volumes for the three cone
widths (1.0, 1.5, 2.0 km). The map rasters are the ones drawn in Figma. When the backend exists,
replace `run.ts` with calls to the API in the architecture section of the document
(`GET /audits/{id}`, `GET /audits/{id}/sources`) and swap the PNGs for map tiles.
