import Link from "next/link";

import { Card, CardDescription, CardTitle } from "@biased/ui";

import { AuthForm } from "@/components/auth-form";

export default function SignUpPage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.24),_transparent_30%),linear-gradient(180deg,_#f1f9f6_0%,_#eef6ff_46%,_#f8fafc_100%)] px-4 py-10 dark:bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_28%),linear-gradient(180deg,_#06101b_0%,_#08111d_100%)]">
      <div className="mx-auto grid max-w-5xl gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--color-brand-600)]">
            Create account
          </p>
          <CardTitle className="text-4xl">Start building your business memory</CardTitle>
          <CardDescription className="leading-7">
            Create a personal owner account, then spin up your own workspace or keep
            the seeded pharmacy demo for deterministic demos and local testing.
          </CardDescription>
        </Card>

        <Card>
          <AuthForm mode="sign-up" />
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">
            Already have an account?{" "}
            <Link className="font-semibold text-[var(--color-brand-700)]" href="/auth/sign-in">
              Sign in here
            </Link>
            .
          </p>
        </Card>
      </div>
    </main>
  );
}
