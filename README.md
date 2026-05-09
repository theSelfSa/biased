# B.I.A.S.E.D.

**Business Intelligence Assistant for Enriched Decision-Making**

B.I.A.S.E.D. is an open-source AI decision intelligence platform for SMB owners. It is designed to rebalance the AI advantage that large companies already enjoy by helping smaller businesses import their historical records, understand recurring obligations, investigate changes in margins and cash flow, and act on evidence-backed recommendations.

The first public story is an India-first pharmacy and medical-store demo, while the core domain model stays reusable for other small and medium businesses.

## Current status

This repository is being built in public in visible milestones:

1. Foundation, branding, auth, and PWA shell
2. Business memory, imports, recurring obligations, and dashboard
3. AI investigations, retrieval, and model routing
4. Forecasting, scenarios, and action center
5. OSS hardening, demos, and self-hosted packaging

Checkpoint tags:

- `v0.2.0-milestone-b-preview`
- `v0.3.0-milestone-b-final`
- `v0.4.0-milestone-c`
- `v0.5.0-milestone-d`
- `v1.0.0-showcase`

## Stack

- Next.js App Router + TypeScript
- Better Auth
- Drizzle + PostgreSQL + pgvector
- Tailwind CSS v4 + shadcn-inspired component system
- FastAPI + Polars + DuckDB
- LiteLLM + LangGraph + Ollama
- Turbo + pnpm + uv

## Quick start

1. Install dependencies:
   - `pnpm install`
   - `uv sync --project apps/api`
2. Copy `.env.example` to `.env.local` in `apps/web`.
3. Start local services with Docker:
   - `pnpm docker:up`
   - PostgreSQL runs on `localhost:5433` to avoid conflicts with other local stacks.
4. Apply auth and app schema:
   - `pnpm --filter @biased/web auth:migrate`
   - `pnpm db:migrate`
5. Seed or reset the demo workspace (Postgres-backed):
   - `pnpm demo:seed` (idempotent)
   - `pnpm demo:reset` (deterministic reset + reload)
6. Run the apps:
   - `pnpm web:dev`
   - `pnpm api:dev`

## Repository layout

- `apps/web` — web app, auth, dashboard, PWA shell
- `apps/api` — FastAPI analytics and AI orchestration service
- `packages/contracts` — shared contracts and schemas
- `packages/ui` — shared UI primitives and design tokens
- `packages/config` — shared config baselines
- `infra` — Docker Compose and local infra docs
- `data/demo` — sample datasets and fixtures
- `docs` — architecture, deployment, roadmap, and showcase scripts

## Demo direction

The first showcase will help an owner answer questions like:

- Why did profits drop this month?
- What bills are due in the next 10 days?
- Which products are slow-moving or near expiry?
- What should I reorder and what should I delay?

## Feature highlights

- Postgres-first business memory for imports, ledgers, recurring obligations, documents, and action state.
- Investigation mode with guardrails, evidence/citations, confidence, provider mode, and latency/cost metadata.
- Model runtime modes:
  - `local-open`
  - `byo-cloud`
  - `hybrid`
- Forecast lab for baseline forecasting, deterministic scenarios, and scheduler-triggered brief generation.
- Action center workflow states:
  - `open`
  - `watching`
  - `snoozed`
  - `resolved`

## Deployment docs

- Architecture: [docs/architecture.md](docs/architecture.md)
- Deployment: [docs/deployment.md](docs/deployment.md)
- Showcase prompts/script: [docs/showcase.md](docs/showcase.md)
- Contributor roadmap: [docs/roadmap.md](docs/roadmap.md)
- Demo data rules: [data/demo/README.md](data/demo/README.md)

## Privacy rule

Never commit raw private business data. Any real-world records used for demos must be sanitized before they enter this repository.
