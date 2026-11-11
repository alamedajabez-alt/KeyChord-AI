import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { Badge } from "../components/ui/Badge";
import { useApiStatus } from "../lib/useApiStatus";
import { useSettings } from "../lib/useSettings";

export default function Settings() {
  const { settings, update } = useSettings();
  const status = useApiStatus();
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

  return (
    <>
      <PageHeader title="Settings" description="Saved in this browser." />
      <div className="max-w-2xl space-y-4">
        <Card className="p-5">
          <h2 className="mb-4 text-sm">Notation</h2>
          <fieldset>
            <legend className="label mb-2">Accidentals</legend>
            <div className="flex gap-2">
              {(["sharps", "flats"] as const).map((v) => (
                <label key={v} className={`cursor-pointer rounded-lg border px-4 py-2 text-sm ${settings.accidentals === v ? "border-accent bg-accent/15 text-accent-soft" : "border-ink-600 text-slate-300"}`}>
                  <input type="radio" name="acc" className="sr-only" checked={settings.accidentals === v} onChange={() => update({ accidentals: v })} />
                  {v === "sharps" ? "Sharps (C♯)" : "Flats (D♭)"}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="mt-5 flex cursor-pointer items-center gap-3 text-sm">
            <input type="checkbox" className="h-4 w-4 accent-[#7c6cff]" checked={settings.showConfidence} onChange={(e) => update({ showConfidence: e.target.checked })} />
            Show chord confidence on the timeline
          </label>
        </Card>
        <Card className="p-5">
          <h2 className="mb-3 text-sm">Connection</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-4"><dt className="text-slate-400">API URL</dt><dd className="truncate font-mono text-xs">{apiBase}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-slate-400">Status</dt><dd><Badge tone={status === "online" ? "ok" : status === "offline" ? "warn" : "neutral"}>{status}</Badge></dd></div>
          </dl>
        </Card>
      </div>
    </>
  );
}
