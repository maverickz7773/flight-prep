# Changes Log

Use this file as the shared handoff log between Codex and Claude Code when both are updating this repo.

## Update Rule

- After every meaningful repo change, add a new dated entry.
- Include: `date`, `model`, `summary`, `verification`, and `open items`.
- Keep this file factual. If earlier work was done outside this log, say that clearly instead of guessing.

## Current Working Notes

- Production runs from Render using the same repo root and URL: [https://flight-prep.onrender.com](https://flight-prep.onrender.com)
- Docker must include `Operational Info.txt`, `Enroute Info.txt`, and `NATS Procedure.txt` or local text-driven notes will disappear in production.
- Use `scripts/smoke_check.sh` for a quick deploy check.
- Current smoke PDF: `QR 8945.pdf`
- Backend regression tests live in `backend/tests/`

## 2026-05-19 — Codex

**Summary**

- Added a new backend NATS loader in `backend/parsers/nats.py`, driven by `NATS Procedure.txt`
- Added top-level `nats_procedure` to the shared backend/frontend data contract
- Triggered NATS only when `route.fir_sequence` contains one of `ENOB`, `BIRD`, `EGGX`, `BGGL`, `CZQX`, or `KZWY`
- Populated `NATS Overview` dynamically from the OFP:
  - `TMI` parsed from the dispatch/NAT track briefing text
  - `NATS Route` derived from the contiguous oceanic route segment
  - entry/exit point, EET, and FIR derived from the first and last trigger-segment waypoints
- Added collapsed NATS UI blocks to:
  - Section 1 `Flight Overview` for `NATS Overview`
  - Section 4 `Takeoff` for `NATS Preflight and Planning`
  - Section 5 `Route` for a parent `NATS` toggle with nested `NATS Enroute` and `NATS Exit`
- Preserved the existing Section 5 FIR-note behavior; NATS is additive and independent
- Added Docker packaging for `NATS Procedure.txt` so the feature will work on Render after push
- Relaxed `backend/tests/test_enroute_info.py` so it verifies correct route/FIR mapping without breaking each time `Enroute Info.txt` grows
- Added `KSEA` timezone coverage so `QR 719.pdf` now shows `STA (UTC-7)` correctly in Section 1
- Verified and refined the NATS exit-point logic so synthetic markers like `ENTRY2` are replaced by the first real named waypoint after the oceanic coordinate chain, e.g. `MEDPA` for `QR 719.pdf`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_nats_procedure tests.test_flight_info_parser tests.test_sid_star_parser tests.test_etops_parser tests.test_airport_notes tests.test_enroute_info` passed
- `cd frontend && npm run lint` passed
- `cd frontend && npm run build` passed
- `./scripts/smoke_check.sh http://127.0.0.1:8000 "QR 8945.pdf"` passed
- `docker build -t flight-prep .` passed
- Refreshed `frontend_build` for the local FastAPI app
- Verified NATS parsing from real OFPs:
  - `QR 707.pdf` → triggered, `trigger_firs = ["EGGX", "CZQX"]`, `TMI = 137`, route `GOMUP ... IRLOK`
  - `QR 719.pdf` → triggered, `trigger_firs = ["BIRD", "BGGL"]`, route `ISVIG ... MEDPA`, `STA UTC = -7`
  - `QR 239.pdf` → no NATS
  - `QR 8452.pdf` → no NATS
  - `QR 701.pdf` → triggered, route `GUNPA ... JANJO`
  - `QR 720.pdf` → triggered, route `BOPUT ... GUNPA`
  - `QR 8075.pdf` → triggered, route `IBERG ... ETIKI`

**Open Items**

- After push, run a Render verification on NAT flights such as `QR 701.pdf`, `QR 707.pdf`, and `QR 719.pdf`
- Continue expanding `NATS Procedure.txt`, `Operational Info.txt`, and `Enroute Info.txt` as route coverage grows

## 2026-05-19 — Codex

**Summary**

- Replaced fixed UTC offset strings in `backend/parsers/flight_info.py` with airport-to-timezone mapping plus date-aware UTC offset calculation using `zoneinfo`
- Added missing airport coverage for examples now verified in the repo, including `KIAD` and `VDTI`, so `STA` shows UTC when those airports appear as arrivals
- Broadened cruise extraction in `backend/parsers/flight_info.py` to read the ATC clearance cruise/step-climb lines directly, instead of depending on an arrival-runway anchor
- Fixed `backend/parsers/weights.py` so `EZFW` is parsed from the actual weights table lines and no longer picks up tankering advisory text
- Extended `backend/tests/test_flight_info_parser.py` with regressions for `QR 707.pdf`, `QR 849.pdf`, and `QR 8974.pdf`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_flight_info_parser tests.test_sid_star_parser tests.test_etops_parser tests.test_airport_notes tests.test_enroute_info` passed
- Verified parser outputs:
  - `QR 849.pdf` → `arrival_utc_offset = +3`, `cruise = ["FL340", "FL360", "FL340", "FL300"]`, `ezfw = 217315`
  - `QR 707.pdf` → `arrival_utc_offset = -4`, `cruise = ["FL320", "FL340", "FL360", "FL380", "FL360", "FL380"]`, `ezfw = 205441`
  - `QR 8974.pdf` → `arrival_utc_offset = +7`, `cruise = ["FL330", "FL350", "FL370", "FL330"]`, `ezfw = 149808`

**Open Items**

- If more airports are seen with missing UTC offsets, add their ICAO-to-timezone mapping in `flight_info.py`
- Frontend label behavior should update automatically from the backend offsets; no frontend code was changed in this pass

## 2026-05-13 — Codex

**Summary**

- Added enroute FIR note support from `Enroute Info.txt` for Section 5 `Route`
- Added cached backend loader in `backend/parsers/enroute_info.py`, keyed by FIR ICAO headers like `[OEJD]`
- Extended `RouteSummary` with `enroute_info`, containing only route FIRs that actually have note coverage in `Enroute Info.txt`
- Updated `frontend/src/components/sections/RouteSection.tsx` so the FIR chain stays compact by default, only FIRs with notes become clickable, and clicking a FIR opens one note panel below the FIR row
- Kept FIRs without notes as plain text, so partial coverage does not clutter the UI
- Updated Docker packaging to copy `Enroute Info.txt` into the production image so Section 5 FIR notes work on Render, not just locally

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_enroute_info tests.test_flight_info_parser tests.test_sid_star_parser tests.test_etops_parser tests.test_airport_notes` passed
- `cd frontend && npm run lint` passed
- `cd frontend && npm run build` passed
- `./scripts/smoke_check.sh http://127.0.0.1:8000 "QR 8945.pdf"` passed
- `docker build -t flight-prep .` passed
- Refreshed `frontend_build` for the local FastAPI app
- Verified route note coverage from real OFPs:
  - `QR 239.pdf` → interactive note candidates: `OBBB`, `OEJD`, `OJAC`, `OSTT`, `LTAA`
  - `QR 719.pdf` → interactive note candidates: `OEJD`, `OJAC`, `OSTT`, `LTAA`
  - `QR 8452.pdf` → interactive note candidates: `OEJD`, `OOMM`, `VABF`, `VRMF`, `YMMM`
  - FIRs without note coverage, such as `LTBB`, `LBSR`, `BIRD`, and `KZSE`, remain plain text only

**Open Items**

- `Enroute Info.txt` is still being built up manually over time; adding a new `[FIR]` block should automatically make that FIR interactive on the next parse
- After push, run a Render smoke check and optionally confirm `QR 8452.pdf` opens `YMMM` correctly in Section 5 on the live site

## 2026-05-13 — Codex (Local data update note)

**Summary**

- User continued expanding `Enroute Info.txt` locally after the Section 5 FIR-note feature was implemented
- Confirmed new/additional FIR coverage now includes `OMAE`, `OOMM`, `VABF`, `VOMF`, `VCCF`, `VRMF`, and a dedicated `[YMMM]` block
- Confirmed `OBBB` block was also updated locally

**Verification**

- Local app is running and healthy at `http://127.0.0.1:8000`
- Searched `Enroute Info.txt` and confirmed `[YMMM]` exists as its own block
- Verified `QR 8452.pdf` includes `MELBOURNE (YMMM)` in `route.fir_sequence`, so it is the correct local test case for the new `YMMM` FIR note

**Open Items**

- These latest `Enroute Info.txt` additions should be pushed together with the Section 5 code changes
- After push, confirm the live Render app shows the same FIR-note coverage as local

## 2026-05-11 — Codex

**Summary**

- Hardened SID/STAR parsing in `backend/parsers/flight_info.py` and `backend/parsers/arrival.py`
- Added shared route-page procedure helpers in `backend/parsers/procedures.py` so SID/STAR extraction no longer depends on procedures ending with a trailing letter
- SID extraction now uses the first valid route page and only scans the lines immediately after the departure runway row, stopping before the first FIR/boundary block
- STAR extraction now scans backward from the arrival runway row across the final route page(s), allowing numeric-ending procedures such as `GLASR3`
- Broadened the route-string STAR fallback to use the same shared procedure-token matcher
- Fixed `cruise_levels` extraction in `backend/parsers/flight_info.py` so Flight Overview now captures both single-level cruise lines like `FL310` and wrapped step-climb sequences that continue onto the next line
- Added regression coverage in `backend/tests/test_sid_star_parser.py`
- Added regression coverage in `backend/tests/test_flight_info_parser.py`

**Verification**

- `venv/bin/python -m unittest tests.test_flight_info_parser tests.test_sid_star_parser tests.test_etops_parser tests.test_airport_notes` passed
- Verified parsed outputs:
  - `QR 719.pdf`: `SID = None`, `STAR = GLASR3`
  - `QR 849.pdf`: `SID = PUGER1E`, `STAR = TOVOX2L`
  - `QR 8240.pdf`: `SID = LNO8E`, `STAR = RIXUV3E`
  - `QR 8945.pdf`: `SID = TOMUD3`, `STAR = LAEEB1P`
- Verified cruise parsing:
  - `QR 8240.pdf`: `CRUISE = [FL310]`
  - `QR 8452.pdf`: `CRUISE = [FL270, FL290, FL310, FL350, FL370, FL390]`
- Confirmed consistency:
  - `flight_info.sid == takeoff.sid`
  - `flight_info.star == arrival.star`

**Open Items**

- Push/deploy this SID/STAR parser hardening if the user wants it on Render
- If future OFPs introduce new procedure naming formats, extend `procedures.py` and add another regression PDF before widening the matcher

## 2026-05-11 — Codex

**Summary**

- Hardened ETOPS sector parsing in `backend/parsers/etops.py` to handle layout variants where the sector exit ICAO appears after an extra continuation line
- Replaced the brittle fixed-line `ENTRY1/EXIT1` parsing with marker-block parsing keyed by sector number
- The parser now tolerates patterns like `EXIT1 ...` followed by an intermediate line such as `2D W00833.4` and then the real ICAO on a later line
- Added regression coverage in `backend/tests/test_etops_parser.py`

**Verification**

- `venv/bin/python -m unittest tests.test_etops_parser tests.test_airport_notes` passed
- `QR 719.pdf` now parses as:
  - `S1 ENTRY = ENBR`
  - `S1 EXIT = BIKF`
  - `S2 ENTRY = BIKF`
  - `S2 EXIT = CYEG`
- `QR 8452.pdf` still parses as:
  - `S1 ENTRY = OOSA`
  - `S1 EXIT = VOCI`
  - `S2 ENTRY = VCBI`
  - `S2 EXIT = YPAD`

**Open Items**

- Push/deploy this ETOPS parser hardening if the user wants the fix on Render
- Consider expanding ETOPS regression coverage with more multi-sector OFPs if more layout variants appear

## 2026-05-10 — Claude Code

**Summary**

- **Section 1 — ETOPS stacked display**: ETOPS data moved out of the 2-column data grid into a dedicated full-width block below the grid (same pattern as crew rest section). Each sector shows ENTRY / EXIT / ALTN rows with EET and gross weight (GW = EZFW + fuel remaining). Multi-sector flights show S1/S2 prefixes. Single-sector shows plain ENTRY/EXIT/ALTN.
- **Section 5 — Remove ETOPS SECTOR block**: The old amber "ETOPS SECTOR" entry/ETP/exit panel in the Route section was removed; all ETOPS detail is now in Section 1.
- **Section 7 — Airport search filter**: Added search input next to "Show LOW relevance". Filters departure, destination, alternates, enroute airports pill list, and enroute FIR blocks simultaneously. Clear (×) button when query is active.
- **Section 7 — NOTAM valid period**: Each NOTAM now shows `valid_from – valid_to` in small muted text below the reference badge. Only displayed when `valid_from` is present.
- **Section 7 — FIR sequence line**: FIR route sequence (e.g. `FIR  JAKARTA (WIIF) → KUALA LUMPUR (WMFC) → ...`) now appears just below the controls row in Section 7, giving FIR context before scanning weather/NOTAM blocks.
- **Backend — ETOPSSector model**: Extended `ETOPSSector` with `entry_eet`, `entry_fuel`, `exit_eet`, `exit_fuel` fields. Parser `_build_sectors()` in `etops.py` updated to extract EET (2nd token on row) and fuel (last float on row) for each entry/exit point.
- Committed as `8811804` and pushed to `main`; Render auto-deploy triggered.

**Verification**

- `QR 849.pdf` — Section 1 shows full-width ETOPS block: `ENTRY VTSP EET 1.30 GW 276.0t`, `EXIT VCRI EET 1.57 GW 272.2t`, `ALTN WIMM`
- Section 5 confirmed: no ETOPS SECTOR block
- Section 7 search: typing an ICAO hides unrelated airports and FIR blocks
- FIR sequence line visible in Section 7 on upload
- `npm run build` passed with no TypeScript errors

**Open Items**

- Smoke test on Render after deploy: verify ETOPS block in Section 1 and FIR line in Section 7 for `QR 849.pdf`

## 2026-05-10 — Codex

**Summary**

- Fixed weather parsing for page-break-contaminated TAF blocks in `QR 8091.pdf`
- Updated `backend/parsers/weather.py` to strip OFP page footer/header lines such as `Page X of Y` and `QTR ... OFP:...` before METAR/TAF extraction
- Updated TAF extraction to prefer the last `FT ... =` block within a sanitized weather block, which handles split forecasts across PDF page breaks
- Committed as `241ca2b` and pushed to `main`; Render auto-deploy triggered

**Verification**

- Re-parsed `QR 8091.pdf` locally
- Confirmed EIDW now returns a clean TAF:
  - `061100 0612/0712 VRB03KT 9999 FEW025 ... PROB30 TEMPO 0711/0712 5000 SHRA SCT015`
- Confirmed the old embedded footer text is gone
- `venv/bin/python -m unittest tests.test_airport_notes` passed

**Open Items**

- If EIDW still shows no underline for `~1100z`, that is expected with the current logic because `~1100z` is before the parsed TAF validity `0612/0712`
- Optional Render smoke check if the user wants to confirm the cleaned EIDW TAF on the live site

## 2026-05-09 — Claude Code

**Summary**

- Added KORD (Chicago O'Hare) personal operational notes to `Operational Info.txt`
- Notes cover: DEP — metering contact, KUSA clearance (30 min prior), ramp/taxi/tower frequencies, Rwy 10L heading freq, enroute sector freqs (Chicago, Cleveland, Boston, Moncton), CPDLC CZQM
- Notes cover: ARR — Chicago Approach 135.02/133.62, ILS Rwy 28C via RZUKO (14 nm), step-down 6000→5000, tower at SEIKA (5 nm), gate metering with QTR 725
- Verified KORD parses correctly via `/api/airport-notes?departure=KORD` on the running local backend
- Committed and pushed to `main`; Render auto-deploy triggered

**Verification**

- `curl http://localhost:8000/api/airport-notes?departure=KORD&arrival=OTHH` returned correct DEP/ARR JSON
- Pushed commit `4c6a307` to `main`

**Open Items**

- Smoke test on Render after deploy: upload a KORD-departure OFP and confirm OPS INFO block appears in Section 4

## 2026-05-08 — Claude Code

**Summary**

- Diagnosed why `KORD` was missing from `backend/data/omc_briefings.json` despite being present in `OM C.pdf`
- Root cause: `HEADER_RE` regex in `backend/scripts/extract_omc.py` matched only exactly 5-part section numbers (`\d+\.\d+\.\d+\.\d+\.\d+`); the current OM C PDF uses variable-length section numbering (4–7+ parts, e.g., `6.3.3.4.3.11`)
- Fixed both occurrences of the pattern to `(?:\d+\.)+\d+` — handles any number of dot-separated parts
- Re-ran `extract_omc.py` against `OM C.pdf` to fully rebuild `backend/data/omc_briefings.json`
- OM C airport coverage grew from **389 → 503 airports**; all previously missed airports now included, including KORD
- Committed and pushed to `main`; Render auto-deploy triggered

**Verification**

- `python3 scripts/extract_omc.py "../OM C.pdf"` reported: `Found 1433 aerodrome headers`, `Extracted 503 aerodromes`
- `omc_briefings.json` confirmed: `KORD` present, name `Chicago - O'Hare International`, category `B`
- Local parse of `QR 8091.pdf` confirmed: `departure_briefing.icao = KORD` (previously `null`)
- Pushed commit `9c979ca` to `main`

**Open Items**

- Smoke check on Render after deploy completes (~3–5 min): verify Section 4 OM C appears for a KORD-departure flight
- The previous Codex open item re KORD is now resolved; no manual JSON editing needed

## 2026-05-08 — Codex

**Summary**

- Rebuilt and ran the app locally on `http://127.0.0.1:8000`
- Rechecked `QR 8091.pdf`
- Confirmed Section 4 has no `OM C` because `KORD` is not present in `backend/data/omc_briefings.json`
- Confirmed Section 6 `OM C` is present because `OTHH` exists in the OM C dataset
- Listed the current OM C airport coverage count: `389` airports

**Verification**

- Local health endpoint returned `{\"status\":\"ok\",\"operational_info_present\":true}`
- Local parse for `QR 8091.pdf` returned:
  - departure `KORD`
  - arrival `OTHH`
  - `departure_briefing = null`
  - `arrival_briefing` present
- Searched `backend/data/omc_briefings.json` and confirmed `KORD` is absent while `OTHH` is present
- No repo code changes were made after this diagnosis

**Open Items**

- If OM C is needed for Section 4 on `QR 8091`, add a real `KORD` briefing entry to `backend/data/omc_briefings.json`
- Do not invent `KORD` OM C content; source text or screenshots are needed first

## 2026-05-07 — Codex

**Summary**

- Diagnosed Render parsing failure for `QR 8091.pdf` as a long-request timeout, not a parser logic failure
- Measured local `/api/parse` at about 5.9 seconds and Render `/api/parse` timing out with `502` after about 110.8 seconds
- Added async parse job endpoints so uploads return quickly and the frontend polls for completion instead of waiting on one long request
- Updated the frontend upload flow to use parse jobs and show clearer status/error messages
- After the Render memory-limit alert, updated page extraction to close each `pdfplumber` page immediately after text extraction
- Reduced in-memory parse job retention from 60 minutes to 10 minutes

**Verification**

- Local `QR 8091.pdf` parse confirmed route `KORD -> OTHH`
- Verified local health endpoint before implementing the fix
- Verified local queued parse flow for `QR 8091.pdf`
- Pending refreshed local tests and Render verification after the memory-focused extractor change

**Open Items**

- Verify the new parse-job flow locally and on Render with `QR 8091.pdf`
- Keep the direct `/api/parse` endpoint for scripts and smoke checks

## 2026-05-06 — Codex

**Summary**

- Updated `AGENTS.md` to match the current app behavior and team workflow
- Corrected the mobile navigation note from bottom nav to sticky top tab bar
- Added a shared update checklist for Codex and Claude Code
- Added explicit handoff notes about `Changes Log.md`, `Operational Info.txt`, and smoke-test usage

**Verification**

- Reviewed `AGENTS.md` against the current deployed/local app behavior
- Confirmed the checklist matches the working commands already validated today

**Open Items**

- Keep `AGENTS.md` and `Changes Log.md` in sync whenever workflow or architecture changes
- Continue adding a new log entry after each meaningful repo change

## 2026-05-06 — Codex

**Summary**

- Added airport-specific `OPS INFO` support from `Operational Info.txt`
- Wired `airport_notes` through backend models, OFP parsing, frontend types, and Sections 4 and 6
- Added `/api/airport-notes` fallback so older saved briefings can hydrate missing notes
- Updated Section 4 and Section 6 layout:
  - compact weather strip above RWY/SID or RWY/STAR
  - `OPS INFO` always visible
  - `OM C` moved behind a toggle for cleaner display
- Added TAF timing highlight logic in Sections 4, 6, and 7
- Moved mobile nav to a sticky top tab bar while keeping the desktop sidebar
- Fixed Render packaging by copying `Operational Info.txt` into the Docker image
- Added a backend startup warning plus health flag for missing operational info
- Added `scripts/smoke_check.sh`
- Added backend regression tests for `QR 8945.pdf` and `QR 8240.pdf`

**Verification**

- `npm run lint`
- `npm run build`
- Local API parsing verified with `QR 8945.pdf`, `QR 8944.pdf`, and `QR 8240.pdf`
- Docker image build verified locally
- Live Render parse verified for `QR 8945.pdf`

**Open Items**

- Enroute airport runway reference data is still pending a local dataset
- Continue updating this file after each change from either Codex or Claude Code

## Historical Note

- The user noted that earlier development on this project was also done in Claude Code before this log was created.
- Exact earlier Claude Code changes were not reconstructed retroactively here.
