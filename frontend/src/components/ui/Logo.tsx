import { Music2 } from "lucide-react";
import { Link } from "react-router-dom";

export function Logo({ to = "/" }: { to?: string }) {
  return (
    <Link to={to} className="flex items-center gap-2 font-semibold text-slate-50">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent/20 text-accent-soft">
        <Music2 className="h-4 w-4" aria-hidden />
      </span>
      KeyChord <span className="text-accent-soft">AI</span>
    </Link>
  );
}
