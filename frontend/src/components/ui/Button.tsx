import { Link, type LinkProps } from "react-router-dom";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type Variant = "primary" | "secondary" | "ghost";
const base =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
const variants: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent-dim shadow-glow",
  secondary: "border border-ink-600 bg-ink-800 text-slate-100 hover:bg-ink-700",
  ghost: "text-slate-300 hover:bg-ink-800 hover:text-white",
};

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={cn(base, variants[variant], className)} {...props} />;
}

export function ButtonLink({
  variant = "primary",
  className,
  ...props
}: LinkProps & { variant?: Variant }) {
  return <Link className={cn(base, variants[variant], className)} {...props} />;
}
