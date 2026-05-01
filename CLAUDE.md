# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Flight Prep converts airline OFP (Operational Flight Plan) PDFs in Lido format into structured, cockpit-ready briefings. Upload a PDF, get an 8-section interactive briefing with dark cockpit theme and PDF export.

## Development Commands

```bash
# Start both servers (backend:8000 + frontend:3000)
npm run dev

# Backend only (requires venv)
cd backend && ../backend/venv/bin/uvicorn main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build

# Lint frontend
cd frontend && npm run lint

# Test a parser change against sample PDFs
cd backend && source venv/bin/activate && python3 -c "
from parsers.ofp_parser import parse_ofp
data = parse_ofp('../QR 848.pdf')
print(data.flight_info)
"
```

Backend Python venv is at `backend/venv/`. Always activate it or use the full path when running Python.

## Architecture

Two-server monorepo: Python FastAPI backend for PDF parsing, Next.js 16 frontend for display.

### Data Flow

```
PDF upload → frontend /api/parse (proxy) → backend POST /api/parse
→ pdfplumber extracts text per page → each parser runs regex extraction
→ Pydantic BriefingData model → JSON response → React rendering
```

Stateless — no database. The frontend proxies to the backend at localhost:8000.

### Backend (`backend/`)

- **`models/briefing.py`** — All Pydantic models. This is the JSON contract. Every field the frontend displays must exist here. When adding a field, update both this file and `frontend/src/lib/types.ts`.
- **`parsers/ofp_parser.py`** — Orchestrator. Calls all sub-parsers, builds `BriefingData`, generates operational insights.
- **`parsers/`** — One file per domain: `flight_info.py`, `fuel.py`, `weights.py`, `route.py`, `etops.py`, `arrival.py`, `weather.py`, `notams.py`, `crew_alerts.py`, `takeoff.py`. Each receives the full page list and knows which pages to search.
- **`services/briefing_generator.py`** — Generates plain-text briefing for clipboard copy (server-side).

### Frontend (`frontend/`)

Next.js 16 App Router, TypeScript, Tailwind CSS 4.

- **`src/lib/types.ts`** — TypeScript interfaces mirroring Pydantic models. Must stay in sync with `backend/models/briefing.py`.
- **`src/lib/textBriefing.ts`** — Client-side plain-text briefing generator (mirrors the Python version).
- **`src/app/page.tsx`** — Single-page app: drag-and-drop upload → briefing display. No routing.
- **`src/components/BriefingView.tsx`** — Renders header card + all section components.
- **`src/components/sections/`** — One component per briefing section (FlightOverview, FuelSection, etc.).
- **`src/components/Section.tsx`** — Collapsible section wrapper used by all sections.

### Type Contract

`backend/models/briefing.py` (Pydantic) and `frontend/src/lib/types.ts` (TypeScript) must stay in sync. When adding a field:
1. Add to the Pydantic model
2. Add to the TypeScript interface
3. Update the parser to populate it
4. Update the frontend component to display it
5. Update both `briefing_generator.py` and `textBriefing.ts` if the field should appear in text export

## OFP Parsing

All parsing is regex-based against pdfplumber text output. No LLM involved — Lido OFP format is highly structured.

Key patterns in Lido OFPs:
- Page 1: flight header, fuel summary, weights, alternates
- Pages with `PAGE X/10` + `AWY` + `WPT` headers: route waypoint pages (where FIR boundaries, PLAN REQ/REM, SID/STAR are found)
- `ETOPS INFORMATION`: ETOPS section
- `WX FORECAST` / `LIDO/WEATHER SERVICE`: weather pages
- `LIDO-NOTAM-BULLETIN`: NOTAM pages with `++++` subcategory delimiters
- `QR ALERT/BULLETIN`: crew alerts

Different OFPs may have different page counts and header variations (e.g., `QTR` vs `QR` airline code, ICAO vs IATA city codes). Parsers should handle both.

## Theme

Dark cockpit theme with CSS custom properties in `globals.css`. Colors: green (#00ff88) for normal/accent, amber (#ffaa00) for caution, red (#ff4444) for warning. `@media print` rules switch to light theme. Elements with class `no-print` are hidden in PDF export.

## Next.js Version Notice

This project uses Next.js 16 which has breaking changes from earlier versions. Read `node_modules/next/dist/docs/` before modifying Next.js-specific code (routing, API routes, config).
