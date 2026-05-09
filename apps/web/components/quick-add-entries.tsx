"use client";

import { useState, useTransition, type FormEvent } from "react";

import { useRouter } from "next/navigation";

import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { appEnv } from "@/lib/env";

const today = new Date().toISOString().slice(0, 10);

export function QuickAddEntries() {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);
  const [sale, setSale] = useState({
    date: today,
    sku: "",
    name: "",
    category: "General",
    quantity: 1,
    amountInr: 0,
    marginPct: 0,
  });
  const [purchase, setPurchase] = useState({
    date: today,
    supplierName: "",
    sku: "",
    quantity: 1,
    amountInr: 0,
  });
  const [expense, setExpense] = useState({
    occurredOn: today,
    label: "",
    category: "Operations",
    amountInr: 0,
  });
  const [busy, setBusy] = useState<"sale" | "purchase" | "expense" | null>(null);

  async function submitQuickAdd(
    event: FormEvent<HTMLFormElement>,
    endpoint: string,
    payload: Record<string, unknown>,
    doneMessage: string,
    form: "sale" | "purchase" | "expense",
  ) {
    event.preventDefault();
    setBusy(form);
    setMessage(null);

    const response = await fetch(`${appEnv.apiBaseUrl}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      setMessage("Unable to save this quick entry right now.");
      setBusy(null);
      return;
    }

    setMessage(doneMessage);
    setBusy(null);
    startTransition(() => router.refresh());
  }

  return (
    <Card className="space-y-5">
      <div className="space-y-2">
        <CardTitle>Quick add daily records</CardTitle>
        <CardDescription>
          Owners can capture sales, purchases, and expenses in seconds so decisions stay
          grounded in today&apos;s real numbers.
        </CardDescription>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <form
          className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
          onSubmit={(event) =>
            submitQuickAdd(
              event,
              "/api/quick-add/sales",
              {
                ...sale,
                amountInr: Number(sale.amountInr),
                quantity: Number(sale.quantity),
                marginPct: Number(sale.marginPct),
              },
              "Sale entry saved.",
              "sale",
            )
          }
        >
          <p className="text-sm font-semibold">Quick sale</p>
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setSale((current) => ({ ...current, date: event.target.value }))}
            required
            type="date"
            value={sale.date}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setSale((current) => ({ ...current, sku: event.target.value }))}
            placeholder="SKU"
            required
            value={sale.sku}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setSale((current) => ({ ...current, name: event.target.value }))}
            placeholder="Product name (optional)"
            value={sale.name}
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
              min={1}
              onChange={(event) =>
                setSale((current) => ({ ...current, quantity: Number(event.target.value) }))
              }
              required
              type="number"
              value={sale.quantity}
            />
            <input
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
              min={0}
              onChange={(event) =>
                setSale((current) => ({ ...current, amountInr: Number(event.target.value) }))
              }
              required
              step="0.01"
              type="number"
              value={sale.amountInr || ""}
            />
          </div>
          <Button
            className="h-9 px-4 text-xs"
            disabled={busy === "sale" || isRefreshing}
            type="submit"
            variant="ghost"
          >
            {busy === "sale" ? "Saving..." : "Add sale"}
          </Button>
        </form>

        <form
          className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
          onSubmit={(event) =>
            submitQuickAdd(
              event,
              "/api/quick-add/purchases",
              {
                ...purchase,
                amountInr: Number(purchase.amountInr),
                quantity: Number(purchase.quantity),
              },
              "Purchase entry saved.",
              "purchase",
            )
          }
        >
          <p className="text-sm font-semibold">Quick purchase</p>
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) =>
              setPurchase((current) => ({ ...current, date: event.target.value }))
            }
            required
            type="date"
            value={purchase.date}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) =>
              setPurchase((current) => ({ ...current, supplierName: event.target.value }))
            }
            placeholder="Supplier name"
            required
            value={purchase.supplierName}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setPurchase((current) => ({ ...current, sku: event.target.value }))}
            placeholder="SKU"
            required
            value={purchase.sku}
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
              min={1}
              onChange={(event) =>
                setPurchase((current) => ({
                  ...current,
                  quantity: Number(event.target.value),
                }))
              }
              required
              type="number"
              value={purchase.quantity}
            />
            <input
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
              min={0}
              onChange={(event) =>
                setPurchase((current) => ({
                  ...current,
                  amountInr: Number(event.target.value),
                }))
              }
              required
              step="0.01"
              type="number"
              value={purchase.amountInr || ""}
            />
          </div>
          <Button
            className="h-9 px-4 text-xs"
            disabled={busy === "purchase" || isRefreshing}
            type="submit"
            variant="ghost"
          >
            {busy === "purchase" ? "Saving..." : "Add purchase"}
          </Button>
        </form>

        <form
          className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
          onSubmit={(event) =>
            submitQuickAdd(
              event,
              "/api/quick-add/expenses",
              {
                ...expense,
                amountInr: Number(expense.amountInr),
              },
              "Expense entry saved.",
              "expense",
            )
          }
        >
          <p className="text-sm font-semibold">Quick expense</p>
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) =>
              setExpense((current) => ({ ...current, occurredOn: event.target.value }))
            }
            required
            type="date"
            value={expense.occurredOn}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setExpense((current) => ({ ...current, label: event.target.value }))}
            placeholder="Expense label"
            required
            value={expense.label}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) =>
              setExpense((current) => ({ ...current, category: event.target.value }))
            }
            placeholder="Category"
            required
            value={expense.category}
          />
          <input
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-[#08111c]"
            min={0}
            onChange={(event) =>
              setExpense((current) => ({ ...current, amountInr: Number(event.target.value) }))
            }
            required
            step="0.01"
            type="number"
            value={expense.amountInr || ""}
          />
          <Button
            className="h-9 px-4 text-xs"
            disabled={busy === "expense" || isRefreshing}
            type="submit"
            variant="ghost"
          >
            {busy === "expense" ? "Saving..." : "Add expense"}
          </Button>
        </form>
      </div>

      {message ? <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p> : null}
    </Card>
  );
}
