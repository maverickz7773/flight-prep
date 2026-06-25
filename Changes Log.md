# Changes Log

Use this file as the shared handoff log between Codex and Claude Code when both are updating this repo.

## Update Rule

- After every meaningful repo change, add a new dated entry.
- Include: `date`, `model`, `summary`, `verification`, and `open items`.
- Keep this file factual. If earlier work was done outside this log, say that clearly instead of guessing.

## Current Working Notes

- Production runs from Render using the same repo root and URL: [https://flight-prep.onrender.com](https://flight-prep.onrender.com)
- Docker must include `Operational Info.txt`, `Enroute Info.txt`, and `NATS Procedure.txt` or local text-driven notes will disappear in production.
- Synology mounts `Operational Info.txt` and `Enroute Info.txt` from `/volume1/docker/flight-prep/` so routine private note updates do not require an app version bump.
- Use `scripts/smoke_check.sh` for a quick deploy check.
- Current smoke PDF: `QR 8945.pdf`
- Backend regression tests live in `backend/tests/`

## 2026-06-25 — Codex

**Summary**

- Fixed STAR extraction for primary arrivals when the final route page also contains a destination-to-alternate section
- `QR 872.pdf` now correctly reads `SASAN2` from the primary arrival segment before the alternate routing begins
- Kept the visible app version unchanged at `v1.1.10` for this same-version Synology hotfix

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_sid_star_parser`
- Confirmed `QR 872.pdf` parses `SID=KUPRO2E` and `STAR=SASAN2`
- Confirmed `QR 8564.pdf` still does not invent a STAR for the direct/VOR arrival case
- Spot-checked `QR 8945.pdf` and `QR 8288.pdf` SID/STAR parsing after the fix

**Open Items**

- Rebuild and redeploy the `v1.1.10` Synology image so the private app receives the parser hotfix without changing the displayed version

## 2026-06-17 — Codex

**Summary**

- Updated Synology `compose.yaml` to mount `Operational Info.txt` and `Enroute Info.txt` from the NAS project folder
- Kept the app image and visible version at `v1.1.10`
- Documented a note-only Synology update path so routine `OPS INFO` and FIR-note changes do not require Docker rebuilds or version bumps
- Clarified that Render still uses text files baked into the Docker image and therefore still requires a normal release for public text-note updates

**Verification**

- Confirmed Section 4/6 `OPS INFO` reads from `Operational Info.txt`
- Confirmed Section 5 FIR notes read from `Enroute Info.txt`
- Confirmed the backend reloads both files by modified time on future parses
- Uploaded `compose.yaml`, `Operational Info.txt`, and `Enroute Info.txt` to `/volume1/docker/flight-prep/`
- Recreated the Synology `flight-prep` project once to activate the NAS-mounted files
- Confirmed the running container has active mounts for:
  - `/volume1/docker/flight-prep/Operational Info.txt` -> `/app/Operational Info.txt`
  - `/volume1/docker/flight-prep/Enroute Info.txt` -> `/app/Enroute Info.txt`
  - `/volume1/docker/flight-prep/data` -> `/app/data`
- Confirmed Synology remained healthy on `v1.1.10`
- Fixed the HECA note labels from `Dep:` / `Arr:` to parser-compatible `DEP:` / `ARR:`
- Confirmed `QR 1302.pdf` (`HECA -> OTHH`) shows HECA departure `OPS INFO` in Section 4
- Confirmed `QR 1301.pdf` (`OTHH -> HECA`) shows HECA arrival `OPS INFO` in Section 6

**Open Items**

- None for the Synology note-mount setup

## 2026-06-15 — Codex

**Summary**

- Added company route identifier parsing from the operational route line before the departure ICAO
- Added `company_route` to the backend and frontend `FlightInfo` contract
- Confirmed support for:
  - `QR 935.pdf` → `MNL-45`
  - `QR 932.pdf` → `40-MNL`
  - `QR 8564.pdf` → `91H-LOS`
  - `QR 8812.pdf` → `90H-LOS`
  - `QR 8945.pdf` → `SZX-20ET`
- Added the company route beside the `MEL/CDL` information in the briefing header
- Kept the header row responsive so MEL/CDL and route information can wrap cleanly on mobile
- Prepared the change for release as `v1.1.10`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_flight_info_parser`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Refreshed the local `frontend_build` served at `http://127.0.0.1:8000`
- Released commit `77dfa8f` to `main`
- Confirmed local, Synology, and Render display `v1.1.10`
- Confirmed Synology is running `ghcr.io/maverickz7773/flight-prep:v1.1.10`
- Confirmed Synology parses `QR 8945.pdf` company route as `SZX-20ET`
- Ran `./scripts/smoke_check.sh https://flight-prep.onrender.com "QR 8945.pdf"`

**Open Items**

- None for this release

## 2026-06-15 — Codex

**Summary**

- Added a one-command `flight-prep` Synology release wrapper at `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/scripts/release_all.sh`
- Kept the automation scoped to `flight-prep` only with hardcoded safety checks for:
  - image repo `ghcr.io/maverickz7773/flight-prep`
  - Synology path `/volume1/docker/flight-prep`
  - project name `flight-prep`
  - container name `flight-prep`
- Added Synology SSH/Tailscale config templating with:
  - tracked example file `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/.synology-release.env.example`
  - ignored local secrets file `.synology-release.env`
- Refactored `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/scripts/release_synology.sh` so it can also run in `--skip-build` mode for dry-run validation
- Added Synology deploy automation steps to:
  - upload repo-root `compose.yaml` to `/volume1/docker/flight-prep`
  - detect `docker compose` first, then `docker-compose`
  - recreate only the `flight-prep` app over SSH/Tailscale
  - verify the running container image tag
  - verify Synology health and frontend version
- Added a short operator guide at `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/docs/synology-release.md`
- Updated `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/AGENTS.md` so the new primary Synology flow is `./scripts/release_all.sh vX.Y.Z`

**Verification**

- `bash -n scripts/release_synology.sh`
- `bash -n scripts/release_all.sh`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `cd backend && venv/bin/python -m unittest tests.test_airport_notes`
- `./scripts/release_all.sh --dry-run v1.1.9` after creating `.synology-release.env`
- Completed the first live automated release as `v1.1.9`
- Confirmed Synology is running `ghcr.io/maverickz7773/flight-prep:v1.1.9`
- Confirmed `http://100.83.254.51:8000/api/health` returns `status: ok`
- Confirmed the Synology frontend displays `v1.1.9`
- Confirmed `/volume1/docker/flight-prep/data/airport_feedback.sqlite3` remained present after recreation
- Updated the upload step to use legacy SCP mode (`scp -O`) for DSM SSH compatibility

**Open Items**

- Render verification is still indirect through `git push origin main`; the new script does not add separate Render polling yet

## 2026-06-15 — Codex

**Summary**

- Updated [Operational Info.txt](/Users/eby/Personal/Programming/Cloude%20Code%20Tutorial/Flight%20Prep/Operational%20Info.txt) with a new `[RPLL]` airport note block
- `RPLL` departure notes now include:
  - `L628` airway flight-level restriction
  - Manila clearance / startup / pushback / taxi call flow
  - expected vectors to `SIRCA`
  - `NADP A` acceleration and thrust-reduction reminders
  - runway, taxi, ramp-lightning, terrain, and `EOSID RWY 06` cautions
- `RPLL` arrival notes now include:
  - extra-fuel guidance for vectoring/weather deviation
  - `ROD/ROC` caution
  - speed profile guidance
  - false localizer / glideslope caution
  - runway / taxi / ramp-lightning cautions
  - holding and `RETI` references
- Updated [Enroute Info.txt](/Users/eby/Personal/Programming/Cloude%20Code%20Tutorial/Flight%20Prep/Enroute%20Info.txt):
  - added a new `[RPHI]` FIR block with CPDLC, airway, boundary, RNP, HF, LSWD, speed, holding, and oceanic emergency notes
  - added `Refer SCB overfly Tripoli.` to `[HLLL]`

**Verification**

- Reviewed the local diff for `Operational Info.txt` and `Enroute Info.txt`
- Confirmed the local app remained available at `http://127.0.0.1:8000`

**Open Items**

- Synology still needs the usual `compose.yaml` upload and project recreate/restart after the new image is cut

## 2026-06-05 — Codex

**Summary**

- Added FIR-scoped `FLIGHT HISTORY` to Section 5 `ROUTE` using the same SQLite DB file as airport history with a separate `fir_feedback` table
- Extended the backend feedback service and API with:
  - `GET /api/fir-feedback?firs=...`
  - `POST /api/fir-feedback`
  - `DELETE /api/fir-feedback/{id}`
- Extended `RouteSummary` with `fir_feedback`, grouped by FIR ICAO for immediate render on first parse
- Updated the Route-section FIR card so a FIR becomes interactive when it has either:
  - static enroute notes, or
  - saved FIR flight history
- Revised the FIR card UI to show two compact disclosures:
  - `NOTES`
  - `FLIGHT HISTORY`
- Added a dedicated frontend `FIRFeedbackPanel` with:
  - read-only OFP-derived `Date`
  - read-only OFP-derived `Route`
  - comments-only save form
  - newest-first saved history
  - summary rows showing `Date` plus compact route pair
  - per-entry permanent delete with confirmation
- Added saved-briefing FIR-history hydration in the frontend so older localStorage briefings can fetch the latest FIR history on reload
- Fixed the Section 5 FIR-history reopen bug by refreshing FIR entries from the API when the FIR card mounts, so a newly saved note is still present after closing and reopening the same FIR

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_airport_feedback`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Reproduced the save/close/reopen behavior locally and patched the FIR panel to refresh from `/api/fir-feedback` on reopen

**Open Items**

- Local manual test still needed in the running app:
  - save FIR history on one OFP
  - open another OFP crossing the same FIR
  - confirm the same FIR history appears there
- Render should remain effectively disabled for this feature until a Synology-first rollout is explicitly requested

## 2026-06-02 — Codex

**Summary**

- Updated [Enroute Info.txt](/Users/eby/Personal/Programming/Cloude%20Code%20Tutorial/Flight%20Prep/Enroute%20Info.txt) with expanded Africa/Malaysia enroute coverage
- Added new FIR sections for:
  - `WMFC`
  - `HECC`
  - `HLLL`
  - `FTTT`
  - `DNKK`
- Clarified older Red Sea crossing wording in existing enroute sections
- Updated [Operational Info.txt](/Users/eby/Personal/Programming/Cloude%20Code%20Tutorial/Flight%20Prep/Operational%20Info.txt) with a new `[DNMM] Arr:` airport note block
- `DNMM` arrival notes now include:
  - holding-fuel caution in below-minima weather
  - LOS approach boundary-entry reminder
  - speed restriction below FL100 within 49 DME
  - glide slope / RNAV / VOR 18R cautions
  - runway/taxiway surface and parking cautions

**Verification**

- Reviewed the local diff for `Enroute Info.txt` and `Operational Info.txt`
- Local app remained healthy at `http://127.0.0.1:8000`

**Open Items**

- Synology still needs the normal `compose.yaml` upload and project recreate after the new image/version push

## 2026-06-01 — Codex

**Summary**

- Added missing ICAO timezone mappings in `backend/parsers/flight_info.py` for the airports surfaced by `QR 8564.pdf`
- New coverage added for:
  - destination and alternates:
    - `DNMM`
    - `DGAA`
    - `DNPO`
    - `DNAA`
    - `DNKN`
  - additional enroute/operational airports from the same OFP:
    - `OEMA`
    - `OETF`
    - `OERS`
    - `HEGN`
    - `HECA`
    - `HEAX`
    - `HELX`
    - `FTTJ`
- Added a `QR 8564.pdf` regression in `backend/tests/test_flight_info_parser.py`
- `QR 8564` now parses:
  - `STD` from `OTHH` with `UTC+3`
  - `STA` to `DNMM` with `UTC+1`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_flight_info_parser`
- Direct parse check:
  - `QR 8564.pdf` → `dep OTHH +3`
  - `QR 8564.pdf` → `arr DNMM +1`

**Open Items**

- The app currently only displays UTC offsets in Section 1 for departure and arrival, even though the timezone map now covers the wider airport set from `QR 8564`
- If the user later wants UTC displayed for alternates or other airport lists in the UI, that would be a separate frontend/backend display enhancement

## 2026-06-02 — Codex

**Summary**

- Fixed STAR extraction for direct-to-airport arrivals in `backend/parsers/procedures.py`
- `QR 8564.pdf` was incorrectly getting a STAR because the parser reverse-scanned the waypoint table and picked up a non-STAR marker
- The STAR extractor now:
  - prefers the procedure line immediately before the destination runway line on route pages
  - treats `DCT` before the arrival airport as “no STAR”
  - still falls back to the ATC clearance line when a real STAR token is explicitly present there
- Added a regression in `backend/tests/test_sid_star_parser.py` to ensure `QR 8564` keeps `STAR = None`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_sid_star_parser`
- Direct parse spot checks:
  - `QR 8564.pdf` → `STAR = None`
  - `QR 849.pdf` → `STAR = TOVOX2L`
  - `QR 427.pdf` → `STAR = ORLEK1L`
  - `QR 701.pdf` → `STAR = PARCH4`
  - `QR 707.pdf` → `STAR = HYPER9`

**Open Items**

- If the user later finds other “direct to VOR” or “direct to airport” arrivals, reuse `QR 8564` as the regression pattern to guard STAR parsing against false positives

## 2026-06-01 — Codex

**Summary**

- Added a Synology-first airport feedback feature for Section 4 `TAKEOFF` and Section 6 `ARRIVAL`
- Kept feedback fully separate from `Operational Info.txt`; new feedback now persists in a SQLite datastore managed by a new backend service:
  - `backend/services/airport_feedback.py`
- Added new backend models and wired `airport_feedback` into `BriefingData`
- Added new feedback API endpoints:
  - `GET /api/airport-feedback`
  - `POST /api/airport-feedback`
  - `DELETE /api/airport-feedback/{id}`
- Enabled feedback by default on local and containerized non-Render environments, while keeping Render disabled via config
- Updated the frontend so Sections 4 and 6 now show a `FEEDBACK` block under `OPS INFO` and before `OM C`
- Added add/view/delete feedback flow:
  - editable departure defaults for `Date`, `Route`, `SID`, and `Runway`
  - arrival form simplified to airport-only above comments
  - newest-first accumulated entries
  - date as clickable summary
  - permanent per-entry delete with confirmation
- Kept feedback visibility keyed by airport + section only:
  - all `departure` entries for an airport appear whenever that airport is the departure airport
  - all `arrival` entries for an airport appear whenever that airport is the arrival airport
  - OFP number, flight number, route pair, and date do not control matching
- Extended saved feedback metadata with:
  - `route_text` for saved departure display
  - `runway` for saved departure display
- Added saved-briefing hydration for airport feedback in `frontend/src/app/page.tsx`
- Updated deployment/runtime files for Synology feedback persistence:
  - `compose.yaml` now mounts `./data:/app/data`
  - `Dockerfile` creates `/app/data`
  - `render.yaml` explicitly disables the feature with `AIRPORT_FEEDBACK_ENABLED=0`
  - `.gitignore` now ignores `data/*.sqlite3`
  - tracked `data/.gitkeep`
- Added backend regression coverage for feedback CRUD and API behavior in `backend/tests/test_airport_feedback.py`
- Added `httpx` to `backend/requirements.txt` so FastAPI `TestClient`-based API tests run in the repo venv

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_airport_feedback tests.test_airport_notes tests.test_sid_star_parser tests.test_flight_info_parser`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Refreshed locally served static frontend:
  - `rm -rf frontend_build && cp -R frontend/out frontend_build`
- Local runtime sanity checks against `http://127.0.0.1:8000`:
  - `/api/health` returns `"airport_feedback_enabled": true`
  - `/api/airport-feedback?departure=OTHH&arrival=OLBA` returns grouped lists scoped only by airport + section

**Open Items**

- Manual UI acceptance is still pending for the revised editable departure form and simplified arrival form in the local app
- Synology deployment still needs a new image/version cut before this feature goes live on the NAS
- Render should remain intentionally disabled for this feature until the user explicitly wants cloud feedback persistence

## 2026-06-01 — Codex

**Summary**

- Renamed the airport feedback panel heading from `FEEDBACK` to `FLIGHT HISTORY`
- Kept the action label as `Add Feedback`
- Updated the collapsed saved-entry summary row in both Section 4 and Section 6 to show:
  - `Date`
  - route summary in compact ICAO form, for example `WMKK OTHH`
- Revised Section 6 `ARRIVAL` flight history form to match the Section 4 `TAKEOFF` structure:
  - `Date`
  - `STAR`
  - `Route`
  - `Runway`
  - `Comments`
- Extended feedback persistence to store and display saved arrival `STAR` values
- Updated expanded arrival history entries to show the same saved fields:
  - `Date`
  - `STAR`
  - `Route`
  - `Runway`
  - comment
  - saved timestamp

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_airport_feedback`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- refreshed locally served static frontend after the build

**Open Items**

- Manual local UI check is still needed to confirm the new arrival form/layout feels good on mobile

## 2026-05-28 — Codex (Synology release cut)

**Summary**

- Ran `./scripts/release_synology.sh v1.1.3`
- Updated `frontend/src/lib/version.ts` to `v1.1.3`
- Updated repo-root `compose.yaml` to `ghcr.io/maverickz7773/flight-prep:v1.1.3`
- Built and pushed the Synology image for `linux/amd64` to GHCR so the NAS can pick up the latest pushed note-file changes

**Verification**

- `./scripts/release_synology.sh v1.1.3`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`

**Open Items**

- Upload the updated `compose.yaml` to Synology `/docker/flight-prep/`
- Recreate or restart the `flight-prep` project in Container Manager so Synology pulls `v1.1.3`

## 2026-05-28 — Codex

**Summary**

- Updated `Enroute Info.txt`:
  - added an `OJAC` communication note: `Freq : 128.5, inform aircraft registration`
- Updated `Operational Info.txt`:
  - simplified `OTHH` departure notes by removing several completed or SCB-only items
  - expanded `OLBA` departure notes with `LEBOR1D`, frequencies, climb restrictions, gradient, pavement, and taxi cautions
  - expanded `OLBA` arrival notes with `CHEKA.1N`, descent/frequency flow, runway 03 details, gate/taxi guidance, and current ILS-related NOTAM notes

**Verification**

- Direct local parse checks:
  - `QR 426.pdf` → `OLBA` arrival note now begins with `ILS.03. CHEKA.1N`
  - `QR 427.pdf` → `OLBA` departure note now begins with `Rwy 21 : LEBOR.1D...`
  - `QR 426.pdf` and `QR 427.pdf` → `OJAC` enroute FIR note now begins with `Freq : 128.5, inform aircraft registration`
  - `QR 426.pdf` and `QR 427.pdf` → `OLBB` FIR note still present
  - `QR 1150.pdf` → `OEDF` arrival note still present

**Open Items**

- Render will pick up these text-file updates after the new commit deploys
- Synology still needs a new image/restart cycle later if these text changes should go live there

## 2026-05-28 — Codex

**Summary**

- Added HTML no-cache headers in `backend/main.py` for the top-level app page so Safari and other browsers stop sticking to an older visible app version after a release
- Fixed SID parsing in `backend/parsers/procedures.py` for OFPs like `QR 427.pdf`, where the departure runway and SID appear on the same ATC-clearance line (`OLBA 21 LEBOR1D ...`) instead of on a separate runway line
- Added `OLBA` to the airport timezone map in `backend/parsers/flight_info.py` so Section 1 now shows `STD UTC` for Beirut departures
- Added backend regression coverage for:
  - `QR 427.pdf` SID parsing in `backend/tests/test_sid_star_parser.py`
  - `QR 427.pdf` departure UTC offset in `backend/tests/test_flight_info_parser.py`

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_sid_star_parser`
- `cd backend && venv/bin/python -m unittest tests.test_flight_info_parser`
- Direct parse checks:
  - `QR 427.pdf` → `SID = LEBOR1D`
  - `QR 427.pdf` → `STD = 27/1625`, `departure_utc_offset = +3`
  - `QR 426.pdf` → `SID = TULUB2A`
  - `QR 701.pdf` → `SID = TULUB2A`
  - `QR 1150.pdf` → `SID = TULUB2A`
- `curl -I http://127.0.0.1:8000` confirms HTML now returns:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`

**Open Items**

- The latest manual edits in `Enroute Info.txt` and `Operational Info.txt` remain local unless intentionally included in a later release commit

## 2026-05-25 — Codex

**Summary**

- Fixed contingency fuel parsing in `backend/parsers/fuel.py` for minimum-fuel layouts like `CONT MINM 590 0005 BLK 0100`
- Switched contingency parsing to read the first real `CONT` line, ignore the separate `AT DEP` advisory line, and strip any trailing `BLK` portion before extracting type, fuel, and time
- Added `backend/tests/test_fuel_parser.py` to cover both:
  - minimum contingency format from `QR 1150.pdf`
  - percentage contingency format from `QR 8974.pdf`
- Reordered Section 2 `FUEL (KG)` rows in the frontend to the operational sequence:
  - `TAXI`, `TRIP`, `CONT`, `ALTN`, `FINL`, `MIN FUEL`, `EXTRA`, `RAMP`
- Moved `T/O` out of the main fuel sequence into its own separate line so it stays visible without interrupting the requested order
- Shortened the Section 2 label from `MIN FUEL REQ` to `MIN FUEL`
- Updated local runtime note files:
  - added/updated `OLBB` in `Enroute Info.txt`
  - added/updated `OEDF` and `OLBA` in `Operational Info.txt`
- Verified the new text-file entries against real OFPs:
  - `QR 1150.pdf` now picks up `OEDF` arrival `OPS INFO`
  - `QR 427.pdf` now picks up `OLBA` departure `OPS INFO`
  - `QR 427.pdf` also shows the new `OLBB` enroute FIR note
- Added backend HTML no-cache headers in `backend/main.py` so future releases do not get stuck on an older visible app version in Safari or other browsers

**Verification**

- `cd backend && venv/bin/python -m unittest tests.test_fuel_parser`
- `cd backend && venv/bin/python -m unittest tests.test_flight_info_parser`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Refreshed `frontend_build` from the latest static export
- Confirmed live parse results locally:
  - `QR 1150.pdf` → `CONT 590`, type `MINM`, time `0005`
  - `QR 8974.pdf` → `CONT 1185`, type `3P/C VTBS`, time `0010`
  - `QR 1150.pdf` → `OEDF` arrival `OPS INFO` present
  - `QR 427.pdf` → `OLBA` departure `OPS INFO` present
  - `QR 427.pdf` → `OLBB` FIR note present in Section 5
- `curl -I http://127.0.0.1:8000` confirms HTML now returns:
  - `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`
  - `Pragma: no-cache`
  - `Expires: 0`

**Open Items**

- If more contingency layouts appear in future OFPs, add them as regression cases in `backend/tests/test_fuel_parser.py`

## 2026-05-20 — Codex

**Summary**

- Added a tracked Synology project file at `compose.yaml` for the private NAS deployment
- Added `scripts/release_synology.sh` to automate the Synology release flow:
  - update `frontend/src/lib/version.ts`
  - update the GHCR image tag in `compose.yaml`
  - build and push a `linux/amd64` image to `ghcr.io/maverickz7773/flight-prep`
- Updated `AGENTS.md` with a dedicated Synology deployment section and a Synology update checklist for Codex and Claude Code

**Verification**

- `bash -n scripts/release_synology.sh`
- Confirmed the current Synology deployment is running from `ghcr.io/maverickz7773/flight-prep:v1.1.1`

**Open Items**

- When releasing the next version, run `./scripts/release_synology.sh vX.Y.Z`, then upload the updated `compose.yaml` to Synology and restart the `flight-prep` project
- Keep Render as backup until Synology has been stable in daily use

## 2026-05-20 — Codex

**Summary**

- Added a shared app version constant and set the current UI version to `v1.1.1`
- Updated the upload screen so the old `Upload OFP PDF for cockpit-ready briefing` subtitle is replaced by the version label
- Updated the parsed briefing top bar to show `v1.1.1` beside `FLIGHT PREP`
- Refined Section 1 `Flight Overview` on mobile by moving `ETOPS` and `NATS` into compact side-by-side toggle buttons
- Hid ETOPS details by default and kept both ETOPS and NATS content opening full-width underneath for cleaner iPhone/iPad readability

**Verification**

- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Refreshed `frontend_build` from the latest static export
- Confirmed the local upload page now shows only `FLIGHT PREP` and `v1.1.1`

**Open Items**

- Verify Render shows the same `v1.1.1` label after the new deploy finishes

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
- Added a release marker to `/api/health` in `backend/main.py` (`2026-05-19-nats-v2`) so Render rollout can be verified directly after deploy

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
