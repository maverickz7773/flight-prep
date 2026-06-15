# Synology Release Automation

Use the one-command release flow for the `flight-prep` project only.

## First-time setup

1. Copy `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/.synology-release.env.example` to `/Users/eby/Personal/Programming/Cloude Code Tutorial/Flight Prep/.synology-release.env`
2. Fill in:
   - `SYNOLOGY_SSH_USER`
   - `SYNOLOGY_SSH_HOST` if the Tailscale IP changes
   - `SYNOLOGY_SSH_PORT` only if you changed SSH away from port `22`

## Normal release command

```bash
./scripts/release_all.sh v1.1.9
```

That command will:
- run local checks
- update `frontend/src/lib/version.ts`
- update repo-root `compose.yaml`
- build and push `ghcr.io/maverickz7773/flight-prep:v1.1.9`
- commit and push `main`
- upload `compose.yaml` to Synology `/volume1/docker/flight-prep`
- recreate only the Synology `flight-prep` app
- verify Synology health and frontend version

## Dry run

```bash
./scripts/release_all.sh --dry-run v1.1.9
```

Use this to validate:
- version format
- config loading
- local checks
- file updates

Dry run skips:
- Docker push
- git commit/push
- Synology upload and restart

## Expected prompts and failure recovery

- If `.synology-release.env` is missing, the script stops and tells you to create it from the example.
- If there are unexpected untracked files, the script stops before any release work starts.
- If the Synology SSH step fails, fix the SSH/Tailscale issue and rerun the same command.
- If the Synology app refresh fails after GitHub/GHCR already succeeded, rerun the same command after fixing the NAS issue; the script is scoped to `flight-prep` only.
