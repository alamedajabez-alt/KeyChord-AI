import { useParams } from "react-router-dom";
import PianoPanel from "../components/workspace/PianoPanel";
import PlayerPanel from "../components/workspace/PlayerPanel";
import TimelinePanel from "../components/workspace/TimelinePanel";

// Mobile: vertical stack (player → timeline → piano). lg+: left player / center timeline / right piano.
export default function Workspace() {
  const { songId } = useParams();
  return (
    <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)_320px] lg:items-start">
      <PlayerPanel songId={songId} />
      <TimelinePanel songId={songId} />
      <PianoPanel />
    </div>
  );
}
