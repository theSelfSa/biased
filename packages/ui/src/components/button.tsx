import type { ButtonHTMLAttributes } from "react";

import { cn } from "../lib/cn";

const variants = {
  primary:
    "bg-[var(--color-brand-600)] text-white shadow-lg shadow-[color:var(--color-brand-600)]/20 hover:bg-[var(--color-brand-500)]",
  secondary:
    "bg-white/10 text-[var(--color-ink-950)] hover:bg-white/20 dark:text-white",
  ghost:
    "bg-transparent text-[var(--color-brand-700)] hover:bg-[var(--color-brand-50)] dark:text-[var(--color-brand-200)] dark:hover:bg-white/10",
};

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-11 items-center justify-center rounded-full px-5 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand-400)] disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className,
      )}
      type={type}
      {...props}
    />
  );
}
