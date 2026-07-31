import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchEndpoints,
  fetchEndpointRisk,
  fetchIncidents,
  triggerCompromise,
  triggerReset,
  type EndpointItem,
  type Incident,
  type RiskResponse,
} from "../lib/api";

const POLL_INTERVAL_MS = 7000;

export interface DashboardData {
  endpoints: EndpointItem[];
  risks: Record<string, RiskResponse>;
  incidents: Incident[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  lastUpdated: Date | null;
  simulationPending: boolean;
  simulationMessage: string | null;
  refetch: () => void;
  simulateCompromise: () => Promise<void>;
  resetSimulation: () => Promise<void>;
}

async function loadAll(): Promise<{
  endpoints: EndpointItem[];
  risks: Record<string, RiskResponse>;
  incidents: Incident[];
}> {
  const endpointsResp = await fetchEndpoints();
  const [riskResults, incidentsResp] = await Promise.all([
    Promise.allSettled(endpointsResp.endpoints.map((e) => fetchEndpointRisk(e.id))),
    fetchIncidents(),
  ]);

  const risks: Record<string, RiskResponse> = {};
  riskResults.forEach((result, index) => {
    if (result.status === "fulfilled") {
      risks[endpointsResp.endpoints[index].id] = result.value;
    }
  });

  return { endpoints: endpointsResp.endpoints, risks, incidents: incidentsResp.incidents };
}

export function useDashboardData(): DashboardData {
  const [endpoints, setEndpoints] = useState<EndpointItem[]>([]);
  const [risks, setRisks] = useState<Record<string, RiskResponse>>({});
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [simulationPending, setSimulationPending] = useState(false);
  const [simulationMessage, setSimulationMessage] = useState<string | null>(null);

  const hasLoadedOnce = useRef(false);
  const messageTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (isBackground: boolean) => {
    if (isBackground) setRefreshing(true);
    try {
      const result = await loadAll();
      setEndpoints(result.endpoints);
      setRisks(result.risks);
      setIncidents(result.incidents);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to reach the SentinelX backend";
      setError(message);
    } finally {
      if (isBackground) setRefreshing(false);
      if (!hasLoadedOnce.current) {
        hasLoadedOnce.current = true;
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    load(false);
    const interval = setInterval(() => load(true), POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [load]);

  const showMessage = useCallback((message: string) => {
    setSimulationMessage(message);
    if (messageTimeoutRef.current) clearTimeout(messageTimeoutRef.current);
    messageTimeoutRef.current = setTimeout(() => setSimulationMessage(null), 6000);
  }, []);

  const simulateCompromise = useCallback(async () => {
    setSimulationPending(true);
    try {
      const result = await triggerCompromise("HOST-042");
      showMessage(`Compromise simulation triggered on ${result.hostname}.`);
      await load(true);
    } catch (err) {
      showMessage(
        err instanceof Error
          ? `Failed to trigger compromise: ${err.message}`
          : "Failed to trigger compromise simulation.",
      );
    } finally {
      setSimulationPending(false);
    }
  }, [load, showMessage]);

  const resetSimulation = useCallback(async () => {
    setSimulationPending(true);
    try {
      const result = await triggerReset();
      showMessage(
        result.reset_hosts.length > 0
          ? `Environment reset. Restored: ${result.reset_hosts.join(", ")}.`
          : "Environment already normal — nothing to reset.",
      );
      await load(true);
    } catch (err) {
      showMessage(
        err instanceof Error
          ? `Failed to reset simulation: ${err.message}`
          : "Failed to reset simulation.",
      );
    } finally {
      setSimulationPending(false);
    }
  }, [load, showMessage]);

  const refetch = useCallback(() => {
    load(true);
  }, [load]);

  return {
    endpoints,
    risks,
    incidents,
    loading,
    refreshing,
    error,
    lastUpdated,
    simulationPending,
    simulationMessage,
    refetch,
    simulateCompromise,
    resetSimulation,
  };
}
