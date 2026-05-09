import type { ImportLedgerSnapshot } from "@biased/contracts";
import { Card, CardDescription, CardTitle } from "@biased/ui";

function humanizeImportType(importType: string) {
  return importType.replaceAll("_", " ");
}

function renderValue(value: unknown) {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

export function ImportLedger({ ledger }: { ledger: ImportLedgerSnapshot }) {
  return (
    <div className="space-y-6">
      <section className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        {ledger.collections.map((collection) => (
          <Card key={collection.importType} className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-brand-600)]">
                {humanizeImportType(collection.importType)}
              </p>
              <CardTitle>{collection.rowCount.toLocaleString("en-IN")} imported rows</CardTitle>
              <CardDescription>
                {collection.latestImportAt
                  ? `Latest import on ${collection.latestImportAt.slice(0, 10)}`
                  : "No confirmed import yet for this ledger."}
              </CardDescription>
            </div>

            <div className="space-y-2 text-sm">
              <p className="font-medium">Detected columns</p>
              <div className="flex flex-wrap gap-2">
                {collection.columns.length ? (
                  collection.columns.map((column) => (
                    <span
                      key={column}
                      className="rounded-full bg-slate-100 px-3 py-1 dark:bg-white/5"
                    >
                      {column}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 dark:text-slate-400">
                    No stored columns yet
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <p className="font-medium">Recent rows</p>
              {collection.sampleRows.length ? (
                <div className="space-y-2">
                  {collection.sampleRows.map((row, index) => (
                    <div
                      key={`${collection.importType}-${index}`}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
                    >
                      <dl className="grid gap-2">
                        {Object.entries(row).map(([key, value]) => (
                          <div key={key} className="grid gap-1 sm:grid-cols-[8rem_1fr]">
                            <dt className="text-xs uppercase tracking-[0.16em] text-slate-500">
                              {key}
                            </dt>
                            <dd>{renderValue(value)}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  ))}
                </div>
              ) : (
                <CardDescription>
                  Confirm an import to start building this ledger inside B.I.A.S.E.D.
                </CardDescription>
              )}
            </div>
          </Card>
        ))}
      </section>

      <Card className="space-y-4">
        <CardTitle>Import history</CardTitle>
        <CardDescription>
          Every confirmed import becomes part of the business memory and can later power
          investigations, forecasting, and action recommendations.
        </CardDescription>

        {ledger.history.length ? (
          <div className="space-y-3">
            {ledger.history.map((entry) => (
              <div
                key={entry.jobId}
                className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm dark:border-white/10 dark:bg-white/5 lg:flex-row lg:items-center lg:justify-between"
              >
                <div>
                  <p className="font-medium">{entry.filename}</p>
                  <p className="mt-1 text-slate-600 dark:text-slate-300">
                    {humanizeImportType(entry.importType)} • {entry.appliedCount} rows applied
                  </p>
                </div>
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-brand-600)]">
                  {entry.confirmedAt.slice(0, 10)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <CardDescription>
            No confirmed imports yet. Start with one CSV or Excel export and the history
            ledger will appear here.
          </CardDescription>
        )}
      </Card>
    </div>
  );
}
