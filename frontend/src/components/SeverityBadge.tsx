import { severityColor, severityLabel } from "../lib/severity";

export function SeverityBadge({ severity }: { severity: string }) {
  const color = severityColor(severity);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs font-semibold uppercase tracking-wide"
      style={{ color, backgroundColor: `${color}1a`, border: `1px solid ${color}40` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {severityLabel(severity)}
    </span>
  );
}
