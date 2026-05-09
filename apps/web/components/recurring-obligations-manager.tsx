"use client";

import { useState, useTransition, type FormEvent } from "react";

import { useRouter } from "next/navigation";

import {
  type CreateRecurringObligationInput,
  type RecurringObligation,
} from "@biased/contracts";
import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { appEnv } from "@/lib/env";

const defaultDueDate = new Date().toISOString().slice(0, 10);

function sortObligations(items: RecurringObligation[]) {
  const order = { due: 0, scheduled: 1, paid: 2 };
  return [...items].sort((left, right) => {
    const leftOrder = order[left.status];
    const rightOrder = order[right.status];

    if (leftOrder !== rightOrder) {
      return leftOrder - rightOrder;
    }

    return left.dueDate.localeCompare(right.dueDate);
  });
}

function toneForStatus(status: RecurringObligation["status"]) {
  switch (status) {
    case "paid":
      return "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-200";
    case "due":
      return "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-200";
    default:
      return "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-200";
  }
}

export function RecurringObligationsManager({
  initialObligations,
}: {
  initialObligations: RecurringObligation[];
}) {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [obligations, setObligations] = useState(() => sortObligations(initialObligations));
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState<CreateRecurringObligationInput>({
    label: "",
    category: "Utilities",
    amountInr: 0,
    dueDate: defaultDueDate,
    recurrence: "monthly",
    status: "due",
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    const response = await fetch(`${appEnv.apiBaseUrl}/api/recurring-obligations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        amountInr: Number(form.amountInr),
      }),
    });

    if (!response.ok) {
      setMessage("Unable to save that recurring obligation right now.");
      setIsSubmitting(false);
      return;
    }

    const obligation = (await response.json()) as RecurringObligation;
    setObligations((current) => sortObligations([obligation, ...current]));
    setForm({
      label: "",
      category: form.category,
      amountInr: 0,
      dueDate: defaultDueDate,
      recurrence: form.recurrence,
      status: "due",
    });
    setMessage("Recurring obligation saved. Your owner dashboard has new context now.");
    setIsSubmitting(false);
    startTransition(() => router.refresh());
  }

  async function markPaid(obligationId: string) {
    setMessage(null);
    const response = await fetch(
      `${appEnv.apiBaseUrl}/api/recurring-obligations/${obligationId}/mark-paid`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "paid" }),
      },
    );

    if (!response.ok) {
      setMessage("Unable to update that bill status right now.");
      return;
    }

    const obligation = (await response.json()) as RecurringObligation;
    setObligations((current) =>
      sortObligations(
        current.map((item) => (item.id === obligation.id ? obligation : item)),
      ),
    );
    setMessage(`Marked ${obligation.label} as paid.`);
    startTransition(() => router.refresh());
  }

  return (
    <Card className="space-y-5">
      <div className="flex flex-col gap-2">
        <CardTitle>Recurring bills coming due</CardTitle>
        <CardDescription>
          Track rent, utilities, distributor settlements, and the operating costs that
          shape every owner decision.
        </CardDescription>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-3">
          {obligations.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 dark:border-white/10 dark:bg-white/5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{item.label}</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                    {item.category} • due {item.dueDate} • {item.recurrence}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${toneForStatus(item.status)}`}
                  >
                    {item.status}
                  </span>
                  <span className="text-sm font-semibold">
                    ₹{item.amountInr.toLocaleString("en-IN")}
                  </span>
                </div>
              </div>

              {item.status === "paid" ? null : (
                <div className="mt-4">
                  <Button
                    className="h-9 px-4 text-xs"
                    disabled={isRefreshing}
                    onClick={() => markPaid(item.id)}
                    variant="ghost"
                  >
                    Mark as paid
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>

        <form
          className="space-y-4 rounded-[24px] border border-dashed border-slate-300 bg-white/80 p-5 dark:border-white/15 dark:bg-white/5"
          onSubmit={handleSubmit}
        >
          <div>
            <h4 className="text-base font-semibold">Add a new recurring obligation</h4>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
              Useful for rent increases, maintenance contracts, internet, payroll, or
              any cost the owner needs visible before it bites cash flow.
            </p>
          </div>

          <label className="block space-y-2">
            <span className="text-sm font-medium">Label</span>
            <input
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
              onChange={(event) =>
                setForm((current) => ({ ...current, label: event.target.value }))
              }
              required
              value={form.label}
            />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block space-y-2">
              <span className="text-sm font-medium">Category</span>
              <input
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) =>
                  setForm((current) => ({ ...current, category: event.target.value }))
                }
                value={form.category}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium">Amount (INR)</span>
              <input
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                min="0"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    amountInr: Number(event.target.value),
                  }))
                }
                required
                step="0.01"
                type="number"
                value={form.amountInr || ""}
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="block space-y-2">
              <span className="text-sm font-medium">Due date</span>
              <input
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) =>
                  setForm((current) => ({ ...current, dueDate: event.target.value }))
                }
                required
                type="date"
                value={form.dueDate}
              />
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium">Recurrence</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    recurrence: event.target.value as CreateRecurringObligationInput["recurrence"],
                  }))
                }
                value={form.recurrence}
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="annual">Annual</option>
              </select>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-medium">Status</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    status: event.target.value as NonNullable<
                      CreateRecurringObligationInput["status"]
                    >,
                  }))
                }
                value={form.status}
              >
                <option value="due">Due</option>
                <option value="scheduled">Scheduled</option>
                <option value="paid">Paid</option>
              </select>
            </label>
          </div>

          <Button disabled={isSubmitting || isRefreshing} type="submit">
            {isSubmitting ? "Saving obligation..." : "Save recurring bill"}
          </Button>
        </form>
      </div>

      {message ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>
      ) : null}
    </Card>
  );
}
