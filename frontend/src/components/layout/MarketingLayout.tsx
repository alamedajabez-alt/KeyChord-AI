import { Link, Outlet } from "react-router-dom";
import { Logo } from "../ui/Logo";

const LINKS = [["Dashboard", "/dashboard"], ["Upload", "/upload"], ["Workspace", "/workspace"], ["History", "/history"]];

export default function MarketingLayout() {
  return (
    <div className="min-h-screen">
      <header className="absolute inset-x-0 top-0 z-20 flex items-center justify-between px-6 py-6 md:px-[4.5vw]">
        <Logo />
        <nav aria-label="Main" className="hidden gap-9 sm:flex">
          {LINKS.map(([l, to]) => <Link key={to} to={to} className="label !text-accent hover:!text-fg">{l}</Link>)}
        </nav>
        <Link to="/dashboard" className="label !text-accent sm:hidden">Open app</Link>
      </header>
      <Outlet />
      <footer className="border-t border-line px-6 py-8 md:px-[4.5vw]">
        <p className="max-w-3xl text-sm text-mutedfg">Chord detection is an estimate, not a perfect transcription. Only upload audio you have the right to use.</p>
      </footer>
    </div>
  );
}
