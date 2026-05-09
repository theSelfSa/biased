"use client";

import { useState } from "react";

import { Button } from "@biased/ui";

export function CreateWorkspaceForm() {
  const [name, setName] = useState("Swasthya Care Pharmacy");
  const [message, setMessage] = useState<string | null>(null);

  async function handleCreate() {
    const response = await fetch("/api/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, slug: name.toLowerCase().replace(/\s+/g, "-") }),
    });

    const payload = (await response.json()) as { message?: string };
    setMessage(payload.message ?? "Workspace created.");
  }

  return (
    <div className="space-y-4 rounded-[28px] border border-white/40 bg-white/80 p-6 dark:border-white/10 dark:bg-white/5">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--color-brand-600)]">
          Create your business workspace
        </p>
        <h3 className="mt-2 text-2xl font-semibold">Start with a real owner context</h3>
      </div>
      <input
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-[var(--color-brand-500)] dark:border-white/10 dark:bg-[#08111c]"
        onChange={(event) => setName(event.target.value)}
        value={name}
      />
      <Button onClick={handleCreate}>Create workspace</Button>
      {message ? <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p> : null}
    </div>
  );
}
