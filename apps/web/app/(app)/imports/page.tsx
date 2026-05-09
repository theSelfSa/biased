import { Card, CardDescription, CardTitle } from "@biased/ui";

import { ImportLedger } from "@/components/import-ledger";
import { ImportUploader } from "@/components/import-uploader";
import { getImportLedger } from "@/lib/api";

export default async function ImportsPage() {
  const ledger = await getImportLedger();

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-brand-600)]">
          Historical memory
        </p>
        <CardTitle className="text-3xl">
          Start with exports your business already has
        </CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          B.I.A.S.E.D. is designed for the real record trail owners already maintain:
          spreadsheet exports, purchase logs, utility bills, tax summaries, and recurring
          obligations that always come back.
        </CardDescription>
      </Card>

      <ImportUploader />
      <ImportLedger ledger={ledger} />
    </div>
  );
}
