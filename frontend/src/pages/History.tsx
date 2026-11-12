import { History as HistoryIcon, Music2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
export default function History(){return <div className="rise"><PageHeader title="Your library" description="All the songs you've explored with KeyChord AI."/><Card className="overflow-hidden"><div className="flex items-center justify-between border-b border-white/[.07] px-6 py-4"><div className="flex items-center gap-2 text-sm font-bold"><Music2 size={17} className="text-[#1ed760]"/> Recent analyses</div><span className="text-xs text-[#77847a]">0 tracks</span></div><EmptyState icon={HistoryIcon} title="Your library is waiting" description="Once you analyze a song, it will appear here so you can jump back into its chords anytime." action={<Link to="/upload" className="green-button inline-flex h-11 items-center px-5 text-sm">Analyze your first song</Link>}/></Card></div>}
