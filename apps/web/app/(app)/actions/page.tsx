import { Card, CardDescription, CardTitle } from "@biased/ui";

import { draftAction, getActionCenter } from "@/lib/api";

function toneForSeverity(severity: "info" | "warning" | "critical") {
  switch (severity) {
    case "critical":
      return "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-200";
    case "warning":
      return "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-200";
    default:
      return "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200";
  }
}

export default async function ActionsPage() {
  const actionCenter = await getActionCenter();
  const featuredAction =
    actionCenter.items.find((item) => item.actionType === "vendor_follow_up") ??
    actionCenter.items[0];
  const draft = featuredAction ? await draftAction(featuredAction.id) : null;

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">Action Center</CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          This is where insight becomes a human-approved next step: reorder plans, vendor
          follow-up drafts, bill warnings, and operator decisions that an owner can take
          immediately.
        </CardDescription>
        <p className="text-sm text-slate-600 dark:text-slate-300">{actionCenter.headline}</p>
      </Card>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="space-y-4">
          <CardTitle>Queued actions</CardTitle>
          {actionCenter.items.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 dark:border-white/10 dark:bg-white/5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <p className="font-semibold">{item.title}</p>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${toneForSeverity(item.severity)}`}
                >
                  {item.severity}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {item.detail}
              </p>
              <p className="mt-3 text-xs uppercase tracking-[0.18em] text-[var(--color-brand-600)]">
                {item.actionType.replaceAll("_", " ")} • {item.status}
              </p>
            </div>
          ))}
        </Card>

        <Card className="space-y-4">
          <CardTitle>
            {featuredAction ? `Featured draft for ${featuredAction.targetEntity}` : "No action draft yet"}
          </CardTitle>
          {draft ? (
            <>
              <CardDescription>{draft.rationale}</CardDescription>
              <div className="rounded-[24px] bg-slate-950 p-5 text-sm leading-7 text-white dark:bg-white dark:text-slate-950">
                {draft.draftText}
              </div>
              <p className="text-xs uppercase tracking-[0.2em] text-[var(--color-brand-600)]">
                Approval required: {draft.approvalRequired ? "Yes" : "No"}
              </p>
            </>
          ) : (
            <CardDescription>
              The queue is empty right now. New action drafts will appear here as owner
              workflows and imported records build up.
            </CardDescription>
          )}
        </Card>
      </div>
    </div>
  );
}
