import type { KeyboardEvent } from "react";
import type { EndpointItem, RiskResponse } from "../lib/api";
import { formatRelativeTime, formatSignalLabel } from "../lib/format";
import { statusTierColor, statusTierLabel } from "../lib/severity";
import { EmptyNotice, LoadingNotice } from "./StateNotice";

const TYPE_LABEL: Record<string, string> = {
  system: "System",
  firewall: "Firewall",
  router: "Router",
};

export function EndpointTable({
  endpoints,
  risks,
  loading,
  onSelectHost,
}: {
  endpoints: EndpointItem[];
  risks: Record<string, RiskResponse>;
  loading: boolean;
  onSelectHost: (hostname: string) => void;
}) {
  if (loading && endpoints.length === 0) return <LoadingNotice label="Loading endpoints…" />;
  if (!loading && endpoints.length === 0) {
    return <EmptyNotice label="No endpoints reported by the backend." />;
  }

  function handleRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, hostname: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelectHost(hostname);
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-[var(--sx-border)] text-xs uppercase tracking-wide text-[var(--sx-text-muted)]">
            <th className="px-2 py-2 font-medium">Host</th>
            <th className="px-2 py-2 font-medium">Status</th>
            <th className="px-2 py-2 text-right font-medium" title="Correlated compromise probability">
              Risk
            </th>
            <th className="px-2 py-2 text-right font-medium" title="IsolationForest anomaly score">
              Anomaly
            </th>
            <th className="px-2 py-2 font-medium">Last Seen</th>
            <th className="px-2 py-2 font-medium" title="The most significant deviating signal, in standard deviations">
              Primary Signal
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--sx-border)]">
          {endpoints.map((endpoint) => {
            const risk = risks[endpoint.id];
            const color = risk ? statusTierColor(risk.severity) : "var(--sx-text-muted)";
            const primarySignal = risk?.contributing_signals[0];
            const label = `Open investigation view for ${endpoint.id}`;

            return (
              <tr
                key={endpoint.id}
                role="button"
                tabIndex={0}
                aria-label={label}
                onClick={() => onSelectHost(endpoint.id)}
                onKeyDown={(event) => handleRowKeyDown(event, endpoint.id)}
                className="cursor-pointer transition hover:bg-white/[0.03] focus:bg-white/[0.05] focus:outline-none focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-[var(--sx-accent)]"
              >
                <td className="px-2 py-2.5">
                  <div className="font-medium text-[var(--sx-text-primary)]">{endpoint.id}</div>
                  <div className="text-xs text-[var(--sx-text-muted)]">
                    {endpoint.name} · {TYPE_LABEL[endpoint.type] ?? endpoint.type}
                  </div>
                </td>
                <td className="px-2 py-2.5">
                  <span
                    className="inline-flex items-center gap-1.5 text-xs font-medium"
                    style={{ color }}
                  >
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
                    {risk ? statusTierLabel(risk.severity) : "Unknown"}
                  </span>
                </td>
                <td className="px-2 py-2.5 text-right tabular-nums text-[var(--sx-text-primary)]">
                  {risk ? `${risk.compromise_probability.toFixed(0)}%` : "—"}
                </td>
                <td className="px-2 py-2.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                  {risk ? `${risk.anomaly_score.toFixed(0)}%` : "—"}
                </td>
                <td className="px-2 py-2.5 text-[var(--sx-text-secondary)]">
                  {formatRelativeTime(endpoint.last_seen)}
                </td>
                <td className="px-2 py-2.5 text-[var(--sx-text-secondary)]">
                  {primarySignal ? (
                    <span>
                      {formatSignalLabel(primarySignal.feature)}{" "}
                      <span className="text-[var(--sx-text-muted)]">
                        ({primarySignal.z_score >= 0 ? "+" : ""}
                        {primarySignal.z_score.toFixed(1)}σ)
                      </span>
                    </span>
                  ) : (
                    <span className="text-[var(--sx-text-muted)]">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
