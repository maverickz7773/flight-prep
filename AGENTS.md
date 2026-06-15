# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What This Is

Flight Prep converts airline OFP (Operational Flight Plan) PDFs in Lido format into structured, cockpit-ready briefings. Upload a PDF, get an 8-section interactive briefing with dark cockpit theme and PDF export. Built for a B777 pilot at Qatar Airways.

## Deployment

- **Live URL**: https://flight-prep.onrender.com
- **GitHub**: git@github.com:maverickz7773/flight-prep.git
- **Hosting**: Render.com free tier, Docker-based, auto-deploys on `git push origin main`
- **Update flow**: make changes → commit → `git push` → Render rebuilds (~3-5 min)
- **Architecture**: Single server. Frontend is statically exported and served by FastAPI. No proxy, no CORS issues.

### Synology Deployment

- **Primary private host**: Synology DS224+ via Container Manager + Tailscale
- **Current Synology URL**: `http://100.83.254.51:8000`
- **Container image**: `ghcr.io/maverickz7773/flight-prep:<version>`
- **Current project path on NAS**: `/volume1/docker/flight-prep`
- **Compose file in repo root**: `compose.yaml`
- **Preferred release flow**:
  1. Make code/content changes on the Mac repo
  2. Ensure `.synology-release.env` exists (copy from `.synology-release.env.example`)
  3. Run `./scripts/release_all.sh vX.Y.Z`
- **What `release_all.sh` does**:
  1. runs local verification
  2. updates `frontend/src/lib/version.ts`
  3. updates repo-root `compose.yaml`
  4. builds and pushes the `linux/amd64` Synology image to GHCR
  5. commits and pushes `main` so Render auto-deploys
  6. uploads `compose.yaml` to Synology `/volume1/docker/flight-prep`
  7. recreates only the Synology `flight-prep` app over SSH/Tailscale
  8. verifies Synology health and frontend version
- **Dry run**: `./scripts/release_all.sh --dry-run vX.Y.Z`
- **Operator note**: see `docs/synology-release.md`
- **Note**: Text-only changes in `Operational Info.txt`, `Enroute Info.txt`, and `NATS Procedure.txt` still require a new Docker image and Synology restart, because those files are baked into the image.

## Development Commands

```bash
# Run locally (recommended): build frontend, copy to backend, start backend on port 8000
cd frontend && npm run build && cd .. && cp -r frontend/out frontend_build
cd backend && ../backend/venv/bin/uvicorn main:app --reload --port 8000
# Then open http://localhost:8000

# Note: `npm run dev` starts frontend:3000 + backend:8000 separately, but the
# frontend uses relative `/api/parse` URLs so PDF parsing won't work from port 3000.
# Always use the single-server approach above for local development.

# Frontend only (for UI-only changes, no API)
cd frontend && npm run dev

# Build frontend static export (outputs to frontend/out/)
cd frontend && npm run build

# Lint frontend
cd frontend && npm run lint

# Docker build and run (matches production)
docker build -t flight-prep . && docker run -p 8000:8000 flight-prep

# Test a parser change against sample PDFs
cd backend && source venv/bin/activate && python3 -c "
from parsers.ofp_parser import parse_ofp
data = parse_ofp('../QR 848.pdf')
print(data.flight_info)
"
```

Backend Python venv is at `backend/venv/`. Always activate it or use the full path when running Python.

## Architecture

Single-server monorepo: Python FastAPI backend parses PDFs and serves the statically-exported Next.js frontend.

### Data Flow

```
PDF upload → POST /api/parse (same origin, no proxy)
→ pdfplumber extracts text per page → each parser runs regex extraction
→ Pydantic BriefingData model → JSON response → React rendering
```

Stateless — no database. localStorage saves last briefing client-side.

### Backend (`backend/`)

- **`main.py`** — FastAPI app. Mounts API routes then serves static frontend from `../frontend_build/`.
- **`models/briefing.py`** — All Pydantic models. This is the JSON contract. Every field the frontend displays must exist here. When adding a field, update both this file and `frontend/src/lib/types.ts`.
- **`parsers/ofp_parser.py`** — Orchestrator. Calls all sub-parsers, builds `BriefingData`, generates operational insights.
- **`parsers/`** — One file per domain: `flight_info.py`, `fuel.py`, `weights.py`, `route.py`, `etops.py`, `arrival.py`, `weather.py`, `notams.py`, `crew_alerts.py`, `takeoff.py`. Each receives the full page list and knows which pages to search. `route.py` also parses enroute wind/shear pages for coordinates and shear rates at cruise FL.
- **`services/briefing_generator.py`** — Generates plain-text briefing for clipboard copy (server-side).

### Frontend (`frontend/`)

Next.js 16 App Router with `output: "export"` (static HTML/JS/CSS). TypeScript, Tailwind CSS 4.

- **`src/lib/types.ts`** — TypeScript interfaces mirroring Pydantic models. Must stay in sync with `backend/models/briefing.py`.
- **`src/lib/textBriefing.ts`** — Client-side plain-text briefing generator (mirrors the Python version).
- **`src/app/page.tsx`** — Single-page app: drag-and-drop upload → briefing display. Includes localStorage save/load.
- **`src/components/BriefingView.tsx`** — Renders header card + all section components. Responsive padding.
- **`src/components/NavSidebar.tsx`** — Desktop sidebar (xl+) and mobile bottom nav (below xl). Both powered by IntersectionObserver.
- **`src/components/sections/`** — One component per briefing section (FlightOverview, FuelSection, etc.). RouteSection displays waypoint table with columns: WPT, FL, ETA, GW (gross weight = ZFW + fuel remaining), SR (shear rate at cruise FL, amber if >5), NOTE.
- **`src/components/Section.tsx`** — Collapsible section wrapper used by all sections.

### Type Contract

`backend/models/briefing.py` (Pydantic) and `frontend/src/lib/types.ts` (TypeScript) must stay in sync. When adding a field:
1. Add to the Pydantic model
2. Add to the TypeScript interface
3. Update the parser to populate it
4. Update the frontend component to display it
5. Update both `briefing_generator.py` and `textBriefing.ts` if the field should appear in text export

### Build & Deploy Files

- **`Dockerfile`** — Multi-stage: Node builds frontend, Python runs everything. WORKDIR is `/app/backend`.
- **`render.yaml`** — Render.com blueprint (Docker, free tier, port 8000).
- **`.dockerignore`** — Excludes node_modules, venv, .next, .git, PDFs.

## OFP Parsing

All parsing is regex-based against pdfplumber text output. No LLM involved — Lido OFP format is highly structured.

Key patterns in Lido OFPs:
- Page 1: flight header, fuel summary, weights, alternates
- Pages with `PAGE X/10` + `AWY` + `WPT` headers: route waypoint pages (where FIR boundaries, PLAN REQ/REM, SID/STAR are found)
- Pages with `LAT/LONG` + `WAYPT` + `ITT` + `WIND DIRCTN SPEED/SHEAR RATE` headers: enroute wind/shear pages (coordinates, shear rates per waypoint at multiple flight levels). The dashed FL in the header row (e.g., `-320-`) indicates the aircraft's current cruise level. Wind/shear entries have format `DDDSS/R` (direction, speed, shear rate).
- `ETOPS INFORMATION`: ETOPS section
- `WX FORECAST` / `LIDO/WEATHER SERVICE`: weather pages
- `LIDO-NOTAM-BULLETIN`: NOTAM pages with `++++` subcategory delimiters
- `QR ALERT/BULLETIN`: crew alerts

Different OFPs may have different page counts and header variations (e.g., `QTR` vs `QR` airline code, ICAO vs IATA city codes). Parsers should handle both.

## Mobile & Responsive

- Grids use `grid-cols-1 sm:grid-cols-2` pattern (stack on mobile, side-by-side on desktop)
- Desktop: fixed left sidebar nav (`hidden xl:flex`)
- Mobile: sticky top tab bar with horizontally scrollable section pills (`xl:hidden`)
- Top bar wraps on small screens (`flex-wrap`)
- Container padding: `p-2 sm:p-4`

## Update Checklist

Use this checklist for both Codex and Claude Code so changes stay compatible in the same folder.

1. Make the code change.
2. If backend data contracts changed, update both `backend/models/briefing.py` and `frontend/src/lib/types.ts`.
3. Update `Changes Log.md` with `date`, `model`, `summary`, `verification`, and `open items`.
4. Run the checks that match the change:
   - Frontend/UI: `cd frontend && npm run lint && npm run build`
   - Backend parser changes: `cd backend && venv/bin/python -m unittest tests.test_airport_notes`
   - Full app / deploy confidence: `./scripts/smoke_check.sh http://127.0.0.1:8000 "QR 8945.pdf"`
   - Render verification after push: `./scripts/smoke_check.sh https://flight-prep.onrender.com "QR 8945.pdf"`
5. If Docker or deployment-related files changed, run a Docker build before pushing:
   - `docker build -t flight-prep .`
6. Push to `main` only after the relevant checks pass.

### Synology Update Checklist

Use this after any user-facing app or text-file change that should go live on Synology.

1. Update the code or the text source file (`Operational Info.txt`, `Enroute Info.txt`, `NATS Procedure.txt`, etc.).
2. If the app version should change, use the next release tag like `v1.1.2`.
3. Update `Changes Log.md`.
4. Ensure `.synology-release.env` exists with the Synology SSH/Tailscale settings.
5. Run:
   - `./scripts/release_all.sh vX.Y.Z`
6. Verify the app on:
   - `http://100.83.254.51:8000`

## Shared Handoff Notes

- `Changes Log.md` is the shared progress file between Codex and Claude Code.
- `Operational Info.txt` is runtime-critical for `OPS INFO`; if it is missing from Docker, production will lose airport notes.
- Current smoke-test PDF is `QR 8945.pdf`.
- Keep local planning/reference files out of deploy commits unless they are intentionally part of the repo.
- `compose.yaml` in the repo root is the tracked Synology project file and should stay aligned with the current GHCR image tag.
- `scripts/release_synology.sh` updates `frontend/src/lib/version.ts`, updates `compose.yaml`, and pushes the `linux/amd64` Synology image to GHCR.
- `scripts/release_all.sh` is the top-level `flight-prep`-only automation wrapper and must never be broadened to touch `ebt-ofp-prep`.

## Theme

Dark cockpit theme with CSS custom properties in `globals.css`. Colors: green (#00ff88) for normal/accent, amber (#ffaa00) for caution, red (#ff4444) for warning. `@media print` rules switch to light theme. Elements with class `no-print` are hidden in PDF export.

## Next.js Version Notice

This project uses Next.js 16 which has breaking changes from earlier versions. Read `node_modules/next/dist/docs/` before modifying Next.js-specific code (routing, API routes, config).
