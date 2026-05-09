import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { draftAction, getDashboardSnapshot } from "@/lib/api";

export default async function ActionsPage() {
  const [dashboard, draft] = await Promise.all([
    getDashboardSnapshot(),
    draftAction("act-2"),
  ]);

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">Action Center</CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          This is where insight becomes a human-approved next step: reorder plans, vendor
          follow-up drafts, bill warnings, and operator decisions that an owner can take
          immediately.
        </CardDescription>
      </Card>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="space-y-4">
          <CardTitle>Queued actions</CardTitle>
          {dashboard.actionQueue.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 dark:border-white/10 dark:bg-white/5"
            >
              <p className="font-semibold">{item.title}</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {item.detail}
              </p>
              <div className="mt-4 flex gap-3">
                <Button className="h-10 px-4 text-xs">Approve draft</Button>
                <Button className="h-10 px-4 text-xs" variant="ghost">
                  Snooze
                </Button>
              </div>
            </div>
          ))}
        </Card>

        <Card className="space-y-4">
          <CardTitle>Suggested vendor message</CardTitle>
          <CardDescription>{draft.rationale}</CardDescription>
          <div className="rounded-[24px] bg-slate-950 p-5 text-sm leading-7 text-white dark:bg-white dark:text-slate-950">
            {draft.draftText}
          </div>
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-brand-600)]">
            Approval required: {draft.approvalRequired ? "Yes" : "No"}
          </p>
        </Card>
      </div>
    </div>
  );
}
