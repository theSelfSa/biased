import { Card, CardDescription, CardTitle } from "@biased/ui";

import { DocumentsWorkspace } from "@/components/documents-workspace";
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

      <DocumentsWorkspace initialDocuments={documents} />
    </div>
  );
}
