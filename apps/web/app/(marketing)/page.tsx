import Link from "next/link";

import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

export default function MarketingPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.24),_transparent_30%),linear-gradient(180deg,_#f1f9f6_0%,_#eef6ff_46%,_#f8fafc_100%)] px-4 py-6 text-slate-950 dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_28%),linear-gradient(180deg,_#06101b_0%,_#08111d_100%)] dark:text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <header className="flex flex-col gap-4 rounded-[36px] border border-white/45 bg-white/75 p-6 shadow-[0_24px_80px_-40px_rgba(13,26,38,0.35)] backdrop-blur dark:border-white/10 dark:bg-white/5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-[var(--color-brand-600)]">
              B.I.A.S.E.D.
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight lg:text-6xl">
              The AI advantage is biased toward big companies. This product is built
              to tilt it back.
            </h1>
            <p className="mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
              Import historical records, understand recurring obligations, investigate
              cash and margin changes, and act on recommendations built for real
              owner workflows.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Link href="/dashboard">
              <Button>Open the demo workspace</Button>
            </Link>
            <Link href="/auth/sign-up">
              <Button variant="secondary">Create your account</Button>
            </Link>
          </div>
        </header>

        <section className="grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">
          <Card className="overflow-hidden">
            <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
              <div className="space-y-4">
                <CardDescription className="text-xs uppercase tracking-[0.24em]">
                  Flagship open-source build
                </CardDescription>
                <CardTitle className="text-3xl">
                  India-first pharmacy demo, reusable SMB core, and a real AI product
                  story.
                </CardTitle>
                <p className="text-sm leading-7 text-slate-600 dark:text-slate-300">
                  B.I.A.S.E.D. is not a generic dashboard. It combines imports,
                  recurring bills, operational monitoring, document context, and
                  investigation workflows so a small business owner can ask one
                  question and get evidence-backed direction.
                </p>
              </div>
              <div className="rounded-[28px] bg-slate-950 p-5 text-white dark:bg-white dark:text-slate-950">
                <p className="text-xs uppercase tracking-[0.24em] opacity-70">
                  First showcase
                </p>
                <ul className="mt-4 space-y-3 text-sm leading-7">
                  <li>Import sales, purchases, products, expenses, and recurring bills</li>
                  <li>Track near-expiry stock and cash pressure</li>
                  <li>Ask “Why did profit drop this month?”</li>
                  <li>Receive evidence, confidence, and recommended action</li>
                </ul>
              </div>
            </div>
          </Card>

          <div className="grid gap-5">
            {[
              {
                title: "Owner-first UX",
                detail:
                  "Mobile-ready quick actions, dashboards that read like decisions, and no analyst jargon.",
              },
              {
                title: "Open-source path",
                detail:
                  "Run privately with Docker + Ollama or use hosted demo mode with your own model keys.",
              },
              {
                title: "Built in public",
                detail:
                  "Visible milestones across auth, imports, AI investigation, forecasting, and action workflows.",
              },
            ].map((item) => (
              <Card key={item.title}>
                <CardTitle className="text-xl">{item.title}</CardTitle>
                <CardDescription className="mt-3 leading-7">
                  {item.detail}
                </CardDescription>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
