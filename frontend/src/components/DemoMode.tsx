import { DEMO_HOSTNAME, useDemoSequence, type DemoLogEntry, type LogTone } from "../hooks/useDemoSequence";
import type { EndpointItem, RiskResponse } from "../lib/api";
import { formatBytes, formatSignalLabel } from "../lib/format";
import { isHealthy, severityColor, statusTierColor, statusTierLabel } from "../lib/severity";
import { ErrorNotice } from "./StateNotice";
import { StatusLegend } from "./StatusLegend";

const TONE_COLOR: Record<LogTone, string> = {
  info: "var(--sx-text-secondary)",
  warning: "#fab219",
  critical: "#d03b3b",
  success: "#0ca30c",
};

const STEPS: { key: string; label: string }[] = [
  { key: "telemetry", label: "Telemetry Anomaly" },
  { key: "anomaly", label: "Anomaly Detection" },
  { key: "correlated", label: "Correlated Risk Increase" },
  { key: "incident", label: "Incident Creation" },
  { key: "explanation", label: "Explanation" },
];

function StepIndicator({
  label,
  done,
  active,
}: {
  label: string;
  done: boolean;
  active: boolean;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold"
        style={{
          borderColor: done ? "#0ca30c" : active ? "var(--sx-accent)" : "var(--sx-border)",
          backgroundColor: done ? "#0ca30c1a" : active ? "var(--sx-accent)1a" : "transparent",
          color: done ? "#0ca30c" : active ? "var(--sx-accent)" : "var(--sx-text-muted)",
        }}
      >
        {done ? "✓" : active ? "…" : ""}
      </span>
      <span
        className="text-sm"
        style={{
          color: done || active ? "var(--sx-text-primary)" : "var(--sx-text-muted)",
          fontWeight: active ? 600 : 400,
        }}
      >
        {label}
      </span>
    </div>
  );
}

function LogRow({ entry, isLatest }: { entry: DemoLogEntry; isLatest: boolean }) {
  return (
    <li className="flex gap-3 border-b border-[var(--sx-border)] py-2.5 last:border-0">
      <span className="mt-0.5 shrink-0 font-mono text-[11px] text-[var(--sx-text-muted)]">
        {entry.time}
      </span>
      <div>
        <p
          className={isLatest ? "text-base font-bold tracking-wide" : "text-xs font-semibold"}
          style={{ color: TONE_COLOR[entry.tone] }}
        >
          {entry.title}
        </p>
        {entry.detail && (
          <p className="mt-0.5 text-xs text-[var(--sx-text-secondary)]">{entry.detail}</p>
        )}
      </div>
    </li>
  );
}

export function DemoMode({
  endpoints,
  risks,
}: {
  endpoints: EndpointItem[];
  risks: Record<string, RiskResponse>;
}) {
  const {
    stage,
    log,
    telemetrySample,
    risk,
    incident,
    explanation,
    error,
    start,
    reset,
    isRunning,
  } = useDemoSequence();

  const allHealthy = endpoints.every((e) => {
    const r = risks[e.id];
    return !r || isHealthy(r.severity);
  });

  const latestEntry = log[log.length - 1];

  return (
    <div className="mx-auto max-w-[1100px] px-6 py-8">
      <div className="mb-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--sx-accent)]">
          Demo Mode
        </p>
        <h2 className="mt-1 text-2xl font-semibold text-[var(--sx-text-primary)]">
          Behavioural compromise detection, end to end
        </h2>
        <p className="mx-auto mt-2 max-w-xl text-sm text-[var(--sx-text-secondary)]">
          Every value below comes from a real request to the live SentinelX backend — nothing
          on this screen is scripted or faked. Target host: <strong>{DEMO_HOSTNAME}</strong>.
        </p>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorNotice label={error} />
        </div>
      )}

      <div className="mb-6 rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] px-4 py-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
            Initial State
          </p>
          <StatusLegend />
        </div>
        <div className="flex flex-wrap gap-2">
          {endpoints.map((e) => {
            const r = risks[e.id];
            const color = r ? statusTierColor(r.severity) : "var(--sx-text-muted)";
            const label = r ? statusTierLabel(r.severity) : "Unknown";
            return (
              <span
                key={e.id}
                title={`${e.id}: ${label}`}
                className="inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium"
                style={{ borderColor: `${color}40`, backgroundColor: `${color}14`, color }}
              >
                <span aria-hidden className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
                {e.id}
              </span>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-[var(--sx-text-muted)]">
          {allHealthy
            ? "All endpoints currently healthy."
            : "One or more endpoints are not currently healthy — reset the demo before presenting."}
        </p>
      </div>

      <div className="mb-6 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={start}
          disabled={isRunning}
          className="rounded-md border border-[#d03b3b66] bg-[#d03b3b1f] px-6 py-3 text-base font-semibold text-[#f0958a] transition hover:bg-[#d03b3b33] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRunning ? "Running…" : "Simulate Compromise"}
        </button>
        <button
          type="button"
          onClick={reset}
          disabled={stage === "resetting"}
          className="rounded-md border border-[var(--sx-border)] bg-transparent px-6 py-3 text-base font-medium text-[var(--sx-text-secondary)] transition hover:border-[var(--sx-text-secondary)] hover:text-[var(--sx-text-primary)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {stage === "resetting" ? "Resetting…" : "Reset Demo"}
        </button>
      </div>

      {latestEntry && (
        <div
          className="mb-6 rounded-lg border px-5 py-6 text-center transition-colors"
          style={{
            borderColor: `${TONE_COLOR[latestEntry.tone]}55`,
            backgroundColor: `${TONE_COLOR[latestEntry.tone]}12`,
          }}
        >
          <p
            className="text-2xl font-extrabold tracking-wide sm:text-3xl"
            style={{ color: TONE_COLOR[latestEntry.tone] }}
          >
            {latestEntry.title}
          </p>
          {latestEntry.detail && (
            <p className="mt-2 text-sm text-[var(--sx-text-secondary)]">{latestEntry.detail}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[220px_1fr]">
        <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
            Progression
          </p>
          <div className="space-y-3">
            {STEPS.map((step) => {
              const done =
                (step.key === "telemetry" && !!telemetrySample) ||
                (step.key === "anomaly" && !!risk) ||
                (step.key === "correlated" && !!risk && risk.correlated_signal_count >= 2) ||
                (step.key === "incident" && !!incident) ||
                (step.key === "explanation" && !!explanation);
              const active = stage === step.key;
              return <StepIndicator key={step.key} label={step.label} done={done} active={active} />;
            })}
          </div>
        </div>

        <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] p-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
            Live Event Log
          </p>
          {log.length === 0 ? (
            <p className="py-6 text-center text-sm text-[var(--sx-text-muted)]">
              Click Simulate Compromise to begin.
            </p>
          ) : (
            <ul>
              {log.map((entry, index) => (
                <LogRow key={entry.id} entry={entry} isLatest={index === log.length - 1} />
              ))}
            </ul>
          )}
        </div>
      </div>

      {(telemetrySample || risk || incident || explanation) && (
        <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2">
          {telemetrySample && (
            <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                Telemetry Sample
              </p>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <dt className="text-[var(--sx-text-muted)]">Outbound</dt>
                <dd className="text-right tabular-nums text-[var(--sx-text-primary)]">
                  {formatBytes(telemetrySample.outbound_bytes)}
                </dd>
                <dt className="text-[var(--sx-text-muted)]">DNS Queries</dt>
                <dd className="text-right tabular-nums text-[var(--sx-text-primary)]">
                  {telemetrySample.dns_queries}
                </dd>
                <dt className="text-[var(--sx-text-muted)]">Failed Logins</dt>
                <dd className="text-right tabular-nums text-[var(--sx-text-primary)]">
                  {telemetrySample.failed_logins}
                </dd>
                <dt className="text-[var(--sx-text-muted)]">Flagged Anomalous</dt>
                <dd
                  className="text-right font-semibold"
                  style={{ color: telemetrySample.is_anomalous ? "#d03b3b" : "#0ca30c" }}
                >
                  {telemetrySample.is_anomalous ? "Yes" : "No"}
                </dd>
              </dl>
            </div>
          )}

          {risk && (
            <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                Risk Assessment
              </p>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <dt className="text-[var(--sx-text-muted)]">Anomaly Score</dt>
                <dd className="text-right tabular-nums text-[var(--sx-text-primary)]">
                  {risk.anomaly_score.toFixed(1)}%
                </dd>
                <dt className="text-[var(--sx-text-muted)]">Compromise Probability</dt>
                <dd
                  className="text-right font-semibold tabular-nums"
                  style={{ color: severityColor(risk.severity) }}
                >
                  {risk.compromise_probability.toFixed(1)}%
                </dd>
                <dt className="text-[var(--sx-text-muted)]">Correlated Signals</dt>
                <dd className="text-right tabular-nums text-[var(--sx-text-primary)]">
                  {risk.correlated_signal_count}
                </dd>
                <dt className="text-[var(--sx-text-muted)]">Severity</dt>
                <dd className="text-right font-semibold" style={{ color: severityColor(risk.severity) }}>
                  {risk.severity.toUpperCase()}
                </dd>
              </dl>
            </div>
          )}

          {incident && (
            <div className="rounded-lg border border-[#d03b3b40] bg-[#d03b3b0f] p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                Incident
              </p>
              <p className="text-sm">
                <span className="font-mono text-[var(--sx-text-muted)]">{incident.incident_id}</span>{" "}
                <span className="font-semibold text-[#f0958a]">{incident.status}</span>
              </p>
              <p className="mt-2 text-xs text-[var(--sx-text-secondary)]">{incident.summary}</p>
            </div>
          )}

          {explanation && (
            <div className="rounded-lg border border-[var(--sx-border)] bg-[var(--sx-surface)] p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--sx-text-muted)]">
                Explanation &amp; Recommended Actions
              </p>
              <p className="text-xs text-[var(--sx-text-secondary)]">{explanation.summary}</p>
              {explanation.evidence.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {explanation.evidence.map((e) => (
                    <span
                      key={e.signal}
                      className="rounded border border-[var(--sx-border)] px-1.5 py-0.5 text-[10px] text-[var(--sx-text-muted)]"
                    >
                      {formatSignalLabel(e.signal)}
                    </span>
                  ))}
                </div>
              )}
              {explanation.recommended_actions.length > 0 && (
                <ol className="mt-2 space-y-1 text-xs text-[var(--sx-text-secondary)]">
                  {explanation.recommended_actions.slice(0, 3).map((action, index) => (
                    <li key={action}>
                      {index + 1}. {action}
                    </li>
                  ))}
                </ol>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
