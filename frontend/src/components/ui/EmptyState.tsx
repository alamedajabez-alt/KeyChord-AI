import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export function EmptyState({ icon: Icon, title, description, action, className }: {
  icon: LucideIcon; title: string; description: string; action?: ReactNode; className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-start justify-center gap-4 p-8 py-14 md:p-12", className)}>
      <div className="grid h-12 w-12 place-items-center border border-line text-accent"><Icon className="h-5 w-5" aria-hidden strokeWidth={1.5} /></div>
      <h3 className="text-2xl md:text-3xl">{title}</h3>
      <p className="max-w-md text-lg text-mutedfg">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
