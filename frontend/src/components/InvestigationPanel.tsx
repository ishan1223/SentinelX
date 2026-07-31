import { useEffect, useRef } from "react";
import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EndpointItem } from "../lib/api";
import { useInvestigation } from "../hooks/useInvestigation";
import { formatAbsoluteTime, formatBytes, formatNumber, formatSignalLabel } from "../lib/format";
import { severityColor, statusTierLabel } from "../lib/severity";
import { SeverityBadge } from "./SeverityBadge";
import { ErrorNotice, LoadingNotice } from "./StateNotice";

const OBSERVED_COLOR = "#3987e5";
const INCREASE_COLOR = "#d03b3b";
const DECREASE_COLOR = "#3987e5";

/** Evidence values span wildly different units (bytes, counts, percentages)
 * -- plotting them raw on one shared axis makes most bars unreadable next
 * to outbound_bytes. z-score (standard deviations from baseline) is already
 * unit-independent, so it is the correct common base for a single chart;
 * literal observed/baseline numbers are shown as text instead of a second
 * axis. */
function formatSignalValue(rawSignal: string, value: number): string {
  if (rawSignal.includes("traffic") || rawSignal.includes("bytes")) return formatBytes(value);
  if (rawSignal.includes("utilization") || rawSignal.includes("usage")) return `${value.toFixed(1)}%`;
  return formatNumber(value, 1);
}

function StatTile({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-md border border-[var(--sx-border)] bg-black/20 px-3 py-2.5">
      <p className="text-[11px] uppercase tracking-wide text-[var(--sx-text-muted)]">{label}</p>
      <p className="mt-1 text-xl font-semibold tabular-nums" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

export function InvestigationPanel({
  hostname,
  endpoint,
  refreshToken,
  onClose,
}: {
  hostname: string;
  endpoint: EndpointItem | undefined;
  refreshToken: number;
  onClose: () => void;
}) {
  const { risk, explanation, telemetry, loading, error } = useInvestigation(
    hostname,
    refreshToken,
  );

  const statusColor = risk ? severityColor(risk.severity) : "var(--sx-text-muted)";

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();
    function handleKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const baselineChartData =
    explanation?.evidence.map((e) => ({
      signal: formatSignalLabel(e.signal),
      deviation: e.deviation,
      observedText: formatSignalValue(e.signal, e.observed),
      baselineText: formatSignalValue(e.signal, e.baseline),
    })) ?? [];

  const contributionChartData =
    explanation?.evidence
      .map((e) => ({ signal: formatSignalLabel(e.signal), contribution: e.contribution }))
      .sort((a, b) => b.contribution - a.contribution) ?? [];

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        aria-label="Close investigation panel"
        onClick={onClose}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />

      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Investigation for ${hostname}`}
        className="relative flex h-full w-full max-w-xl flex-col overflow-y-auto border-l border-[var(--sx-border)] bg-[var(--sx-page)] shadow-2xl"
      >
        <div aria-hidden className="h-1 shrink-0" style={{ backgroundColor: statusColor }} />
        <header className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-[var(--sx-border)] bg-[var(--sx-page)] px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-[var(--sx-text-muted)]">
              Investigation
            </p>
            <div className="mt-0.5 flex items-center gap-2.5">
              <h2 className="text-lg font-semibold text-[var(--sx-text-primary)]">{hostname}</h2>
              {risk && <SeverityBadge severity={risk.severity} />}
            </div>
            {endpoint && (
              <p className="mt-0.5 text-xs text-[var(--sx-text-muted)]">
                {endpoint.name} · {endpoint.ip_address}
              </p>
            )}
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="rounded-md border border-[var(--sx-border)] px-2.5 py-1.5 text-xs text-[var(--sx-text-secondary)] transition hover:text-[var(--sx-text-primary)] focus-visible:ring-1 focus-visible:ring-[var(--sx-accent)]"
          >
            Close <span aria-hidden>✕</span>
          </button>
        </header>

        <div className="flex-1 space-y-5 px-5 py-5">
          {loading && !risk && <LoadingNotice label="Loading investigation data…" />}
          {error && <ErrorNotice label={error} />}

          {risk && (
            <>
              <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
                <StatTile
                  label="Compromise Probability"
                  value={`${risk.compromise_probability.toFixed(1)}%`}
                  color={statusColor}
                />
                <StatTile
                  label="Anomaly Score"
                  value={`${risk.anomaly_score.toFixed(1)}%`}
                  color="var(--sx-text-primary)"
                />
                <StatTile
                  label="Correlated Signals"
                  value={String(risk.correlated_signal_count)}
                  color="var(--sx-text-primary)"
                />
              </div>

              {explanation && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                    Why {statusTierLabel(risk.severity)}
                  </h3>
                  <p
                    className="rounded-md border-l-2 bg-black/20 p-3 text-sm leading-relaxed text-[var(--sx-text-secondary)]"
                    style={{ borderColor: statusColor }}
                  >
                    {explanation.summary}
                  </p>
                </section>
              )}

              {baselineChartData.length > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                    Behavioural Baseline Comparison
                  </h3>
                  <p className="mb-2 text-[11px] text-[var(--sx-text-muted)]">
                    Deviation from each signal's own baseline, in standard deviations (σ) — the
                    common unit across signals of different scales.
                  </p>
                  <ResponsiveContainer width="100%" height={Math.max(160, baselineChartData.length * 40)}>
                    <BarChart
                      data={baselineChartData}
                      layout="vertical"
                      margin={{ top: 0, right: 32, bottom: 0, left: 0 }}
                    >
                      <XAxis type="number" tick={{ fill: "var(--sx-text-muted)", fontSize: 10 }} axisLine={false} tickLine={false} unit="σ" />
                      <YAxis
                        type="category"
                        dataKey="signal"
                        tick={{ fill: "var(--sx-text-secondary)", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={110}
                      />
                      <ReferenceLine x={0} stroke="var(--sx-axis)" />
                      <Tooltip
                        cursor={{ fill: "rgba(255,255,255,0.04)" }}
                        content={({ active, payload }) => {
                          if (!active || !payload || payload.length === 0) return null;
                          const entry = payload[0].payload as (typeof baselineChartData)[number];
                          return (
                            <div className="rounded-md border border-[var(--sx-border)] bg-[var(--sx-surface)] px-3 py-2 text-xs shadow-lg">
                              <p className="font-medium text-[var(--sx-text-primary)]">{entry.signal}</p>
                              <p className="mt-1 text-[var(--sx-text-secondary)]">
                                {entry.deviation >= 0 ? "+" : ""}
                                {entry.deviation.toFixed(1)}σ
                              </p>
                              <p className="mt-1 text-[var(--sx-text-muted)]">
                                Observed {entry.observedText} · Baseline {entry.baselineText}
                              </p>
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="deviation" radius={[0, 3, 3, 0]} maxBarSize={16} isAnimationActive={false}>
                        {baselineChartData.map((entry) => (
                          <Cell
                            key={entry.signal}
                            fill={entry.deviation >= 0 ? INCREASE_COLOR : DECREASE_COLOR}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-2 space-y-1 border-t border-[var(--sx-border)] pt-2">
                    {baselineChartData.map((entry) => (
                      <div
                        key={entry.signal}
                        className="flex items-center justify-between text-xs text-[var(--sx-text-secondary)]"
                      >
                        <span>{entry.signal}</span>
                        <span className="tabular-nums text-[var(--sx-text-muted)]">
                          {entry.observedText} observed · {entry.baselineText} baseline
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {contributionChartData.length > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                    Signal Contribution
                  </h3>
                  <ResponsiveContainer width="100%" height={Math.max(140, contributionChartData.length * 34)}>
                    <BarChart
                      data={contributionChartData}
                      layout="vertical"
                      margin={{ top: 0, right: 24, bottom: 0, left: 0 }}
                    >
                      <XAxis type="number" hide domain={[0, "dataMax"]} />
                      <YAxis
                        type="category"
                        dataKey="signal"
                        tick={{ fill: "var(--sx-text-secondary)", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={110}
                      />
                      <Tooltip
                        cursor={{ fill: "rgba(255,255,255,0.04)" }}
                        content={({ active, payload }) => {
                          if (!active || !payload || payload.length === 0) return null;
                          const entry = payload[0].payload as { signal: string; contribution: number };
                          return (
                            <div className="rounded-md border border-[var(--sx-border)] bg-[var(--sx-surface)] px-3 py-2 text-xs shadow-lg">
                              {entry.signal}: {entry.contribution.toFixed(1)}%
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="contribution" fill={OBSERVED_COLOR} radius={[0, 3, 3, 0]} maxBarSize={14} isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </section>
              )}

              {explanation && explanation.evidence.length === 0 && (
                <p className="text-xs text-[var(--sx-text-muted)]">
                  No signals currently deviate from this host's baseline.
                </p>
              )}

              {explanation && explanation.recommended_actions.length > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                    Recommended Actions
                  </h3>
                  <ul className="space-y-1.5">
                    {explanation.recommended_actions.map((action, index) => (
                      <li
                        key={action}
                        className="flex items-start gap-2 text-sm text-[var(--sx-text-secondary)]"
                      >
                        <span className="mt-0.5 shrink-0 text-[11px] font-semibold text-[var(--sx-accent)]">
                          {index + 1}.
                        </span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                  Recent Telemetry
                </h3>
                {telemetry.length === 0 ? (
                  <p className="rounded-md border border-[var(--sx-border)] py-4 text-center text-xs text-[var(--sx-text-muted)]">
                    No telemetry recorded yet for this host.
                  </p>
                ) : (
                <div className="overflow-x-auto rounded-md border border-[var(--sx-border)]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[var(--sx-border)] text-[var(--sx-text-muted)]">
                        <th className="px-2 py-1.5 font-medium">Time</th>
                        <th className="px-2 py-1.5 text-right font-medium">CPU</th>
                        <th className="px-2 py-1.5 text-right font-medium">Mem</th>
                        <th className="px-2 py-1.5 text-right font-medium">Out</th>
                        <th className="px-2 py-1.5 text-right font-medium">DNS</th>
                        <th className="px-2 py-1.5 text-right font-medium">Failed Auth</th>
                        <th className="px-2 py-1.5 font-medium"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--sx-border)]">
                      {[...telemetry].reverse().map((sample) => (
                        <tr key={sample.timestamp} className={sample.is_anomalous ? "bg-[#d03b3b0f]" : undefined}>
                          <td className="px-2 py-1.5 tabular-nums text-[var(--sx-text-secondary)]">
                            {formatAbsoluteTime(sample.timestamp)}
                          </td>
                          <td className="px-2 py-1.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                            {sample.cpu_usage.toFixed(0)}%
                          </td>
                          <td className="px-2 py-1.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                            {sample.memory_usage.toFixed(0)}%
                          </td>
                          <td className="px-2 py-1.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                            {formatBytes(sample.outbound_bytes)}
                          </td>
                          <td className="px-2 py-1.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                            {sample.dns_queries}
                          </td>
                          <td className="px-2 py-1.5 text-right tabular-nums text-[var(--sx-text-secondary)]">
                            {sample.failed_logins}
                          </td>
                          <td className="px-2 py-1.5">
                            {sample.is_anomalous && (
                              <span className="text-[10px] font-semibold uppercase text-[#f0958a]">
                                anomalous
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                )}
              </section>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}
