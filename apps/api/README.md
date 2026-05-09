# api

FastAPI service for ingestion, analytics, retrieval, forecasting, and AI orchestration in B.I.A.S.E.D.

## Scope
`apps/api` provides backend workflows that power the web application:
- import preview, normalization, and confirmation flows
- recurring obligations, documents, and ledger persistence
- investigation and briefing generation
- forecast, scenario, and scheduler execution
- model provider mode persistence and runtime metadata

## Key API surfaces
- `GET /health`
- `GET /api/dashboard`
- `POST /api/import-jobs`
- `POST /api/import-jobs/{job_id}/confirm`
- `POST /api/investigations`
- `POST /api/briefings/generate`
- `POST /api/forecasts/run`
- `POST /api/scenarios/run`
- `POST /api/scheduler/run`

## Local commands
- start API locally:
  - `uv run --project apps/api uvicorn api.main:app --reload --port 8000`
- demo data management:
  - `uv run --project apps/api api-data seed`
  - `uv run --project apps/api api-data reset`

## Runtime notes
- Postgres is the source of truth for operational business memory.
- pgvector stores retrieval chunks for evidence snippets.
- local-open mode runs with Ollama; cloud providers are optional.

## Quality expectations
- preserve deterministic demo behavior for reproducible walkthroughs
- keep endpoint contracts aligned with `packages/contracts`
- treat prompt guardrails and data safety constraints as non-optional
