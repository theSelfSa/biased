import { Card, CardDescription, CardTitle } from "@biased/ui";

import { ImportUploader } from "@/components/import-uploader";

export default function ImportsPage() {
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
    </div>
  );
}
