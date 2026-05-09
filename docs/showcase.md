# Showcase Script

Use this script for recruiter demos, recorded walkthroughs, and README-linked proof.

## 90-second flow

1. Open dashboard and show imported stats + near-expiry card.
2. Open Imports and show confirmed ledger history.
3. Open Ask B.I.A.S.E.D. and run:
   - `Why did profit drop this month?`
4. Show evidence cards, confidence, and provider metadata.
5. Open Action Center and move one item through:
   - `open -> snoozed -> resolved`
6. Open Forecast Lab and run one forecast + one scenario.

## 2-minute flow (expanded)

1. Upload one document in Documents workspace.
2. Run investigation again and show document citations in evidence.
3. Save model mode as `hybrid` with providers:
   - `openrouter, openai`
4. Trigger scheduler run and show generated brief id and reminder counts.

## Prompt set for consistency

- `Why did profit drop this month?`
- `What are my top selling products?`
- `Which expense categories are spiking?`
- `What should I reorder next week?`

## Expected outcomes

- Investigation returns:
  - summary
  - confidence
  - evidence
  - recommendations
  - provider/mode/latency/cost metadata
- Action Center supports owner workflow states:
  - `open`
  - `watching`
  - `snoozed`
  - `resolved`
- Forecast Lab returns deterministic, explainable scenario deltas.
