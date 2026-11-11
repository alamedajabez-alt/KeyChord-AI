import { Pause, Play, SkipBack } from "lucide-react";
import { Card } from "../ui/Card";

export default function PlayerPanel() {
  return (
    <Card className="flex flex-col p-4">
      <h2 className="label mb-3">Player</h2>
      <div className="mb-4 grid h-24 place-items-center rounded-lg bg-ink-800 text-xs text-slate-500">
        No audio loaded
      </div>
      <div className="flex items-center justify-center gap-2">
        <button disabled className="rounded-full p-2 text-slate-500" aria-label="Restart"><SkipBack className="h-4 w-4" /></button>
        <button disabled className="rounded-full bg-ink-700 p-3 text-slate-500" aria-label="Play"><Play className="h-5 w-5" /></button>
        <button disabled className="hidden rounded-full p-2" aria-label="Pause"><Pause className="h-4 w-4" /></button>
      </div>
      <p className="mt-3 text-center font-mono text-xs text-slate-500">0:00 / 0:00</p>
      <dl className="mt-4 space-y-1 border-t border-ink-700 pt-3 text-xs">
        <div className="flex justify-between"><dt className="text-slate-500">Key</dt><dd>—</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Tempo</dt><dd>—</dd></div>
      </dl>
    </Card>
  );
}
