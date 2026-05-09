"use client";

import { useState, useTransition, type FormEvent } from "react";

import { useRouter } from "next/navigation";

import { Button, Card, CardDescription, CardHeader, CardTitle } from "@biased/ui";
import type { ImportConfirmResponse, ImportPreview } from "@biased/contracts";

import { appEnv } from "@/lib/env";

export function ImportUploader() {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [importType, setImportType] = useState("sales");
  const [jobId, setJobId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [confirmation, setConfirmation] = useState<ImportConfirmResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [message, setMessage] = useState<string>("Upload a CSV or Excel file to generate a preview.");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setConfirmation(null);
    const formData = new FormData(event.currentTarget);
    const response = await fetch(`${appEnv.apiBaseUrl}/api/import-jobs`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      setMessage("Unable to preview this file right now.");
      setIsSubmitting(false);
      return;
    }

    const payload = (await response.json()) as { jobId: string; preview: ImportPreview };
    setJobId(payload.jobId);
    setPreview(payload.preview);
    setMessage("Preview generated. Confirm mappings before import.");
    setIsSubmitting(false);
  }

  async function handleConfirm() {
    if (!jobId) {
      return;
    }

    setIsConfirming(true);
    const response = await fetch(`${appEnv.apiBaseUrl}/api/import-jobs/${jobId}/confirm`, {
      method: "POST",
    });

    if (!response.ok) {
      setMessage("Unable to confirm this import right now.");
      setIsConfirming(false);
      return;
    }

    const payload = (await response.json()) as ImportConfirmResponse;
    setConfirmation(payload);

    if (payload.status === "confirmed") {
      setMessage(
        `Imported ${payload.appliedCount} rows into ${payload.affectedCollections.join(", ")}.`,
      );
      startTransition(() => router.refresh());
    } else if (payload.status === "already_confirmed") {
      setMessage("This import job was already applied earlier.");
    } else {
      setMessage("This import job could not be found.");
    }

    setIsConfirming(false);
  }

  return (
    <Card className="space-y-5">
      <CardHeader className="flex-col items-start">
        <div>
          <CardTitle>Import historical records</CardTitle>
          <CardDescription>
            Bring in exports from spreadsheets, accounting tools, or tax-ready ledgers.
          </CardDescription>
        </div>
      </CardHeader>

      <form
        className="space-y-4 rounded-[24px] border border-dashed border-slate-300 bg-white/80 p-5 dark:border-white/15 dark:bg-white/5"
        onSubmit={handleSubmit}
      >
        <label className="block space-y-2">
          <span className="text-sm font-medium">Import type</span>
          <select
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
            name="importType"
            onChange={(event) => setImportType(event.target.value)}
            value={importType}
          >
            <option value="sales">Sales export</option>
            <option value="purchases">Purchases export</option>
            <option value="products">Products and inventory</option>
            <option value="expenses">Expenses</option>
            <option value="recurring_obligations">Recurring obligations</option>
          </select>
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium">File</span>
          <input
            className="block w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
            name="file"
            required
            type="file"
          />
        </label>

        <Button disabled={isSubmitting || isRefreshing} type="submit">
          {isSubmitting ? "Generating preview..." : "Generate preview"}
        </Button>
      </form>

      <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>

      {preview ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle className="mb-2 text-base">Detected columns</CardTitle>
            <CardDescription className="mb-4">
              {preview.filename} • {preview.rowCount} rows detected
            </CardDescription>
            <ul className="space-y-2 text-sm">
              {preview.columns.map((column) => (
                <li key={column} className="rounded-2xl bg-slate-100 px-3 py-2 dark:bg-white/5">
                  {column}
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <CardTitle className="mb-4 text-base">Inferred mapping</CardTitle>
            <ul className="space-y-2 text-sm">
              {Object.entries(preview.inferredMappings).map(([source, target]) => (
                <li key={source} className="flex items-center justify-between rounded-2xl bg-slate-100 px-3 py-2 dark:bg-white/5">
                  <span>{source}</span>
                  <span className="font-medium text-[var(--color-brand-700)] dark:text-[var(--color-brand-200)]">
                    {target}
                  </span>
                </li>
              ))}
            </ul>
          </Card>

          <Card className="lg:col-span-2">
            <CardTitle className="mb-4 text-base">Import confirmation</CardTitle>
            {preview.warnings.length ? (
              <ul className="mb-4 space-y-2 text-sm text-amber-700 dark:text-amber-200">
                {preview.warnings.map((warning) => (
                  <li
                    key={warning}
                    className="rounded-2xl bg-amber-50 px-3 py-2 dark:bg-amber-500/10"
                  >
                    {warning}
                  </li>
                ))}
              </ul>
            ) : (
              <CardDescription className="mb-4">
                No validation warnings were detected in this preview.
              </CardDescription>
            )}

            <div className="flex flex-wrap items-center gap-3">
              <Button
                disabled={!jobId || isConfirming || isRefreshing}
                onClick={handleConfirm}
              >
                {isConfirming ? "Applying import..." : "Confirm and apply import"}
              </Button>

              {confirmation ? (
                <span className="text-sm text-slate-600 dark:text-slate-300">
                  Status: {confirmation.status}
                </span>
              ) : null}
            </div>

            {confirmation?.affectedCollections.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {confirmation.affectedCollections.map((collection) => (
                  <span
                    key={collection}
                    className="rounded-full bg-[var(--color-brand-100)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-brand-700)] dark:bg-[var(--color-brand-600)]/15 dark:text-[var(--color-brand-200)]"
                  >
                    {collection}
                  </span>
                ))}
              </div>
            ) : null}
          </Card>
        </div>
      ) : null}
    </Card>
  );
}
