"use client";

import { useMemo, useState, useTransition } from "react";

import { useRouter } from "next/navigation";

import type { ModelProfile, ModelProviderMode } from "@biased/contracts";
import { Button, Card, CardDescription, CardTitle } from "@biased/ui";

import { saveModelProviderSettings } from "@/lib/api";

function parseProviders(input: string): string[] {
  const values = input
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter(Boolean);
  return Array.from(new Set(values));
}

export function ModelProviderSettings({
  initialProfile,
}: {
  initialProfile: ModelProfile;
}) {
  const router = useRouter();
  const [isRefreshing, startTransition] = useTransition();
  const [mode, setMode] = useState<ModelProviderMode>(initialProfile.mode);
  const [providers, setProviders] = useState(
    initialProfile.providers.join(", "),
  );
  const [updatedAt, setUpdatedAt] = useState(initialProfile.updatedAt);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const providerCount = useMemo(
    () => parseProviders(providers).length,
    [providers],
  );

  async function handleSave() {
    setSaving(true);
    setMessage(null);

    const response = await saveModelProviderSettings({
      mode,
      providers: parseProviders(providers),
    });

    if (!response.saved) {
      setMessage("Unable to save model settings right now.");
      setSaving(false);
      return;
    }

    setMessage(
      `Saved ${response.profile.mode} mode with ${response.profile.providers.length} provider(s).`,
    );
    setUpdatedAt(response.profile.updatedAt);
    setSaving(false);
    startTransition(() => router.refresh());
  }

  return (
    <Card className="space-y-4">
      <div>
        <CardTitle>Model routing mode</CardTitle>
        <CardDescription className="mt-2 leading-7">
          Choose how B.I.A.S.E.D. resolves AI calls: local-only, cloud-only, or
          hybrid fallback.
        </CardDescription>
      </div>

      <div className="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
        <label className="space-y-2">
          <span className="text-sm font-medium">Runtime mode</span>
          <select
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) =>
              setMode(event.target.value as ModelProviderMode)
            }
            value={mode}
          >
            <option value="local-open">local-open (Ollama first)</option>
            <option value="byo-cloud">byo-cloud (provider keys only)</option>
            <option value="hybrid">hybrid (local first, cloud fallback)</option>
          </select>
        </label>

        <label className="space-y-2">
          <span className="text-sm font-medium">
            Provider priority (comma-separated)
          </span>
          <input
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-[#08111c]"
            onChange={(event) => setProviders(event.target.value)}
            placeholder="openrouter, openai, anthropic"
            value={providers}
          />
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Parsed providers: {providerCount}
          </p>
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button disabled={saving || isRefreshing} onClick={handleSave}>
          {saving ? "Saving..." : "Save model settings"}
        </Button>
        <p className="text-xs uppercase tracking-[0.18em] text-[var(--color-brand-600)]">
          Last updated: {updatedAt.slice(0, 19).replace("T", " ")}
        </p>
      </div>

      {message ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>
      ) : null}
    </Card>
  );
}
