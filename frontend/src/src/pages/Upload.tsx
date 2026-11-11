import { AlertCircle, FileAudio, Loader2, UploadCloud, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { PageHeader } from "../components/ui/PageHeader";
import { ApiError, uploadSong } from "../lib/api";
import { cn } from "../lib/cn";
import { formatBytes, formatTime } from "../lib/format";

// Mirror backend defaults (KEYCHORD_MAX_UPLOAD_MB / KEYCHORD_MAX_DURATION_SECONDS). They only give
// instant feedback; the server re-checks everything and stays the source of truth.
const MAX_MB = 50;
const MAX_BYTES = MAX_MB * 1024 * 1024;
const MAX_DURATION_S = 600;
const ACCEPT = ".mp3,.wav,.m4a,.flac,audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/flac";
const EXT = /\.(mp3|wav|m4a|flac)$/i;

type Phase = "idle" | "uploading" | "processing";

function checkFile(file: File): string | null {
  if (!EXT.test(file.name)) return "Unsupported file type. Use MP3, WAV, M4A or FLAC.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_BYTES) return `This file is ${formatBytes(file.size)}. The limit is ${MAX_MB} MB.`;
  return null;
}

export default function Upload() {
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const abort = useRef<AbortController | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);

  const busy = phase !== "idle";
  const tooLong = duration !== null && duration > MAX_DURATION_S;
  const shownError =
    error ?? (tooLong ? `This audio is ${formatTime(duration!)} long. The limit is ${MAX_DURATION_S / 60} minutes.` : null);

  // Read the duration in the browser so a too-long file is caught before any bytes are sent.
  useEffect(() => {
    setDuration(null);
    if (!file) return;
    const url = URL.createObjectURL(file);
    const probe = new Audio();
    probe.preload = "metadata";
    probe.onloadedmetadata = () => {
      if (Number.isFinite(probe.duration)) setDuration(probe.duration);
    };
    // If this browser can't read the metadata, say nothing: the server will decide.
    probe.src = url;
    return () => {
      probe.onloadedmetadata = null;
      probe.removeAttribute("src");
      probe.load();
      URL.revokeObjectURL(url);
    };
  }, [file]);

  // Leaving the page cancels an in-flight upload.
  useEffect(() => () => abort.current?.abort(), []);

  function pick(files: FileList | null) {
    if (!files || files.length === 0) return;
    if (files.length > 1) {
      setFile(null);
      setError("Please add one file at a time.");
      return;
    }
    const problem = checkFile(files[0]);
    setError(problem);
    setFile(problem ? null : files[0]);
  }

  function clear() {
    setFile(null);
    setError(null);
  }

  async function submit() {
    if (!file || busy || tooLong) return;
    setError(null);
    setProgress(0);
    setPhase("uploading");
    const ctrl = new AbortController();
    abort.current = ctrl;
    try {
      const song = await uploadSong(
        file,
        (fraction) => {
          setProgress(fraction);
          if (fraction >= 1) setPhase("processing"); // bytes are sent; the server is now validating the audio
        },
        ctrl.signal,
      );
      navigate(`/workspace/${song.id}`);
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError")) {
        setError(e instanceof ApiError ? e.message : "Upload failed. Please try again.");
      }
      setPhase("idle");
    } finally {
      abort.current = null;
    }
  }

  const pct = Math.round(progress * 100);

  return (
    <>
      <PageHeader title="Upload" description={`MP3, WAV, M4A or FLAC, up to ${MAX_MB} MB and ${MAX_DURATION_S / 60} minutes.`} />
      <Card className="max-w-2xl p-5">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = busy ? "none" : "copy";
            if (!busy) setDragging(true);
          }}
          onDragLeave={(e) => {
            // dragleave also fires when moving onto a child element; only react when truly leaving the zone
            if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false);
          }}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (!busy) pick(e.dataTransfer.files);
          }}
          className={cn(
            "grid place-items-center rounded-lg border-2 border-dashed px-6 py-12 text-center transition-colors",
            dragging ? "border-accent bg-accent/5" : "border-ink-600",
            busy && "opacity-50",
          )}
        >
          <UploadCloud className="mb-3 h-8 w-8 text-accent-soft" aria-hidden />
          <p className="text-sm text-slate-300">{dragging ? "Drop to add this file" : "Drag an audio file here, or"}</p>
          <Button variant="secondary" className="mt-3" disabled={busy} onClick={() => input.current?.click()}>
            Choose file
          </Button>
          <input
            ref={input}
            type="file"
            accept={ACCEPT}
            className="sr-only"
            tabIndex={-1}
            onChange={(e) => {
              pick(e.target.files);
              e.target.value = ""; // allow re-selecting the same file after an error
            }}
          />
        </div>

        {shownError && (
          <p role="alert" className="mt-3 flex items-start gap-2 text-sm text-bad">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            {shownError}
          </p>
        )}

        {file && (
          <div className="mt-4 rounded-lg bg-ink-800 px-3 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <FileAudio className="h-5 w-5 shrink-0 text-accent-soft" aria-hidden />
                <div className="min-w-0">
                  <p className="truncate text-sm text-slate-100" title={file.name}>
                    {file.name}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {file.name.split(".").pop()?.toUpperCase()} · {formatBytes(file.size)}
                    {duration !== null && <> · {formatTime(duration)}</>}
                  </p>
                </div>
              </div>
              <button
                onClick={clear}
                disabled={busy}
                aria-label="Remove file"
                className="shrink-0 rounded p-1 text-slate-400 hover:text-white disabled:opacity-40"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {busy && (
              <div className="mt-3">
                <div
                  role="progressbar"
                  aria-label="Upload progress"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={pct}
                  className="h-2 overflow-hidden rounded-full bg-ink-700"
                >
                  <div className="h-full rounded-full bg-accent transition-[width] duration-150" style={{ width: `${pct}%` }} />
                </div>
                <p className="mt-2 flex items-center gap-2 text-xs text-slate-400" aria-live="polite">
                  {phase === "processing" ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" aria-hidden /> Checking your audio…
                    </>
                  ) : (
                    <>Uploading… {pct}%</>
                  )}
                </p>
              </div>
            )}
          </div>
        )}

        <div className="mt-5 flex items-center gap-3">
          <Button disabled={!file || busy || tooLong} onClick={submit}>
            {busy ? "Uploading…" : "Upload"}
          </Button>
          {phase === "uploading" && (
            <Button variant="ghost" onClick={() => abort.current?.abort()}>
              Cancel
            </Button>
          )}
        </div>
      </Card>
    </>
  );
}
