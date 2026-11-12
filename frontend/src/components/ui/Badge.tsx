import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

const tones = { neutral: "border-line text-mutedfg", ok: "border-accent text-accent", warn: "border-fg/40 text-fg", bad: "border-fg text-fg" };

export function Badge({ tone = "neutral", children }: { tone?: keyof typeof tones; children: ReactNode }) {
  return <span className={cn("inline-flex items-center rounded-sm border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.16em]", tones[tone])}>{children}</span>;
}
