import Link from "next/link";

import { Button } from "@biased/ui";

export function AppShell({
  children,
  userLabel,
}: {
  children: React.ReactNode;
  userLabel: string;
}) {
  const links = [
    { href: "/dashboard", label: "Overview" },
    { href: "/imports", label: "Imports" },
    { href: "/documents", label: "Documents" },
    { href: "/actions", label: "Action Center" },
    { href: "/ask", label: "Ask B.I.A.S.E.D." },
  ];

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(8,145,178,0.14),_transparent_34%),linear-gradient(180deg,_#f3faf8_0%,_#f8fafc_44%,_#eff6ff_100%)] text-slate-950 dark:bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.14),_transparent_25%),linear-gradient(180deg,_#06101b_0%,_#08111d_100%)] dark:text-white">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-4 py-6 lg:flex-row lg:px-6">
        <aside className="flex flex-col justify-between rounded-[32px] border border-white/50 bg-white/85 p-5 shadow-[0_24px_80px_-40px_rgba(13,26,38,0.35)] backdrop-blur dark:border-white/10 dark:bg-[#09111d]/85 lg:w-80">
          <div className="space-y-8">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--color-brand-600)]">
                B.I.A.S.E.D.
              </p>
              <div>
                <h2 className="text-2xl font-semibold leading-tight">
                  Decision intelligence for owners who cannot afford blind spots.
                </h2>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  Built for smaller businesses that need the operating clarity large
                  companies already buy with bigger systems.
                </p>
              </div>
            </div>

            <nav className="space-y-2">
              {links.map((link) => (
                <Link
                  key={link.href}
                  className="flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-950 hover:text-white dark:text-slate-200 dark:hover:bg-white dark:hover:text-slate-950"
                  href={link.href}
                >
                  <span>{link.label}</span>
                  <span className="text-xs opacity-65">/</span>
                </Link>
              ))}
            </nav>
          </div>

          <div className="space-y-4 rounded-[24px] bg-slate-950 p-4 text-white dark:bg-white dark:text-slate-950">
            <p className="text-xs uppercase tracking-[0.24em] opacity-70">
              Active context
            </p>
            <div>
              <p className="text-base font-semibold">{userLabel}</p>
              <p className="text-sm opacity-80">India-first pharmacy demo workspace</p>
            </div>
            <Link href="/auth/sign-in">
              <Button className="w-full" variant="secondary">
                Switch account
              </Button>
            </Link>
          </div>
        </aside>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
