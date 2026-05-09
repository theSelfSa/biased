"use client";

import { useState, useTransition, type FormEvent } from "react";

import { useRouter } from "next/navigation";

import {
  type BusinessDocument,
  type DocumentUploadResponse,
} from "@biased/contracts";
import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { appEnv } from "@/lib/env";

export function DocumentsWorkspace({
  initialDocuments,
}: {
  initialDocuments: BusinessDocument[];
}) {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [documents, setDocuments] = useState(initialDocuments);
  const [message, setMessage] = useState<string | null>(null);
  const [kind, setKind] = useState("invoice");
  const [isUploading, setIsUploading] = useState(false);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    formData.set("kind", kind);

    setIsUploading(true);
    setMessage(null);

    const response = await fetch(`${appEnv.apiBaseUrl}/api/documents`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      setMessage("Unable to store that document right now.");
      setIsUploading(false);
      return;
    }

    const document = (await response.json()) as DocumentUploadResponse;
    setDocuments((current) => [document, ...current]);
    setMessage("Document stored. It will now be available for future investigations.");
    form.reset();
    setIsUploading(false);
    startTransition(() => router.refresh());
  }

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div className="flex flex-col gap-2">
          <CardTitle>Upload a bill, invoice, or owner note</CardTitle>
          <CardDescription className="max-w-3xl leading-7">
            Give B.I.A.S.E.D. the business context behind the numbers so retrieval and
            investigations can explain what changed, not just what moved.
          </CardDescription>
        </div>

        <form
          className="grid gap-4 rounded-[24px] border border-dashed border-slate-300 bg-white/80 p-5 md:grid-cols-[0.95fr_1.05fr_auto] dark:border-white/15 dark:bg-white/5"
          onSubmit={handleUpload}
        >
          <label className="block space-y-2">
            <span className="text-sm font-medium">Document type</span>
            <select
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
              name="kind"
              onChange={(event) => setKind(event.target.value)}
              value={kind}
            >
              <option value="invoice">Invoice</option>
              <option value="utility">Utility bill</option>
              <option value="supplier_note">Supplier note</option>
              <option value="tax_summary">Tax summary</option>
              <option value="owner_note">Owner note</option>
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

          <div className="flex items-end">
            <Button className="w-full md:w-auto" disabled={isUploading || isRefreshing} type="submit">
              {isUploading ? "Uploading..." : "Store document"}
            </Button>
          </div>
        </form>

        {message ? (
          <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>
        ) : null}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        {documents.map((document) => (
          <Card key={document.id}>
            <CardTitle>{document.title}</CardTitle>
            <CardDescription className="mt-3 leading-7">
              {document.summary}
            </CardDescription>
            <p className="mt-4 text-xs uppercase tracking-[0.2em] text-[var(--color-brand-600)]">
              {document.kind} • uploaded {document.uploadedAt}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
