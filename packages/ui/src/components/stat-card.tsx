import { Card, CardDescription, CardHeader, CardTitle } from "./card";

export function StatCard({
  label,
  value,
  delta,
  tone = "neutral",
}: {
  label: string;
  value: string;
  delta: string;
  tone?: "positive" | "neutral" | "warning" | "critical";
}) {
  const toneClasses = {
    positive: "text-emerald-600 dark:text-emerald-300",
    neutral: "text-slate-600 dark:text-slate-300",
    warning: "text-amber-600 dark:text-amber-300",
    critical: "text-rose-600 dark:text-rose-300",
  };

  return (
    <Card className="min-h-36">
      <CardHeader className="mb-6 flex-col items-start">
        <CardDescription className="text-xs uppercase tracking-[0.2em]">
          {label}
        </CardDescription>
        <CardTitle className="text-3xl">{value}</CardTitle>
      </CardHeader>
      <p className={`text-sm font-medium ${toneClasses[tone]}`}>{delta}</p>
    </Card>
  );
}
