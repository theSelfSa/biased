# Showcase Runbook

Use this runbook for recruiter demos, interview walkthroughs, and recorded proof assets.

## Demo preparation checklist
1. Start stack and seed demo data:
   - `pnpm docker:up`
   - `pnpm demo:seed`
2. Confirm app health:
   - web: `http://localhost:3000`
   - api: `http://localhost:8000/health`
3. Keep one concise narrative:
   - business problem
   - evidence-backed investigation
   - action-oriented output

## 90-second recruiter walkthrough (impact-first)
1. Open Dashboard and call out revenue/margin/bills/near-expiry signals.
2. Open Imports and show confirmed ledger history.
3. Open Ask B.I.A.S.E.D. and run:
   - `Why did profit drop this month?`
4. Highlight evidence, confidence, and provider metadata.
5. Open Action Center and move one item:
   - `open -> snoozed -> resolved`
6. Open Forecast Lab and run one forecast + one scenario.

## 2-3 minute technical walkthrough (depth-first)
1. Show architecture summary (`docs/architecture.md`) in one sentence.
2. Upload one document in Documents workspace.
3. Re-run investigation and point to document citations.
4. Save model mode as `hybrid` with providers:
   - `openrouter, openai`
5. Trigger scheduler run and show:
   - generated brief id
   - anomaly count
   - due reminder count
6. Close with deployment options:
   - hosted demo path
   - self-hosted Docker + Ollama

## Prompt pack for consistency
- `Why did profit drop this month?`
- `What are my top selling products?`
- `Which expense categories are spiking?`
- `What should I reorder next week?`

## Expected evidence points
- investigation output includes:
  - summary
  - confidence
  - evidence list with source labels
  - recommendations
  - provider/mode/latency/cost metadata
- action lifecycle is visible:
  - `open`
  - `watching`
  - `snoozed`
  - `resolved`
- forecast/scenario output is deterministic and explainable

## Recording checklist
- keep browser zoom and font readable
- use stable sample prompts from this file
- avoid long pauses while loading pages
- show one end-to-end flow, not every feature
- keep versions aligned with current tagged release

## Repository proof assets to maintain
- 90-second walkthrough video
- 2-3 minute technical walkthrough video
- screenshots for dashboard, imports, investigation, action center, forecast lab
- one sample investigation response snippet in docs with citations and metadata
