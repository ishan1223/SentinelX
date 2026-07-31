import { useEffect, useState } from "react";
import {
  fetchEndpointExplanation,
  fetchEndpointRisk,
  fetchTelemetry,
  type ExplanationResponse,
  type RiskResponse,
  type TelemetrySample,
} from "../lib/api";

export interface InvestigationData {
  risk: RiskResponse | null;
  explanation: ExplanationResponse | null;
  telemetry: TelemetrySample[];
  loading: boolean;
  error: string | null;
}

export function useInvestigation(
  hostname: string | null,
  refreshToken: number,
): InvestigationData {
  const [risk, setRisk] = useState<RiskResponse | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetrySample[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hostname) return;
    let cancelled = false;
    setLoading(true);

    async function load() {
      try {
        const [riskResp, explanationResp, telemetryResp] = await Promise.all([
          fetchEndpointRisk(hostname as string),
          fetchEndpointExplanation(hostname as string),
          fetchTelemetry(hostname as string, 15),
        ]);
        if (cancelled) return;
        setRisk(riskResp);
        setExplanation(explanationResp);
        setTelemetry(telemetryResp.samples);
        setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load investigation data",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [hostname, refreshToken]);

  return { risk, explanation, telemetry, loading, error };
}
