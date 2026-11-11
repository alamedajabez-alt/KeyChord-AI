import { AudioWaveform } from "lucide-react";
import { ButtonLink } from "../ui/Button";
import { Card } from "../ui/Card";
import { EmptyState } from "../ui/EmptyState";

export default function TimelinePanel({ songId }: { songId?: string }) {
  return (
    <Card className="flex min-h-[260px] flex-col">
      <h2 className="label border-b border-ink-700 px-4 py-3">Chord timeline</h2>
      <EmptyState
        className="flex-1"
        icon={AudioWaveform}
        title={songId ? "No analysis yet" : "No song selected"}
        description={
          songId
            ? "Chords will appear here once this song has been analyzed."
            : "Upload a song to see its chords on a timeline."
        }
        action={!songId && <ButtonLink to="/upload" variant="secondary">Upload a song</ButtonLink>}
      />
    </Card>
  );
}
