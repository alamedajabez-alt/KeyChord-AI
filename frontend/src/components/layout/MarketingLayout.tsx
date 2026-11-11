import { Outlet } from "react-router-dom";
import { ButtonLink } from "../ui/Button";
import { Logo } from "../ui/Logo";

export default function MarketingLayout() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Logo />
        <ButtonLink to="/dashboard" variant="secondary">Open app</ButtonLink>
      </header>
      <Outlet />
      <footer className="mx-auto max-w-6xl border-t border-ink-800 px-4 py-6 text-xs text-slate-500 sm:px-6">
        Chord detection is an estimate, not a perfect transcription. Only upload audio you have the right to use.
      </footer>
    </div>
  );
}
