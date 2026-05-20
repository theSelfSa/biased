# Changelog

All notable changes to B.I.A.S.E.D. are documented in this file.

## Unreleased

### Changed

- Aligned workspace and API version metadata to `1.0.0` to match the public `v1.0.0-showcase` release baseline.
- Replaced placeholder test scripts with smoke-check commands (`pnpm test` now executes type-level checks in active workspace packages).

## v1.0.0-showcase - 2026-05-09

### Added

- Hosted + self-hosted deployment documentation for `Vercel + Render + Supabase` and Docker Compose local mode.
- Full-stack self-hosted runtime packaging:
  - `apps/web/Dockerfile`
  - `apps/api/Dockerfile`
  - `infra/docker-compose.yml` (web + api + postgres + ollama)
- Showcase assets/docs:
  - architecture overview with system flow
  - scripted 90-second and 2-minute demo paths
  - contributor roadmap and good-first-issue list
- Demo data privacy guardrails and anonymization script:
  - `data/demo/README.md`
  - `data/demo/anonymize_fixtures.py`

## v0.5.0-milestone-d - 2026-05-09

### Added

- Forecasting and scenario planning APIs with explainable, deterministic baselines.
- Scheduler execution endpoint for morning brief + anomaly + due-reminder runs.
- Forecast Lab UI with:
  - metric forecast
  - scenario planner templates
  - manual scheduler trigger panel
- Action Center status lifecycle support:
  - `open`
  - `watching`
  - `snoozed`
  - `resolved`

## v0.4.0-milestone-c - 2026-05-09

### Added

- Model provider runtime settings API and persistence:
  - `local-open`
  - `byo-cloud`
  - `hybrid`
- Investigation response metadata:
  - provider
  - mode
  - latency
  - estimated cost
- Retrieval chunk storage with pgvector-backed similarity lookup and evidence citations.
- Guarded investigation flow with safe prompt checks and SQL insight helper.
- Model settings UI and expanded investigation workspace for clearer demo flows.

## v0.3.0-milestone-b-final - 2026-05-09

### Added

- Postgres-backed import jobs and import-row persistence for preview/confirm flows.
- Postgres-backed recurring obligations, business documents, and ledger transaction storage.
- Quick-add API + dashboard UX for `sale`, `purchase`, and `expense` daily owner entries.
- Demo workspace data utilities:
  - `pnpm demo:seed` (idempotent seed)
  - `pnpm demo:reset` (deterministic reset + reload)

### Changed

- Dashboard stats and action queue now compute from live Postgres data.
- API persistence moved off runtime JSON files for owner-critical flows.
- Drizzle schema expanded to include operational tables used by the API layer.

## v0.2.0-milestone-b-preview - 2026-05-09

### Added

- Recurring obligation CRUD flows with owner-facing status transitions (`due`, `scheduled`, `paid`).
- Persisted document upload workspace and retrieval-ready document history view.
- Import preview + confirm/apply workflow for CSV and Excel historical records.
- Runtime-backed import ledger cards and import history timeline.
- Action Center queue surface powered by persisted owner context.

### Changed

- Dashboard recurring obligations section now includes interactive management instead of static rows.
- Actions and imports pages now render from runtime API data contracts.
- Shared contracts expanded for import confirmation, action center snapshots, and recurring obligation inputs.

### Quality

- Lint, typecheck, build, tests, and API compile sanity verified on this checkpoint.
