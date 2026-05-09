import { Card, CardDescription, CardTitle } from "@biased/ui";

import { InvestigationConsole } from "@/components/investigation-console";
import { ModelProviderSettings } from "@/components/model-provider-settings";
import { getModelProviderProfile } from "@/lib/api";

export default async function AskPage() {
  const profile = await getModelProviderProfile();

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">Ask B.I.A.S.E.D.</CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          This is the flagship AI surface: structured business data, recurring
          obligations, and supporting documents combined into a focused answer
          with evidence and recommendations.
        </CardDescription>
      </Card>

      <InvestigationConsole />
      <ModelProviderSettings initialProfile={profile} />
    </div>
  );
}
