import { Card, CardDescription, CardHeader, CardTitle, StatCard } from "@biased/ui";

import { CreateWorkspaceForm } from "@/components/create-workspace-form";
import { MarginChart } from "@/components/margin-chart";
import { getDashboardSnapshot, getMorningBrief } from "@/lib/api";
import { getSession } from "@/lib/session";

export default async function DashboardPage() {
  const [dashboard, brief, session] = await Promise.all([
    getDashboardSnapshot(),
    getMorningBrief(),
    getSession(),
  ]);

  return (
    <div className="space-y-6">
      <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="overflow-hidden">
          <CardHeader className="flex-col items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-brand-600)]">
                Demo workspace
              </p>
              <CardTitle className="mt-2 text-4xl">{dashboard.workspaceName}</CardTitle>
              <CardDescription className="mt-3 max-w-2xl text-base leading-7">
                {dashboard.subtitle}
              </CardDescription>
            </div>
          </CardHeader>
        </Card>

        {session?.user ? (
          <Card className="space-y-4">
            <CardTitle className="text-2xl">Signed in as {session.user.email}</CardTitle>
            <CardDescription className="leading-7">
              Auth is live. You can create a fresh business workspace or keep using the
              seeded pharmacy demo while the rest of the platform comes online.
            </CardDescription>
          </Card>
        ) : (
          <CreateWorkspaceForm />
        )}
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {dashboard.stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader className="flex-col items-start">
            <CardTitle>Revenue and margin trajectory</CardTitle>
            <CardDescription>
              A quick read on whether growth is translating into healthy cash and margin.
            </CardDescription>
          </CardHeader>
          <MarginChart data={dashboard.marginSeries} />
        </Card>

        <Card className="space-y-4">
          <CardTitle>Morning brief</CardTitle>
          <CardDescription>{brief.headline}</CardDescription>
          <ul className="space-y-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
            {brief.items.map((item) => (
              <li key={item} className="rounded-2xl bg-slate-100 px-4 py-3 dark:bg-white/5">
                {item}
              </li>
            ))}
          </ul>
        </Card>
      </section>

      <section className="grid gap-5 xl:grid-cols-3">
        <Card className="space-y-4">
          <CardTitle>Recurring bills coming due</CardTitle>
          <ul className="space-y-3 text-sm">
            {dashboard.obligations.map((item) => (
              <li
                key={item.id}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{item.label}</span>
                  <span>₹{item.amountInr.toLocaleString("en-IN")}</span>
                </div>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {item.dueDate} • {item.recurrence}
                </p>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="space-y-4">
          <CardTitle>Inventory alerts</CardTitle>
          <ul className="space-y-3 text-sm">
            {dashboard.inventoryAlerts.map((alert) => (
              <li
                key={alert.id}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                <p className="font-medium">{alert.title}</p>
                <p className="mt-1 text-slate-600 dark:text-slate-300">{alert.detail}</p>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="space-y-4">
          <CardTitle>Action queue</CardTitle>
          <ul className="space-y-3 text-sm">
            {dashboard.actionQueue.map((item) => (
              <li
                key={item.id}
                className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-white/10 dark:bg-white/5"
              >
                <p className="font-medium">{item.title}</p>
                <p className="mt-1 text-slate-600 dark:text-slate-300">{item.detail}</p>
              </li>
            ))}
          </ul>
        </Card>
      </section>
    </div>
  );
}
