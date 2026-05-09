import type {
  ActionDraft,
  ActionCenterSnapshot,
  BriefingResult,
  BusinessDocument,
  DashboardSnapshot,
  ExpenseEntry,
  ImportLedgerSnapshot,
  InvestigationResult,
  PurchaseTransaction,
  QuickAddExpenseInput,
  QuickAddPurchaseInput,
  QuickAddSaleInput,
  SalesTransaction,
} from "@biased/contracts";

import {
  fallbackActionCenter,
  fallbackBriefing,
  fallbackDashboard,
  fallbackDocuments,
  fallbackImportLedger,
  fallbackInvestigation,
} from "@/lib/fallback-data";

import { appEnv } from "@/lib/env";

async function safeJson<T>(path: string, fallback: T, init?: RequestInit) {
  try {
    const response = await fetch(`${appEnv.apiBaseUrl}${path}`, {
      ...init,
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });

    if (!response.ok) {
      return fallback;
    }

    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function getDashboardSnapshot() {
  return safeJson<DashboardSnapshot>("/api/dashboard", fallbackDashboard);
}

export function getDocuments() {
  return safeJson<BusinessDocument[]>("/api/documents", fallbackDocuments);
}

export function getImportLedger() {
  return safeJson<ImportLedgerSnapshot>("/api/import-records", fallbackImportLedger);
}

export function getMorningBrief() {
  return safeJson<BriefingResult>("/api/briefings/generate", fallbackBriefing, {
    method: "POST",
    body: JSON.stringify({ mode: "demo" }),
  });
}

export function runInvestigation(question: string) {
  return safeJson<InvestigationResult>(
    "/api/investigations",
    {
      ...fallbackInvestigation,
      question,
    },
    {
      method: "POST",
      body: JSON.stringify({ question }),
    },
  );
}

export function draftAction(actionId: string) {
  return safeJson<ActionDraft>(
    `/api/actions/${actionId}/draft`,
    {
      actionType: "vendor_follow_up",
      targetEntity: "Primary distributor",
      rationale: "Cash buffer is tight before the next weekend sales peak.",
      draftText:
        "Hello, I would like to split the next invoice into two settlement windows so I can rebalance our near-expiry stock first.",
      approvalRequired: true,
    },
    {
      method: "POST",
      body: JSON.stringify({ actionId }),
    },
  );
}

export function getActionCenter() {
  return safeJson<ActionCenterSnapshot>("/api/actions", fallbackActionCenter);
}

export function quickAddSale(payload: QuickAddSaleInput) {
  return safeJson<SalesTransaction>(
    "/api/quick-add/sales",
    {
      id: "fallback-sale",
      ...payload,
    },
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function quickAddPurchase(payload: QuickAddPurchaseInput) {
  return safeJson<PurchaseTransaction>(
    "/api/quick-add/purchases",
    {
      id: "fallback-purchase",
      ...payload,
    },
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function quickAddExpense(payload: QuickAddExpenseInput) {
  return safeJson<ExpenseEntry>(
    "/api/quick-add/expenses",
    {
      id: "fallback-expense",
      ...payload,
    },
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
