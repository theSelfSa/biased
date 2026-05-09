import { Card, CardDescription, CardTitle } from "@biased/ui";

import { ActionCenterManager } from "@/components/action-center-manager";
import { draftAction, getActionCenter } from "@/lib/api";

export default async function ActionsPage() {
  const actionCenter = await getActionCenter();
  const initialActionId = actionCenter.items[0]?.id;
  const initialDraft = initialActionId
    ? await draftAction(initialActionId)
    : null;

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">Action Center</CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          This is where insight becomes a human-approved next step: reorder
          plans, vendor follow-up drafts, bill warnings, and owner decisions
          with a clear open-watch-snooze-resolve workflow.
        </CardDescription>
      </Card>

      <ActionCenterManager
        initialDraft={initialDraft}
        initialSnapshot={actionCenter}
      />
    </div>
  );
}
