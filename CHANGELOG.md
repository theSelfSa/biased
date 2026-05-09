# Changelog

All notable changes to B.I.A.S.E.D. are documented in this file.

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
