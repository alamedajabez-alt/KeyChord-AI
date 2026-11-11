import { History as HistoryIcon } from "lucide-react";
import { ButtonLink } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";

export default function History() {
  return (
    <>
      <PageHeader title="History" description="Every analysis you've run, newest first." />
      <Card>
        <EmptyState
          icon={HistoryIcon}
          title="No analyses yet"
          description="Completed and failed analyses will be listed here so you can reopen or delete them."
          action={<ButtonLink to="/upload" variant="secondary">Analyze a song</ButtonLink>}
        />
      </Card>
    </>
  );
}
