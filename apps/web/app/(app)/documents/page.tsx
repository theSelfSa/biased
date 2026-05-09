import { Card, CardDescription, CardTitle } from "@biased/ui";

import { getDocuments } from "@/lib/api";

export default async function DocumentsPage() {
  const documents = await getDocuments();

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">Business documents with context</CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          Bills, invoices, supplier notes, and tax-ready documents give B.I.A.S.E.D.
          richer context when it explains margin changes or cash pressure.
        </CardDescription>
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
