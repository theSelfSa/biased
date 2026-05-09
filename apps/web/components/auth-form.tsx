"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@biased/ui";

import { authClient } from "@/lib/auth-client";

const schema = z.object({
  name: z.string().optional(),
  email: z.email(),
  password: z.string().min(8),
});

type AuthInput = z.infer<typeof schema>;

export function AuthForm({ mode }: { mode: "sign-in" | "sign-up" }) {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const form = useForm<AuthInput>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", name: "" },
  });

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    setSuccess(null);

    const result =
      mode === "sign-in"
        ? await authClient.signIn.email({
            email: values.email,
            password: values.password,
            callbackURL: "/dashboard",
          })
        : await authClient.signUp.email({
            email: values.email,
            password: values.password,
            name: values.name || "Owner",
            callbackURL: "/dashboard",
          });

    if (result.error) {
      setError(result.error.message ?? "Authentication failed.");
      return;
    }

    setSuccess("Success. Redirecting to your workspace...");
  });

  return (
    <form className="space-y-4" onSubmit={onSubmit}>
      {mode === "sign-up" ? (
        <label className="block space-y-2">
          <span className="text-sm font-medium">Name</span>
          <input
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-[var(--color-brand-500)] dark:border-white/10 dark:bg-white/5"
            placeholder="Akash Kore"
            {...form.register("name")}
          />
        </label>
      ) : null}

      <label className="block space-y-2">
        <span className="text-sm font-medium">Email</span>
        <input
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-[var(--color-brand-500)] dark:border-white/10 dark:bg-white/5"
          placeholder="owner@pharmacy.in"
          {...form.register("email")}
        />
      </label>

      <label className="block space-y-2">
        <span className="text-sm font-medium">Password</span>
        <input
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-[var(--color-brand-500)] dark:border-white/10 dark:bg-white/5"
          type="password"
          placeholder="At least 8 characters"
          {...form.register("password")}
        />
      </label>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {success ? <p className="text-sm text-emerald-600">{success}</p> : null}

      <Button className="w-full" type="submit">
        {mode === "sign-in" ? "Sign in" : "Create account"}
      </Button>
    </form>
  );
}
