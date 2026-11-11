import { useEffect, useState } from "react";
import { ApiError, getSong, type Song } from "./api";

export function useSong(songId: string | undefined) {
  const [song, setSong] = useState<Song | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(songId));

  useEffect(() => {
    setSong(null);
    setError(null);
    if (!songId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    const ctrl = new AbortController();
    getSong(songId, ctrl.signal)
      .then(setSong)
      .catch((e: unknown) => {
        if (ctrl.signal.aborted) return;
        if (e instanceof ApiError) setError(e.status === 404 ? "Song not found." : e.message);
        else setError("Couldn't reach the server.");
      })
      .finally(() => !ctrl.signal.aborted && setLoading(false));
    return () => ctrl.abort();
  }, [songId]);

  return { song, error, loading };
}
