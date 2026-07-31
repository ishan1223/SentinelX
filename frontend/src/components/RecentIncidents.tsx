import type { Incident } from "../lib/api";
import { formatRelativeTime } from "../lib/format";
import { SeverityBadge } from "./SeverityBadge";
import { EmptyNotice } from "./StateNotice";

const STATUS_STYLE: Record<Incident["status"], string> = {
  OPEN: "text-[#f0958a]",
  INVESTIGATING: "text-[#fab219]",
  RESOLVED: "text-[var(--sx-text-muted)]",
};

export function RecentIncidents({
  incidents,
  onSelectHost,
}: {
  incidents: Incident[];
  onSelectHost: (hostname: string) => void;
}) {
  if (incidents.length === 0) {
    return <EmptyNotice label="No incidents recorded. Trigger a simulated compromise to see one appear." />;
  }

  const recent = [...incidents]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 6);

  return (
    <ul className="divide-y divide-[var(--sx-border)]">
      {recent.map((incident) => (
        <li key={incident.incident_id}>
          <button
            type="button"
            onClick={() => onSelectHost(incident.hostname)}
            className="flex w-full items-start justify-between gap-3 py-2.5 text-left transition hover:opacity-80"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--sx-text-muted)]">
                  {incident.incident_id}
                </span>
                <span className="text-sm font-medium text-[var(--sx-text-primary)]">
                  {incident.hostname}
                </span>
                <SeverityBadge severity={incident.severity} />
              </div>
              <p className="mt-1 truncate text-xs text-[var(--sx-text-secondary)]">
                {incident.summary}
              </p>
            </div>
            <div className="shrink-0 text-right text-xs">
              <p className={`font-medium ${STATUS_STYLE[incident.status]}`}>{incident.status}</p>
              <p className="mt-1 text-[var(--sx-text-muted)]">
                {formatRelativeTime(incident.created_at)}
              </p>
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}
