import { Music, Upload } from "lucide-react";
import { ButtonLink } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";

// Counts are only shown once the API provides them (Phase 3). No placeholder numbers.
export default function Dashboard() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Your recent songs and analyses."
        action={<ButtonLink to="/upload"><Upload className="h-4 w-4" aria-hidden /> Upload song</ButtonLink>}
      />
      <Card>
        <div className="border-b border-ink-700 px-5 py-3">
          <h2 className="text-sm">Recent songs</h2>
        </div>
        <EmptyState
          icon={Music}
          title="No songs yet"
          description="Upload an MP3, WAV, M4A or FLAC file and its chords will show up here."
          action={<ButtonLink to="/upload" variant="secondary">Upload your first song</ButtonLink>}
        />
      </Card>
    </>
  );
}
