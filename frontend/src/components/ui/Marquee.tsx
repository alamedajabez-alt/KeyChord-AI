import type { ReactNode } from "react";

// Pure-CSS endless marquee (no dependency, no pause-on-hover, no edge fade).
export function Marquee({ children, speed = 30, className = "" }: { children: ReactNode; speed?: number; className?: string }) {
  return (
    <div className={`overflow-hidden ${className}`}>
      <div className="marquee-track" style={{ ["--mq-speed" as string]: `${speed}s` }}>
        <div className="flex shrink-0 items-center">{children}</div>
        <div className="flex shrink-0 items-center" aria-hidden>{children}</div>
      </div>
    </div>
  );
}
