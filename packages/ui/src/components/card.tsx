import type { HTMLAttributes, PropsWithChildren } from "react";

import { cn } from "../lib/cn";

export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[28px] border border-white/40 bg-white/90 p-6 shadow-[0_24px_80px_-40px_rgba(13,26,38,0.35)] backdrop-blur dark:border-white/10 dark:bg-[#09111d]/85",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return <div className={cn("mb-4 flex items-start justify-between gap-4", className)}>{children}</div>;
}

export function CardTitle({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return <h3 className={cn("text-lg font-semibold tracking-tight", className)}>{children}</h3>;
}

export function CardDescription({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return <p className={cn("text-sm text-slate-600 dark:text-slate-300", className)}>{children}</p>;
}
