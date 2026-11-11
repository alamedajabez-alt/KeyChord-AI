import { useCallback, useEffect, useRef, useState } from "react";

export const SPEEDS = [0.5, 0.75, 1, 1.25] as const;
export type Speed = (typeof SPEEDS)[number];

export interface AudioPlayer {
  playing: boolean;
  loading: boolean; // metadata not ready yet, or stalled waiting for data
  error: string | null;
  currentTime: number;
  duration: number;
  speed: Speed;
  toggle: () => void;
  seek: (seconds: number) => void;
  setSpeed: (speed: Speed) => void;
}

/**
 * Wraps one HTMLAudioElement. `src` should be a Range-capable URL so seeking is cheap.
 * `knownDuration` (from the server) is used until the browser reports its own.
 */
export function useAudioPlayer(src: string | null, knownDuration = 0): AudioPlayer {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(Boolean(src));
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(knownDuration);
  const [speed, setSpeedState] = useState<Speed>(1);

  useEffect(() => {
    setPlaying(false);
    setError(null);
    setCurrentTime(0);
    setSpeedState(1);
    if (!src) {
      setLoading(false);
      return;
    }
    setLoading(true);

    const audio = new Audio();
    audio.preload = "metadata";
    audio.preservesPitch = true; // slowing down to learn a part must not change the pitch
    audio.src = src;
    audioRef.current = audio;

    let raf = 0;
    const tick = () => {
      setCurrentTime(audio.currentTime);
      raf = requestAnimationFrame(tick);
    };
    const syncDuration = () => {
      if (Number.isFinite(audio.duration) && audio.duration > 0) setDuration(audio.duration);
    };

    const on = {
      loadedmetadata: () => {
        syncDuration();
        setLoading(false);
      },
      durationchange: syncDuration,
      canplay: () => setLoading(false),
      waiting: () => setLoading(true),
      playing: () => {
        setLoading(false);
        setPlaying(true);
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(tick); // smooth progress while playing (timeupdate only fires ~4x/s)
      },
      pause: () => {
        setPlaying(false);
        cancelAnimationFrame(raf);
        setCurrentTime(audio.currentTime);
      },
      ended: () => {
        setPlaying(false);
        cancelAnimationFrame(raf);
        setCurrentTime(audio.duration);
      },
      seeked: () => setCurrentTime(audio.currentTime),
      error: () => {
        setLoading(false);
        setPlaying(false);
        setError("This audio couldn't be loaded.");
      },
    };
    (Object.entries(on) as [string, () => void][]).forEach(([name, fn]) => audio.addEventListener(name, fn));

    return () => {
      cancelAnimationFrame(raf);
      (Object.entries(on) as [string, () => void][]).forEach(([name, fn]) => audio.removeEventListener(name, fn));
      audio.pause();
      audio.removeAttribute("src");
      audio.load(); // abort any in-flight range requests
      audioRef.current = null;
    };
  }, [src]);

  const toggle = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (!audio.paused) {
      audio.pause();
      return;
    }
    if (audio.ended) audio.currentTime = 0;
    audio.play().catch((e: unknown) => {
      // AbortError = a pause()/new load interrupted play(); that's not a failure
      if (!(e instanceof DOMException && e.name === "AbortError")) setError("Couldn't start playback.");
    });
  }, []);

  const seek = useCallback((seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    const max = Number.isFinite(audio.duration) ? audio.duration : Infinity;
    const t = Math.min(Math.max(seconds, 0), max);
    audio.currentTime = t;
    setCurrentTime(t);
  }, []);

  const setSpeed = useCallback((next: Speed) => {
    const audio = audioRef.current;
    if (audio) {
      audio.playbackRate = next;
      audio.preservesPitch = true;
    }
    setSpeedState(next);
  }, []);

  return { playing, loading, error, currentTime, duration, speed, toggle, seek, setSpeed };
}
