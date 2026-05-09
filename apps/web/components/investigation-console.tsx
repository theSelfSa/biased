"use client";

import { useState } from "react";

import { Button, Card, CardDescription, CardTitle } from "@biased/ui";
import type { InvestigationResult } from "@biased/contracts";

import { appEnv } from "@/lib/env";
import { fallbackInvestigation } from "@/lib/fallback-data";

export function InvestigationConsole() {
  const [question, setQuestion] = useState("Why did profit drop this month?");
  const [result, setResult] = useState<InvestigationResult>(
    fallbackInvestigation,
  );
  const [loading, setLoading] = useState(false);

  async function handleRun() {
    setLoading(true);

    try {
      const response = await fetch(`${appEnv.apiBaseUrl}/api/investigations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (response.ok) {
        const nextResult = (await response.json()) as InvestigationResult;
        setResult(nextResult);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
      <Card className="space-y-4">
        <div>
          <CardTitle>Investigation mode</CardTitle>
          <CardDescription>
            Ask a business question and let B.I.A.S.E.D. combine transactions,
            obligations, and supporting documents into an answer.
          </CardDescription>
        </div>

        <textarea
          className="min-h-36 w-full rounded-[24px] border border-slate-200 bg-white px-4 py-4 outline-none focus:border-[var(--color-brand-500)] dark:border-white/10 dark:bg-white/5"
          onChange={(event) => setQuestion(event.target.value)}
          value={question}
        />

        <Button disabled={loading} onClick={handleRun}>
          {loading ? "Investigating..." : "Run investigation"}
        </Button>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs uppercase tracking-[0.16em] text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
          Provider: {result.provider ?? "local-open"} • Mode:{" "}
          {result.mode ?? "local-open"} • Latency: {result.latencyMs ?? 0}ms •
          Est. cost: ${(result.estimatedCostUsd ?? 0).toFixed(6)}
        </div>
      </Card>

      <Card className="space-y-4">
        <div>
          <CardTitle>{result.summary}</CardTitle>
          <CardDescription>
            Confidence {Math.round(result.confidence * 100)}%
          </CardDescription>
        </div>

        <div className="space-y-3">
          {result.evidence.map((item) => (
            <div
              key={item.label}
              className="rounded-[20px] border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
            >
              <p className="font-semibold">{item.label}</p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                {item.detail}
              </p>
              <p className="mt-2 text-xs uppercase tracking-[0.2em] text-[var(--color-brand-600)]">
                {item.source}
              </p>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <p className="text-sm font-semibold">Recommendations</p>
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
            {result.recommendations.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-white/5"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      </Card>
    </div>
  );
}
