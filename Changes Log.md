# Changes Log

Use this file as the shared handoff log between Codex and Claude Code when both are updating this repo.

## Update Rule

- After every meaningful repo change, add a new dated entry.
- Include: `date`, `model`, `summary`, `verification`, and `open items`.
- Keep this file factual. If earlier work was done outside this log, say that clearly instead of guessing.

## Current Working Notes

- Production runs from Render using the same repo root and URL: [https://flight-prep.onrender.com](https://flight-prep.onrender.com)
- Docker must include `Operational Info.txt` or `OPS INFO` will disappear in production.
- Use `scripts/smoke_check.sh` for a quick deploy check.
- Current smoke PDF: `QR 8945.pdf`
- Backend regression tests live in `backend/tests/`

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
