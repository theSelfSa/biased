# Feature Evidence Map
This document maps core product claims to concrete implementation points in this repository.

## Agentic RAG investigation workflow
- Backend investigation entrypoint: `apps/api/src/api/main.py` (`POST /api/investigations`)
- Orchestration runtime: `apps/api/src/api/services/agent_orchestration.py`
- Investigation assembly and evidence output: `apps/api/src/api/services/demo_data.py` (`generate_investigation`)
- Structured contract for investigation output (including orchestration metadata): `packages/contracts/src/index.ts`
- UI display of tool route/trace: `apps/web/components/investigation-console.tsx`

## pgvector-backed retrieval and citations
- Extension setup + vector schema: `apps/api/src/api/services/demo_data.py` (`ensure_operational_schema`)
- Chunking and embeddings: `apps/api/src/api/services/demo_data.py` (`chunk_text`, `embedding_for_text`, `upsert_document_chunks`)
- Similarity retrieval: `apps/api/src/api/services/demo_data.py` (`retrieve_document_citations`)

## MCP server for external tool integration
- MCP JSON-RPC handler: `apps/api/src/api/services/mcp_rpc.py`
- Public MCP endpoint: `apps/api/src/api/main.py` (`POST /mcp`)
- Exposed tool methods: `initialize`, `tools/list`, `tools/call`

## Full-stack platform (Next.js + FastAPI + Docker Compose)
- Web app: `apps/web`
- API service: `apps/api`
- Local full stack runtime: `infra/docker-compose.yml`
- License: `LICENSE` (Apache-2.0)

## PWA delivery
- PWA manifest: `apps/web/app/manifest.ts`
- Service worker registration: `apps/web/components/pwa-register.tsx`
- Service worker file: `apps/web/public/sw.js`

## RBAC authentication
- Auth integration: `apps/web/lib/auth.ts`, `apps/web/lib/session.ts`
- Workspace membership schema: `apps/web/lib/schema.ts` (`workspace_members`)
- RBAC helpers: `apps/web/lib/rbac.ts`
- RBAC-protected membership APIs:
  - `apps/web/app/api/workspaces/[slug]/members/route.ts`
  - `apps/web/app/api/workspaces/[slug]/members/[userId]/route.ts`

## Scenario planning engine
- API endpoint: `apps/api/src/api/main.py` (`POST /api/scenarios/run`)
- Scenario logic: `apps/api/src/api/services/demo_data.py` (`build_scenario_plan`)
- Planner UI: `apps/web/components/forecast-lab.tsx`
