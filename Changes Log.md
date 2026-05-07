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

## 2026-05-07 — Codex

**Summary**

- Diagnosed Render parsing failure for `QR 8091.pdf` as a long-request timeout, not a parser logic failure
- Measured local `/api/parse` at about 5.9 seconds and Render `/api/parse` timing out with `502` after about 110.8 seconds
- Added async parse job endpoints so uploads return quickly and the frontend polls for completion instead of waiting on one long request
- Updated the frontend upload flow to use parse jobs and show clearer status/error messages

**Verification**

- Local `QR 8091.pdf` parse confirmed route `KORD -> OTHH`
- Verified local health endpoint before implementing the fix
- Pending full verification after rebuild, local retest, and Render deploy

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
