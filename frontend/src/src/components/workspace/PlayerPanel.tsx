import { AlertCircle, Loader2, Pause, Play, SkipBack } from "lucide-react";
import { useState } from "react";
import { audioUrl } from "../../lib/api";
import { cn } from "../../lib/cn";
import { formatTime } from "../../lib/format";
import { SPEEDS, useAudioPlayer } from "../../lib/useAudioPlayer";
import { useSong } from "../../lib/useSong";
import { useWaveform } from "../../lib/useWaveform";
import { Card } from "../ui/Card";
import Waveform from "./Waveform";

export default function PlayerPanel({ songId }: { songId?: string }) {
  if (!songId) {
    return (
      <Card className="flex flex-col p-4">
        <h2 className="label mb-3">Player</h2>
        <div className="grid h-24 place-items-center rounded-lg bg-ink-800 text-xs text-slate-500">No audio loaded</div>
      </Card>
    );
  }
  // key → switching songs remounts the player, so no state from the previous song can leak in
  return <LoadedPlayer key={songId} songId={songId} />;
}

function LoadedPlayer({ songId }: { songId: string }) {
  const { song, error: songError, loading: songLoading } = useSong(songId);
  const { peaks } = useWaveform(song ? songId : undefined);
  const player = useAudioPlayer(song ? audioUrl(song.id) : null, song?.duration ?? 0);
  const [scrub, setScrub] = useState<number | null>(null);

  const error = songError ?? player.error;
  const shownTime = scrub ?? player.currentTime;
  const ready = Boolean(song) && !error;

  return (
    <Card className="flex flex-col p-4">
      <h2 className="label mb-3">Player</h2>

      {songLoading && (
        <div className="grid h-16 place-items-center rounded-lg bg-ink-800 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading song" />
        </div>
      )}

      {error && (
        <p role="alert" className="flex items-start gap-2 rounded-lg bg-bad/10 p-3 text-xs text-bad">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          {error}
        </p>
      )}

      {song && !songError && (
        <>
          <p className="mb-2 truncate text-sm text-slate-200" title={song.original_filename}>
            {song.original_filename}
          </p>
          <Waveform
            peaks={peaks}
            currentTime={shownTime}
            duration={player.duration}
            disabled={!ready}
            onSeek={player.seek}
            onScrub={setScrub}
          />
          <p className="mt-2 text-center font-mono text-xs text-slate-400" aria-label="Playback position">
            {formatTime(shownTime)} / {formatTime(player.duration)}
          </p>

          <div className="mt-3 flex items-center justify-center gap-3">
            <button
              onClick={() => player.seek(0)}
              disabled={!ready}
              className="rounded-full p-2 text-slate-300 hover:text-white disabled:text-slate-600"
              aria-label="Restart"
            >
              <SkipBack className="h-4 w-4" />
            </button>
            <button
              onClick={player.toggle}
              disabled={!ready}
              className="grid h-12 w-12 place-items-center rounded-full bg-accent text-white shadow-glow hover:bg-accent-dim disabled:bg-ink-700 disabled:text-slate-500 disabled:shadow-none"
              aria-label={player.playing ? "Pause" : "Play"}
            >
              {player.loading && !player.playing ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : player.playing ? (
                <Pause className="h-5 w-5" />
              ) : (
                <Play className="h-5 w-5" />
              )}
            </button>
            <span className="w-8" aria-hidden /> {/* balances the restart button so play stays centered */}
          </div>

          <div className="mt-4" role="group" aria-label="Playback speed">
            <div className="grid grid-cols-4 gap-1 rounded-lg bg-ink-800 p-1">
              {SPEEDS.map((s) => (
                <button
                  key={s}
                  onClick={() => player.setSpeed(s)}
                  aria-pressed={player.speed === s}
                  disabled={!ready}
                  className={cn(
                    "rounded-md py-1 font-mono text-xs transition-colors disabled:opacity-50",
                    player.speed === s ? "bg-accent text-white" : "text-slate-400 hover:text-white",
                  )}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>

          <dl className="mt-4 space-y-1 border-t border-ink-700 pt-3 text-xs">
            <div className="flex justify-between"><dt className="text-slate-500">Key</dt><dd>—</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Tempo</dt><dd>—</dd></div>
          </dl>
        </>
      )}
    </Card>
  );
}
