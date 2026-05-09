"use client";

import { useState, type FormEvent } from "react";

import { Button, Card, CardDescription, CardHeader, CardTitle } from "@biased/ui";
import type { ImportPreview } from "@biased/contracts";

import { appEnv } from "@/lib/env";

export function ImportUploader() {
  const [importType, setImportType] = useState("sales");
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [message, setMessage] = useState<string>("Upload a CSV or Excel file to generate a preview.");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const response = await fetch(`${appEnv.apiBaseUrl}/api/import-jobs`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      setMessage("Unable to preview this file right now.");
      return;
    }

    const payload = (await response.json()) as { preview: ImportPreview };
    setPreview(payload.preview);
    setMessage("Preview generated. Confirm mappings before import.");
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
            type="file"
          />
        </label>

        <Button type="submit">Generate preview</Button>
      </form>

      <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>

      {preview ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardTitle className="mb-4 text-base">Detected columns</CardTitle>
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
        </div>
      ) : null}
    </Card>
  );
}
