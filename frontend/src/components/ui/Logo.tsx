import { Link } from "react-router-dom";

// Wordmark framed by two corner brackets
export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="relative inline-block px-2.5 py-1.5 leading-[1.05] text-fg" aria-label="KeyChord AI home">
      <span aria-hidden className="absolute left-0 top-0 h-2 w-2 border-l border-t border-fg/70" />
      <span aria-hidden className="absolute bottom-0 right-0 h-2 w-2 border-b border-r border-fg/70" />
      <span className="block text-lg font-medium tracking-tight" style={{ fontStretch: "125%" }}>KeyChord</span>
      <span className="block text-[10px] tracking-[0.3em] text-mutedfg">AI</span>
    </Link>
  );
}
