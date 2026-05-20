# Roadmap and Contributor Guide

This roadmap tracks the public evolution of B.I.A.S.E.D. and highlights where contributors can add high-value improvements.

## Timeline narrative
- Earlier project origin: domain exploration and prototype learning.
- Current public implementation: milestone-based rebuild and hardening.
- Ongoing track: continuous product and engineering quality improvements.

## Public milestones
- `v0.2.0-milestone-b-preview` — imports + recurring obligations foundations
- `v0.3.0-milestone-b-final` — Postgres-backed owner workflows
- `v0.4.0-milestone-c` — AI analyst core and model routing
- `v0.5.0-milestone-d` — forecasting, scenarios, action workflows
- `v1.0.0-showcase` — deployment packaging and OSS polish

## Active focus (current cycle)
- strengthen testing depth for core flows
- improve proof assets (screenshots, walkthrough outputs)
- harden docs around runtime behavior, tradeoffs, and failure handling

## Next milestone themes
### v1.1 candidate
- API integration tests for import confirmation and recurring obligation lifecycle
- web e2e smoke flow for dashboard → import → ask → action transitions
- richer action center filtering and export workflows

### v1.2 candidate
- import mapping presets by common SMB tooling formats
- expanded localization scaffolding (INR-first, multilingual-ready labels)
- improved observability for model mode routing and scheduler runs

## Module boundaries
- `apps/web`: UX composition, state orchestration, PWA surfaces
- `apps/api`: ingestion, analytics, retrieval, forecasting, scheduler logic
- `packages/contracts`: typed API/UI contracts and structured AI outputs
- `packages/ui`: shared design primitives and visual consistency
- `infra`: local runtime and deployment descriptors
- `data/demo`: sanitized fixtures only

## Contribution entry points
### Good first issues
- add filtering chips for Action Center by status
- add CSV export for forecast/scenario results
- add import mapping presets for common source formats
- add Playwright coverage for planner and action transitions

### Mid-level contributions
- improve API contract test coverage across investigation and scheduler flows
- enhance error-state UX around provider configuration and fallbacks
- tighten docs with concrete sample outputs for critical endpoints

## Definition of done for PRs
- change is scoped and reviewable
- docs are updated when behavior changes
- lint/typecheck/build pass for touched modules
- data safety rules are respected (`data/demo` only, sanitized fixtures)

## Data safety guardrails
- never commit private customer or family business records
- keep all public fixtures sanitized and reproducible
- use the anonymization helper before adding new datasets
