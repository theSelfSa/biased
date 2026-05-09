# Demo Data Rules

This folder is the only place for public sample datasets used by B.I.A.S.E.D.

## Rules

- Never commit raw private business records.
- Never commit real customer phone numbers, email addresses, or addresses.
- Any external dataset must be sanitized before commit.

## Sanitization helper

Use:

```bash
python data/demo/anonymize_fixtures.py data/demo/<file>.csv
python data/demo/anonymize_fixtures.py data/demo/<file>.json
```

Use `--in-place` only after you review the generated sanitized copy.
