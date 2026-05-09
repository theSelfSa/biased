"use client";

import { useSyncExternalStore } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const subscribe = () => () => {};

export function MarginChart({
  data,
}: {
  data: { label: string; revenueInr: number; marginPct: number }[];
}) {
  const mounted = useSyncExternalStore(subscribe, () => true, () => false);

  if (!mounted) {
    return <div className="h-72 w-full rounded-[24px] bg-slate-100/80 dark:bg-white/5" />;
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="revenueGradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#0f766e" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#0f766e" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
          <XAxis dataKey="label" stroke="currentColor" fontSize={12} />
          <YAxis yAxisId="left" stroke="currentColor" fontSize={12} />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="currentColor"
            fontSize={12}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 18,
              border: "1px solid rgba(148,163,184,0.2)",
              background: "rgba(2, 6, 23, 0.92)",
              color: "#fff",
            }}
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="revenueInr"
            stroke="#0f766e"
            fill="url(#revenueGradient)"
            strokeWidth={3}
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="marginPct"
            stroke="#f97316"
            fill="transparent"
            strokeWidth={3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
