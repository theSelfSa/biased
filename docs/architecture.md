# Architecture Overview

B.I.A.S.E.D. is split into a web app, an API service, shared contract packages, and local infrastructure.

## Web app

- Marketing and product story
- Better Auth session handling
- Business workspace flows
- Dashboard, imports, documents, actions, and AI investigation surfaces

## API service

- Import parsing and validation
- Analytics and dashboard snapshots
- Retrieval and document chunking
- AI orchestration and investigation flows
- Forecasting and scheduled jobs

## Shared packages

- Contracts: shared DTOs and zod schemas
- UI: branded components and layout primitives
- Config: workspace-level config baselines

## Local infrastructure

- PostgreSQL + pgvector
- Ollama
- Optional self-hosted web/API runtime via Docker Compose
