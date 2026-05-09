# Deployment Guide (Milestone E)

This guide covers both showcase paths:

1. Hosted demo (`Vercel + Render + Supabase`)
2. Private self-hosted mode (`Docker Compose + Ollama`)

## Hosted demo (near-zero cost)

### 1) Supabase (Postgres + pgvector)

- Create a new Supabase project.
- In SQL editor, run:

```sql
create extension if not exists vector;
```

- Copy connection string and use it as `DATABASE_URL` for API and Web server-side env.

### 2) Render (API)

- Create a new Web Service from this repo.
- Root directory: repo root.
- Build command:

```bash
pip install uv && uv sync --project apps/api
```

- Start command:

```bash
uv run --project apps/api uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

- Required env vars:
  - `DATABASE_URL`
  - `CORS_ORIGINS` (set to your Vercel app URL)
  - `DEMO_WORKSPACE_SLUG`
  - `DEMO_WORKSPACE_NAME`
  - Optional BYO keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

### 3) Vercel (Web)

- Import the same repo in Vercel.
- Set project root to `apps/web`.
- Required env vars:
  - `NEXT_PUBLIC_APP_URL` = deployed Vercel URL
  - `NEXT_PUBLIC_API_BASE_URL` = Render API URL
  - `INTERNAL_API_BASE_URL` = same Render API URL
  - `DATABASE_URL` = Supabase DB URL
  - `AUTH_SECRET` = strong random string

## Self-hosted mode (Windows-first)

From repo root:

```bash
pnpm docker:up
pnpm demo:seed
```

App URLs:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Postgres: `localhost:5433`
- Ollama: `http://localhost:11434`

Optional local model pull:

```bash
docker exec -it biased-ollama ollama pull llama3.1
```

Stop stack:

```bash
pnpm docker:down
```

## Runtime modes

- `local-open`: Ollama-first (default, no paid APIs required)
- `byo-cloud`: cloud providers via env keys
- `hybrid`: local-first, cloud fallback
