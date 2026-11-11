import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 px-6 py-12 text-center", className)}>
      <div className="grid h-11 w-11 place-items-center rounded-full bg-ink-800 text-accent-soft">
        <Icon className="h-5 w-5" aria-hidden />
      </div>
      <h3 className="text-base">{title}</h3>
      <p className="max-w-sm text-sm text-slate-400">{description}</p>
      {action}
    </div>
  );
}
