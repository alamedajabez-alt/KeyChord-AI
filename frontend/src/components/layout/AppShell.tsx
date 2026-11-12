import { History, LayoutDashboard, Menu, Settings, Upload, Piano, X, Headphones } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { cn } from "../../lib/cn";
import { useApiStatus } from "../../lib/useApiStatus";

const NAV = [
  { to: "/dashboard", label: "Home", icon: LayoutDashboard },
  { to: "/upload", label: "Analyze a song", icon: Upload },
  { to: "/workspace", label: "Studio", icon: Piano },
  { to: "/history", label: "Your library", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
];
export default function AppShell() {
  const [open,setOpen]=useState(false); const {pathname}=useLocation(); const status=useApiStatus();
  useEffect(()=>setOpen(false),[pathname]);
  return <div className="min-h-screen bg-[#090b0a] text-[#f4f4f5] lg:grid lg:grid-cols-[250px_minmax(0,1fr)]">
    <aside className={cn("fixed inset-y-0 left-0 z-40 w-[250px] border-r border-white/[.07] bg-[#0d110e] px-5 py-7 transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",open?"translate-x-0":"-translate-x-full")}>
      <div className="mb-10 flex items-center gap-3 px-2"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#1ed760] text-[#061108]"><Headphones size={22}/></div><div><div className="font-['Space_Grotesk'] text-xl font-bold tracking-tight">KeyChord<span className="text-[#1ed760]"> AI</span></div><div className="text-[10px] font-bold uppercase tracking-[.2em] text-[#748078]">Music intelligence</div></div><button className="ml-auto lg:hidden" onClick={()=>setOpen(false)} aria-label="Close menu"><X/></button></div>
      <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.2em] text-[#667168]">Workspace</p>
      <nav className="flex flex-col gap-1">{NAV.map(({to,label,icon:Icon})=><NavLink key={to} to={to} className={({isActive})=>cn("group flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition",isActive?"bg-[#1ed760]/10 text-[#1ed760]":"text-[#9aa39c] hover:bg-white/[.045] hover:text-white")}><Icon size={19} strokeWidth={2}/>{label}</NavLink>)}</nav>
      <div className="absolute inset-x-5 bottom-6 rounded-2xl border border-white/[.07] bg-white/[.035] p-4"><div className="mb-2 flex items-center gap-2 text-xs font-bold"><span className={cn("h-2 w-2 rounded-full",status==="online"?"bg-[#1ed760]":"bg-amber-400")}/>{status==="online"?"Connected to KeyChord API":`API ${status}`}</div><p className="text-xs leading-relaxed text-[#78837b]">Your music, mapped into chords.</p></div>
    </aside>
    {open&&<button className="fixed inset-0 z-30 bg-black/70 lg:hidden" onClick={()=>setOpen(false)} aria-label="Close navigation"/>}
    <div className="min-w-0"><header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-white/[.06] bg-[#090b0a]/90 px-5 backdrop-blur-xl md:px-9"><button className="grid h-10 w-10 place-items-center rounded-full text-[#a3ada5] hover:bg-white/5 lg:hidden" onClick={()=>setOpen(true)} aria-label="Open menu"><Menu/></button><div className="hidden text-sm text-[#849087] lg:block">Make every song easier to play.</div><div className="flex items-center gap-3"><span className="hidden text-xs text-[#87928a] sm:inline">Analysis engine</span><span className={cn("rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wider",status==="online"?"border-[#1ed760]/25 bg-[#1ed760]/10 text-[#1ed760]":"border-white/10 bg-white/5 text-[#a5ada7]")}>{status}</span></div></header><main className="mx-auto w-full max-w-[1600px] p-5 pb-12 md:p-9 lg:p-10"><Outlet/></main></div>
  </div>;
}
