# Roadmap and Contributor Entry Points

## Current release path

- `v0.3.0-milestone-b-final` ✅
- `v0.4.0-milestone-c` (AI analyst core)
- `v0.5.0-milestone-d` (forecasting + scenarios + action workflows)
- `v1.0.0-showcase` (deployment + OSS hardening)

## Module boundaries

- `apps/web`: UX, page composition, client interactions
- `apps/api`: import pipelines, analytics, retrieval, forecasting, scheduling
- `packages/contracts`: shared API and UI data contracts
- `packages/ui`: shared branded primitives
- `infra`: local stack and deployment descriptors
- `data/demo`: sanitized fixtures only

## Good first issues

- Add filtering chips for Action Center by status.
- Add CSV export for forecast and scenario outputs.
- Add import mapping presets by source tool (Tally/Zoho/offline formats).
- Add localization scaffold for INR + future multilingual labels.
- Add Playwright e2e coverage for planner and action status transitions.

## Data safety guardrail

- Never commit private customer or family business records.
- Use sanitized fixtures in `data/demo` only.
- Use the anonymization script before creating any new public dataset.
