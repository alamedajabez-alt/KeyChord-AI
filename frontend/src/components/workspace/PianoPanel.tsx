import { Card } from "../ui/Card";

// Static C3–B4 keyboard. No keys are highlighted until a chord is active.
const WHITE = ["C", "D", "E", "F", "G", "A", "B"];
const BLACK_AFTER: Record<string, boolean> = { C: true, D: true, E: false, F: true, G: true, A: true, B: false };
const OCTAVES = [3, 4];

export default function PianoPanel() {
  const keys = OCTAVES.flatMap((o) => WHITE.map((n) => ({ n, o })));
  return (
    <Card className="p-4">
      <h2 className="label mb-3">Piano</h2>
      <div className="flex h-32 overflow-hidden rounded-md" role="img" aria-label="Piano keyboard, no chord selected">
        {keys.map(({ n, o }) => (
          <div key={`${n}${o}`} className="relative flex-1 border-r border-ink-600 bg-slate-200 last:border-r-0">
            {BLACK_AFTER[n] && <div className="absolute -right-1.5 top-0 z-10 h-2/3 w-3 rounded-b bg-ink-950" />}
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-500">Suggested voicings appear here for the selected chord.</p>
    </Card>
  );
}
