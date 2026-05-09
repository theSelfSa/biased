"use client";

import { useState } from "react";

import type {
  ForecastResult,
  ScenarioPlannerRequest,
  ScenarioPlannerResult,
  SchedulerRunResult,
} from "@biased/contracts";
import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { runForecast, runScenario, runScheduler } from "@/lib/api";

const defaultScenario: ScenarioPlannerRequest = {
  scenarioType: "supplier_price_increase",
  horizonDays: 30,
  percentage: 10,
};

export function ForecastLab() {
  const [metric, setMetric] = useState("sales");
  const [horizon, setHorizon] = useState("30d");
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [scenarioInput, setScenarioInput] =
    useState<ScenarioPlannerRequest>(defaultScenario);
  const [scenario, setScenario] = useState<ScenarioPlannerResult | null>(null);
  const [schedulerRun, setSchedulerRun] = useState<SchedulerRunResult | null>(
    null,
  );
  const [loading, setLoading] = useState<
    "forecast" | "scenario" | "scheduler" | null
  >(null);

  async function handleForecast() {
    setLoading("forecast");
    const result = await runForecast(metric, horizon);
    setForecast(result);
    setLoading(null);
  }

  async function handleScenario() {
    setLoading("scenario");
    const result = await runScenario(scenarioInput);
    setScenario(result);
    setLoading(null);
  }

  async function handleScheduler() {
    setLoading("scheduler");
    const result = await runScheduler();
    setSchedulerRun(result);
    setLoading(null);
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="space-y-4">
          <CardTitle>Forecast studio</CardTitle>
          <CardDescription>
            Fast, explainable baselines for sales, purchases, recurring
            obligations, and simple cash projection.
          </CardDescription>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium">Metric</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) => setMetric(event.target.value)}
                value={metric}
              >
                <option value="sales">Sales</option>
                <option value="purchases">Purchases</option>
                <option value="recurring">Recurring expenses</option>
                <option value="cash">Cash projection</option>
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Horizon</span>
              <input
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) => setHorizon(event.target.value)}
                placeholder="30d"
                value={horizon}
              />
            </label>
          </div>

          <Button disabled={loading !== null} onClick={handleForecast}>
            {loading === "forecast" ? "Running forecast..." : "Run forecast"}
          </Button>

          {forecast ? (
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-white/10 dark:bg-white/5">
              <p className="font-semibold">
                {forecast.metric} • {forecast.horizon}
              </p>
              <p>{forecast.baseline}</p>
              <p className="text-[var(--color-brand-700)] dark:text-[var(--color-brand-200)]">
                {forecast.projectedRange}
              </p>
              <ul className="space-y-1 text-slate-600 dark:text-slate-300">
                {forecast.warnings.map((warning) => (
                  <li key={warning}>• {warning}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>

        <Card className="space-y-4">
          <CardTitle>Scenario planner</CardTitle>
          <CardDescription>
            Compare deterministic impact for supplier inflation, underperforming
            lines, delayed reorder, and rent/electricity changes.
          </CardDescription>

          <div className="grid gap-4 md:grid-cols-3">
            <label className="space-y-2 md:col-span-2">
              <span className="text-sm font-medium">Scenario</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                onChange={(event) =>
                  setScenarioInput((current) => ({
                    ...current,
                    scenarioType: event.target
                      .value as ScenarioPlannerRequest["scenarioType"],
                  }))
                }
                value={scenarioInput.scenarioType}
              >
                <option value="supplier_price_increase">
                  Supplier price increase
                </option>
                <option value="underperforming_product_line">
                  Underperforming product line
                </option>
                <option value="delayed_reorder">Delayed reorder</option>
                <option value="rent_electricity_increase">
                  Rent/electricity increase
                </option>
              </select>
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Horizon days</span>
              <input
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
                max={180}
                min={7}
                onChange={(event) =>
                  setScenarioInput((current) => ({
                    ...current,
                    horizonDays: Number(event.target.value),
                  }))
                }
                type="number"
                value={scenarioInput.horizonDays}
              />
            </label>
          </div>

          <label className="space-y-2">
            <span className="text-sm font-medium">Impact percentage</span>
            <input
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
              max={100}
              min={0}
              onChange={(event) =>
                setScenarioInput((current) => ({
                  ...current,
                  percentage: Number(event.target.value),
                }))
              }
              type="number"
              value={scenarioInput.percentage}
            />
          </label>

          <Button disabled={loading !== null} onClick={handleScenario}>
            {loading === "scenario" ? "Running scenario..." : "Run scenario"}
          </Button>

          {scenario ? (
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-white/10 dark:bg-white/5">
              <p className="font-semibold">{scenario.summary}</p>
              <ul className="space-y-2">
                {scenario.deltas.map((delta) => (
                  <li key={delta.metric}>
                    <p className="font-medium">{delta.metric}</p>
                    <p className="text-slate-600 dark:text-slate-300">
                      {delta.projected}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>
      </div>

      <Card className="space-y-4">
        <CardTitle>Scheduler run (daily brief + anomaly scan)</CardTitle>
        <CardDescription>
          Trigger the deterministic scheduler now to generate a morning brief id
          and reminder counts.
        </CardDescription>
        <Button disabled={loading !== null} onClick={handleScheduler}>
          {loading === "scheduler"
            ? "Running scheduler..."
            : "Run scheduler now"}
        </Button>
        {schedulerRun ? (
          <p className="text-sm text-slate-600 dark:text-slate-300">
            {schedulerRun.morningBriefId} • anomalies{" "}
            {schedulerRun.anomalyCount} • due reminders{" "}
            {schedulerRun.dueReminderCount} • generated{" "}
            {schedulerRun.generatedAt.slice(0, 19).replace("T", " ")}
          </p>
        ) : null}
      </Card>
    </div>
  );
}
