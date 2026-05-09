"use client";

import { useMemo, useState, useTransition } from "react";

import { useRouter } from "next/navigation";

import type {
  ActionCenterItem,
  ActionCenterSnapshot,
  ActionDraft,
} from "@biased/contracts";
import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { draftAction, updateActionStatus } from "@/lib/api";

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

function patchActionItem(
  current: ActionCenterSnapshot,
  next: ActionCenterItem,
): ActionCenterSnapshot {
  return {
    ...current,
    items: current.items.map((item) => (item.id === next.id ? next : item)),
  };
}

const defaultSnoozeDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)
  .toISOString()
  .slice(0, 10);

export function ActionCenterManager({
  initialSnapshot,
  initialDraft,
}: {
  initialSnapshot: ActionCenterSnapshot;
  initialDraft: ActionDraft | null;
}) {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [selectedId, setSelectedId] = useState(
    initialSnapshot.items[0]?.id ?? "",
  );
  const [draft, setDraft] = useState<ActionDraft | null>(initialDraft);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [snoozeUntil, setSnoozeUntil] = useState(defaultSnoozeDate);
  const [resolutionNote, setResolutionNote] = useState("");

  const selected = useMemo(
    () =>
      snapshot.items.find((item) => item.id === selectedId) ??
      snapshot.items[0],
    [selectedId, snapshot.items],
  );
  async function handleSelect(nextActionId: string) {
    setSelectedId(nextActionId);
    setLoadingDraft(true);
    const nextDraft = await draftAction(nextActionId);
    setDraft(nextDraft);
    setLoadingDraft(false);
  }

  async function setStatus(
    status: "open" | "watching" | "snoozed" | "resolved",
  ) {
    if (!selected) {
      return;
    }

    setMessage(null);
    const response = await updateActionStatus(selected.id, {
      status,
      snoozeUntil: status === "snoozed" ? snoozeUntil : undefined,
      resolutionNote:
        status === "resolved" ? resolutionNote.trim() || undefined : undefined,
    });

    if (!response.updated) {
      setMessage("Could not update action status.");
      return;
    }

    setSnapshot((current) => patchActionItem(current, response.item));
    setMessage(`Status updated to ${response.item.status}.`);
    startTransition(() => router.refresh());
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <Card className="space-y-4">
        <CardTitle>Queued actions</CardTitle>
        <CardDescription>{snapshot.headline}</CardDescription>

        {snapshot.items.map((item) => (
          <button
            key={item.id}
            className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
              selected?.id === item.id
                ? "border-[var(--color-brand-500)] bg-[var(--color-brand-50)] dark:bg-[var(--color-brand-600)]/10"
                : "border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-white/5"
            }`}
            onClick={() => handleSelect(item.id)}
            type="button"
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
          </button>
        ))}
      </Card>

      <Card className="space-y-4">
        <CardTitle>
          {selected
            ? `Action controls for ${selected.targetEntity}`
            : "No action selected"}
        </CardTitle>

        {selected ? (
          <>
            <CardDescription>{selected.detail}</CardDescription>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={isRefreshing}
                onClick={() => setStatus("open")}
                variant="ghost"
              >
                Set open
              </Button>
              <Button
                disabled={isRefreshing}
                onClick={() => setStatus("watching")}
                variant="ghost"
              >
                Set watching
              </Button>
              <Button
                disabled={isRefreshing}
                onClick={() => setStatus("snoozed")}
                variant="ghost"
              >
                Snooze
              </Button>
              <Button
                disabled={isRefreshing}
                onClick={() => setStatus("resolved")}
                variant="ghost"
              >
                Resolve
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium">Snooze until</span>
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
                  onChange={(event) => setSnoozeUntil(event.target.value)}
                  type="date"
                  value={snoozeUntil}
                />
              </label>

              <label className="space-y-2">
                <span className="text-sm font-medium">Resolution note</span>
                <input
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
                  onChange={(event) => setResolutionNote(event.target.value)}
                  placeholder="What did the owner decide?"
                  value={resolutionNote}
                />
              </label>
            </div>

            {loadingDraft ? (
              <CardDescription>Preparing action draft...</CardDescription>
            ) : draft ? (
              <div className="space-y-3 rounded-[24px] bg-slate-950 p-5 text-sm leading-7 text-white dark:bg-white dark:text-slate-950">
                <p className="font-semibold">{draft.rationale}</p>
                <p>{draft.draftText}</p>
                <p className="text-xs uppercase tracking-[0.18em] opacity-80">
                  Approval required: {draft.approvalRequired ? "Yes" : "No"}
                </p>
              </div>
            ) : (
              <CardDescription>
                No draft is available for this action right now.
              </CardDescription>
            )}
          </>
        ) : (
          <CardDescription>
            The queue is empty right now. New action recommendations will appear
            as business data changes.
          </CardDescription>
        )}

        {message ? (
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {message}
          </p>
        ) : null}
      </Card>
    </div>
  );
}
