import { FileAudio, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";

// Mirrors backend defaults (KEYCHORD_MAX_UPLOAD_MB=50). The server stays the source of truth.
const MAX_MB = 50;
const ACCEPT = ".mp3,.wav,.m4a,.flac,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/flac";
const EXT = /\.(mp3|wav|m4a|flac)$/i;

function validate(file: File): string | null {
  if (!EXT.test(file.name)) return "Unsupported file type. Use MP3, WAV, M4A or FLAC.";
  if (file.size > MAX_MB * 1024 * 1024) return `File is larger than ${MAX_MB} MB.`;
  return null;
}

export default function Upload() {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  function pick(f: File | undefined) {
    if (!f) return;
    const problem = validate(f);
    setError(problem);
    setFile(problem ? null : f);
  }

  return (
    <>
      <PageHeader title="Upload" description={`MP3, WAV, M4A or FLAC, up to ${MAX_MB} MB.`} />
      <Card className="max-w-2xl p-5">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files[0]); }}
          className={`grid place-items-center rounded-lg border-2 border-dashed px-6 py-12 text-center ${dragging ? "border-accent bg-accent/5" : "border-ink-600"}`}
        >
          <UploadCloud className="mb-3 h-8 w-8 text-accent-soft" aria-hidden />
          <p className="text-sm text-slate-300">Drag an audio file here, or</p>
          <Button variant="secondary" className="mt-3" onClick={() => input.current?.click()}>Choose file</Button>
          <input ref={input} type="file" accept={ACCEPT} className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />
        </div>

        {error && <p role="alert" className="mt-3 text-sm text-bad">{error}</p>}

        {file && (
          <div className="mt-4 flex items-center justify-between gap-3 rounded-lg bg-ink-800 px-3 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <FileAudio className="h-4 w-4 shrink-0 text-accent-soft" aria-hidden />
              <span className="truncate text-sm">{file.name}</span>
              <span className="shrink-0 text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
            </div>
            <button onClick={() => setFile(null)} aria-label="Remove file"><X className="h-4 w-4" /></button>
          </div>
        )}

        <div className="mt-5 flex items-center gap-3">
          <Button disabled>Analyze</Button>
          <span className="text-xs text-slate-500">Uploading and analysis are enabled in Phase 3.</span>
        </div>
      </Card>
    </>
  );
}
