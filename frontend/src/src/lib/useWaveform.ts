import { useEffect, useState } from "react";
import { audioUrl } from "./api";
import { computePeaks } from "./peaks";

/**
 * Best-effort waveform. Downloads and decodes the file in the browser (the transient decoded buffer
 * can be large for long tracks), and returns null peaks on any failure so the UI falls back to a plain
 * progress bar. Playback never depends on this.
 */
export function useWaveform(songId: string | undefined): { peaks: number[] | null; loading: boolean } {
  const [peaks, setPeaks] = useState<number[] | null>(null);
  const [loading, setLoading] = useState(Boolean(songId));

  useEffect(() => {
    setPeaks(null);
    if (!songId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const ctrl = new AbortController();
    (async () => {
      try {
        const res = await fetch(audioUrl(songId), { signal: ctrl.signal });
        if (!res.ok) throw new Error(String(res.status));
        const result = await computePeaks(await res.arrayBuffer());
        if (!ctrl.signal.aborted) setPeaks(result);
      } catch {
        /* fall back to the progress bar */
      } finally {
        if (!ctrl.signal.aborted) setLoading(false);
      }
    })();
    return () => ctrl.abort();
  }, [songId]);

  return { peaks, loading };
}
