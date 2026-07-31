import { useCallback, useRef, useState } from "react";
import {
  fetchEndpointExplanation,
  fetchEndpointRisk,
  fetchIncidents,
  fetchTelemetry,
  triggerCompromise,
  triggerReset,
  updateIncidentStatus,
  type ExplanationResponse,
  type Incident,
  type RiskResponse,
  type TelemetrySample,
} from "../lib/api";

export const DEMO_HOSTNAME = "HOST-042";

const MIN_CORRELATED_SIGNALS = 2;
const HIGH_SEVERITY_TIERS = new Set(["high", "critical"]);
const STAGE_PAUSE_MS = 1100;

export type DemoStage =
  | "idle"
  | "triggering"
  | "telemetry"
  | "anomaly"
  | "correlated"
  | "compromise"
  | "incident"
  | "explanation"
  | "complete"
  | "resetting";

export type LogTone = "info" | "warning" | "critical" | "success";

export interface DemoLogEntry {
  id: string;
  time: string;
  tone: LogTone;
  title: string;
  detail?: string;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function nowLabel(): string {
  return new Date().toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/**
 * Orchestrates the interactive demo walkthrough sequence.
 */
export function useDemoSequence() {
  const [stage, setStage] = useState<DemoStage>("idle");
  const [log, setLog] = useState<DemoLogEntry[]>([]);
  const [telemetrySample, setTelemetrySample] = useState<TelemetrySample | null>(null);
  const [risk, setRisk] = useState<RiskResponse | null>(null);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runToken = useRef(0);
  const logIdRef = useRef(0);

  const pushLog = useCallback((entry: Omit<DemoLogEntry, "id" | "time">) => {
    logIdRef.current += 1;
    setLog((prev) => [...prev, { ...entry, id: `log-${logIdRef.current}`, time: nowLabel() }]);
  }, []);

  const start = useCallback(async () => {
    const token = ++runToken.current;
    const current = () => token === runToken.current;

    setError(null);
    setTelemetrySample(null);
    setRisk(null);
    setIncident(null);
    setExplanation(null);
    setLog([]);

    try {
      setStage("triggering");
      pushLog({
        tone: "info",
        title: "Triggering simulated compromise",
        detail: `Requesting POST /api/simulation/compromise for ${DEMO_HOSTNAME}.`,
      });
      await triggerCompromise(DEMO_HOSTNAME);
      if (!current()) return;

      await sleep(700);
      if (!current()) return;
      setStage("telemetry");
      const telemetryResp = await fetchTelemetry(DEMO_HOSTNAME, 1);
      if (!current()) return;
      const sample = telemetryResp.samples[telemetryResp.samples.length - 1] ?? null;
      setTelemetrySample(sample);
      pushLog({
        tone: sample?.is_anomalous ? "warning" : "info",
        title: sample?.is_anomalous ? "Anomalous telemetry captured" : "Telemetry captured",
        detail: sample
          ? `outbound ${sample.outbound_bytes.toLocaleString()} B · dns ${sample.dns_queries} · failed logins ${sample.failed_logins}`
          : "No telemetry sample returned.",
      });

      await sleep(STAGE_PAUSE_MS);
      if (!current()) return;
      setStage("anomaly");
      const riskResp = await fetchEndpointRisk(DEMO_HOSTNAME);
      if (!current()) return;
      setRisk(riskResp);
      pushLog({
        tone: "warning",
        title: "BEHAVIOURAL ANOMALY DETECTED",
        detail: `IsolationForest anomaly score: ${riskResp.anomaly_score.toFixed(0)}% (vs. this host's own learned baseline).`,
      });

      await sleep(STAGE_PAUSE_MS);
      if (!current()) return;
      if (riskResp.correlated_signal_count >= MIN_CORRELATED_SIGNALS) {
        setStage("correlated");
        const signalNames = riskResp.contributing_signals.map((s) => s.feature).join(", ");
        pushLog({
          tone: "warning",
          title: "MULTIPLE SIGNALS CORRELATED",
          detail: `${riskResp.correlated_signal_count} independent signals deviating together: ${signalNames}.`,
        });
        await sleep(STAGE_PAUSE_MS);
        if (!current()) return;
      }

      if (HIGH_SEVERITY_TIERS.has(riskResp.severity)) {
        setStage("compromise");
        pushLog({
          tone: "critical",
          title: "POSSIBLE SYSTEM COMPROMISE",
          detail: `Compromise probability ${riskResp.compromise_probability.toFixed(0)}% · severity ${riskResp.severity.toUpperCase()}.`,
        });
        await sleep(STAGE_PAUSE_MS);
        if (!current()) return;
      }

      setStage("incident");
      const incidentsResp = await fetchIncidents("OPEN");
      if (!current()) return;
      const match = incidentsResp.incidents.find((i) => i.hostname === DEMO_HOSTNAME) ?? null;
      setIncident(match);
      if (match) {
        pushLog({
          tone: "critical",
          title: "HIGH RISK INCIDENT",
          detail: `${match.incident_id} opened for ${match.hostname} — status ${match.status}.`,
        });
      } else {
        pushLog({
          tone: "info",
          title: "No incident opened this run",
          detail: "Compromise probability stayed below the incident threshold — see the full dashboard for live risk.",
        });
      }

      await sleep(STAGE_PAUSE_MS);
      if (!current()) return;
      setStage("explanation");
      const explanationResp = await fetchEndpointExplanation(DEMO_HOSTNAME);
      if (!current()) return;
      setExplanation(explanationResp);
      pushLog({
        tone: "success",
        title: "Explanation generated",
        detail: `${explanationResp.evidence.length} evidence signals · ${explanationResp.recommended_actions.length} recommended actions.`,
      });

      await sleep(500);
      if (!current()) return;
      setStage("complete");
    } catch (err) {
      if (current()) {
        setError(err instanceof Error ? err.message : "Demo sequence failed");
        setStage("idle");
      }
    }
  }, [pushLog]);

  const reset = useCallback(async () => {
    const token = ++runToken.current;
    const current = () => token === runToken.current;

    setStage("resetting");
    setError(null);
    try {
      await triggerReset();
      if (!current()) return;

      // Auto-resolve active incidents on the demo host so the sequence can be rerun cleanly
      const [openList, investigatingList] = await Promise.all([
        fetchIncidents("OPEN"),
        fetchIncidents("INVESTIGATING"),
      ]);
      const active = [...openList.incidents, ...investigatingList.incidents].filter(
        (i) => i.hostname === DEMO_HOSTNAME,
      );
      await Promise.all(active.map((i) => updateIncidentStatus(i.incident_id, "RESOLVED")));
      if (!current()) return;
    } catch (err) {
      if (current()) {
        setError(err instanceof Error ? err.message : "Failed to reset demo");
      }
    } finally {
      if (current()) {
        setTelemetrySample(null);
        setRisk(null);
        setIncident(null);
        setExplanation(null);
        setLog([]);
        setStage("idle");
      }
    }
  }, []);

  return {
    stage,
    log,
    telemetrySample,
    risk,
    incident,
    explanation,
    error,
    start,
    reset,
    isRunning: stage !== "idle" && stage !== "complete",
  };
}
