import type { EndpointItem, Incident, RiskResponse } from "../lib/api";
import { isHealthy, severityColor, severityLabel } from "../lib/severity";

function StatCard({
  label,
  value,
  accent,
  hint,
}: {
  label: string;
  value: string;
  accent?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] px-4 py-3.5">
      <p className="text-xs font-medium uppercase tracking-wide text-[var(--sx-text-muted)]">
        {label}
      </p>
      <p
        className="mt-1.5 text-2xl font-semibold tabular-nums"
        style={{ color: accent ?? "var(--sx-text-primary)" }}
      >
        {value}
      </p>
      {hint && <p className="mt-1 text-xs text-[var(--sx-text-muted)]">{hint}</p>}
    </div>
  );
}

export function SummaryCards({
  endpoints,
  risks,
  incidents,
}: {
  endpoints: EndpointItem[];
  risks: Record<string, RiskResponse>;
  incidents: Incident[];
}) {
  const riskValues = Object.values(risks);
  const healthyCount = riskValues.filter((r) => isHealthy(r.severity)).length;
  const suspiciousCount = riskValues.filter((r) => !isHealthy(r.severity)).length;
  const activeIncidents = incidents.filter(
    (i) => i.status === "OPEN" || i.status === "INVESTIGATING",
  ).length;

  const worst = riskValues.reduce<RiskResponse | null>((acc, r) => {
    if (!acc || r.compromise_probability > acc.compromise_probability) return r;
    return acc;
  }, null);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <StatCard label="Total Endpoints" value={String(endpoints.length)} />
      <StatCard
        label="Healthy"
        value={String(healthyCount)}
        accent={healthyCount > 0 ? severityColor("low") : undefined}
      />
      <StatCard
        label="Suspicious"
        value={String(suspiciousCount)}
        accent={suspiciousCount > 0 ? severityColor("high") : undefined}
      />
      <StatCard
        label="Active Incidents"
        value={String(activeIncidents)}
        accent={activeIncidents > 0 ? severityColor("critical") : undefined}
      />
      <StatCard
        label="Infrastructure Risk"
        value={worst ? `${worst.compromise_probability.toFixed(0)}%` : "—"}
        accent={worst ? severityColor(worst.severity) : undefined}
        hint={worst ? `Peak: ${worst.hostname} (${severityLabel(worst.severity)})` : "No data yet"}
      />
    </div>
  );
}
