# Contributing to B.I.A.S.E.D.

Thanks for contributing. This project is being built in public and is organized around clear milestones, so good contributions are usually small, scoped, and easy to review.

## Ground rules

- Do not commit raw private business data.
- Prefer additive, well-scoped changes over broad rewrites.
- Keep the India-first pharmacy demo authentic, but keep the underlying domain model reusable for other SMBs.
- For new features, update docs and sample data expectations alongside the code.

## Getting started

1. Install workspace dependencies:
   - `pnpm install`
   - `uv sync --project apps/api`
2. Start local infra:
   - `pnpm docker:up`
3. Run the apps:
   - `pnpm web:dev`
   - `pnpm api:dev`

## Good first contributions

- Improve dashboard polish and mobile responsiveness
- Add more realistic sample import files
- Expand document parsing and retrieval
- Add tests around import preview, obligations, and investigation flows
- Improve Docker and self-hosted documentation
