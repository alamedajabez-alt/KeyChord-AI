import { useEffect, useRef } from "react";
import { formatTime } from "../../lib/format";

const PLAYED = "#7c6cff"; // accent
const UNPLAYED = "#2e3347"; // ink-600
const BAR = 2;
const GAP = 1;
const SEEK_STEP = 5; // seconds per arrow key

interface Props {
  peaks: number[] | null; // null → plain progress bar
  currentTime: number;
  duration: number;
  disabled?: boolean;
  onSeek: (seconds: number) => void; // committed seek (pointer up / key press)
  onScrub: (seconds: number | null) => void; // live position while dragging; null when the drag ends
}

/** Click or drag to seek; arrow keys / Home / End when focused. Renders a waveform, or a progress bar without peaks. */
export default function Waveform({ peaks, currentTime, duration, disabled, onSeek, onScrub }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const dragging = useRef(false);
  const fraction = duration > 0 ? Math.min(currentTime / duration, 1) : 0;

  useEffect(() => {
    const el = canvas.current;
    const wrap = box.current;
    if (!el || !wrap || !peaks) return;
    const dpr = window.devicePixelRatio || 1;
    const draw = () => {
      const w = wrap.clientWidth;
      const h = wrap.clientHeight;
      el.width = Math.floor(w * dpr);
      el.height = Math.floor(h * dpr);
      const ctx = el.getContext("2d");
      if (!ctx) return;
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);
      const bars = Math.max(1, Math.floor(w / (BAR + GAP)));
      const playedBars = Math.round(bars * fraction);
      for (let i = 0; i < bars; i++) {
        const from = Math.floor((i / bars) * peaks.length);
        const to = Math.max(from + 1, Math.floor(((i + 1) / bars) * peaks.length));
        let peak = 0;
        for (let j = from; j < to; j++) peak = Math.max(peak, peaks[j] ?? 0);
        const bh = Math.max(2, peak * (h - 4));
        ctx.fillStyle = i < playedBars ? PLAYED : UNPLAYED;
        ctx.fillRect(i * (BAR + GAP), (h - bh) / 2, BAR, bh);
      }
    };
    draw();
    const ro = new ResizeObserver(draw);
    ro.observe(wrap);
    return () => ro.disconnect();
  }, [peaks, fraction]);

  const timeAt = (clientX: number) => {
    const rect = box.current!.getBoundingClientRect();
    const f = rect.width > 0 ? Math.min(Math.max((clientX - rect.left) / rect.width, 0), 1) : 0;
    return f * duration;
  };

  return (
    <div
      ref={box}
      role="slider"
      tabIndex={disabled ? -1 : 0}
      aria-label="Seek"
      aria-valuemin={0}
      aria-valuemax={Math.floor(duration)}
      aria-valuenow={Math.floor(currentTime)}
      aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
      aria-disabled={disabled}
      className={`relative h-16 w-full touch-none select-none rounded-lg bg-ink-800 ${disabled ? "opacity-50" : "cursor-pointer"}`}
      onPointerDown={(e) => {
        if (disabled || duration <= 0) return;
        dragging.current = true;
        e.currentTarget.setPointerCapture(e.pointerId);
        onScrub(timeAt(e.clientX));
      }}
      onPointerMove={(e) => {
        if (dragging.current) onScrub(timeAt(e.clientX));
      }}
      onPointerUp={(e) => {
        if (!dragging.current) return;
        dragging.current = false;
        onSeek(timeAt(e.clientX));
        onScrub(null);
      }}
      onPointerCancel={() => {
        dragging.current = false;
        onScrub(null);
      }}
      onKeyDown={(e) => {
        if (disabled || duration <= 0) return;
        const keys: Record<string, number> = {
          ArrowLeft: currentTime - SEEK_STEP,
          ArrowDown: currentTime - SEEK_STEP,
          ArrowRight: currentTime + SEEK_STEP,
          ArrowUp: currentTime + SEEK_STEP,
          Home: 0,
          End: duration,
        };
        if (e.key in keys) {
          e.preventDefault();
          onSeek(keys[e.key]);
        }
      }}
    >
      {peaks ? (
        <canvas ref={canvas} className="absolute inset-0 h-full w-full" aria-hidden />
      ) : (
        <div className="absolute inset-x-2 top-1/2 h-2 -translate-y-1/2 overflow-hidden rounded-full bg-ink-600" aria-hidden>
          <div className="h-full rounded-full bg-accent" style={{ width: `${fraction * 100}%` }} />
        </div>
      )}
      {/* playhead */}
      <div
        className="pointer-events-none absolute inset-y-0 w-0.5 bg-white/80"
        style={{ left: `calc(${fraction * 100}% - 1px)` }}
        aria-hidden
      />
    </div>
  );
}
