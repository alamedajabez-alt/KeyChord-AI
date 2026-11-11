import { History, LayoutDashboard, Menu, Settings, Upload, Piano, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { cn } from "../../lib/cn";
import { useApiStatus } from "../../lib/useApiStatus";
import { Badge } from "../ui/Badge";
import { Logo } from "../ui/Logo";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Upload", icon: Upload },
  { to: "/workspace", label: "Workspace", icon: Piano },
  { to: "/history", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function AppShell() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  const status = useApiStatus();
  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[220px_1fr]">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-56 border-r border-ink-800 bg-ink-900 p-4 transition-transform lg:static lg:w-auto lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="mb-6 flex items-center justify-between">
          <Logo to="/" />
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="space-y-1" aria-label="Main">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm",
                  isActive ? "bg-accent/15 text-accent-soft" : "text-slate-400 hover:bg-ink-800 hover:text-slate-100",
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      {open && <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setOpen(false)} aria-hidden />}

      <div className="min-w-0">
        <header className="flex items-center justify-between border-b border-ink-800 px-4 py-3 sm:px-6">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
          <span className="hidden lg:block" />
          <Badge tone={status === "online" ? "ok" : status === "offline" ? "warn" : "neutral"}>API {status}</Badge>
        </header>
        <main className="p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
