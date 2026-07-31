import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
});

export type Severity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "OPEN" | "INVESTIGATING" | "RESOLVED";
export type EndpointType = "system" | "firewall" | "router";
export type SignalDirection = "increase" | "decrease";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  simulated_data: boolean;
}

export interface EndpointItem {
  id: string;
  name: string;
  type: EndpointType;
  ip_address: string;
  status: string;
  risk_score: number;
  last_seen: string;
}

export interface EndpointListResponse {
  count: number;
  endpoints: EndpointItem[];
  notice: string;
}

export interface TelemetrySample {
  hostname: string;
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  network_connections: number;
  inbound_bytes: number;
  outbound_bytes: number;
  dns_queries: number;
  failed_logins: number;
  successful_logins: number;
  new_processes: number;
  unique_destinations: number;
  is_anomalous: boolean;
}

export interface TelemetryResponse {
  hostname: string;
  count: number;
  samples: TelemetrySample[];
  notice: string;
}

export interface ContributingSignal {
  feature: string;
  value: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  direction: SignalDirection;
  note: string;
}

export interface ModelInfo {
  method: string;
  trained_at: string | null;
  training_samples: number;
}

export interface RiskResponse {
  hostname: string;
  timestamp: string;
  anomaly_score: number;
  compromise_probability: number;
  severity: Severity;
  correlated_signal_count: number;
  contributing_signals: ContributingSignal[];
  model_info: ModelInfo;
  notice: string;
}

export interface EvidenceItem {
  signal: string;
  observed: number;
  baseline: number;
  baseline_range: [number, number];
  deviation: number;
  deviation_pct: number | null;
  contribution: number;
  direction: SignalDirection;
  severity: string;
}

export interface ExplanationResponse {
  hostname: string;
  timestamp: string;
  severity: string;
  summary: string;
  evidence: EvidenceItem[];
  recommended_actions: string[];
  notice: string;
}

export interface Incident {
  incident_id: string;
  hostname: string;
  created_at: string;
  updated_at: string;
  severity: string;
  compromise_probability: number;
  anomaly_score: number;
  status: IncidentStatus;
  summary: string;
  evidence: EvidenceItem[];
  recommended_actions: string[];
}

export interface IncidentListResponse {
  count: number;
  incidents: Incident[];
  notice: string;
}

export interface SimulationActionResponse {
  hostname: string;
  compromised: boolean;
  compromised_since: string | null;
  affected_signals: string[];
  sample: TelemetrySample;
}

export interface SimulationResetResponse {
  reset_hosts: string[];
  notice: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function fetchEndpoints(): Promise<EndpointListResponse> {
  const { data } = await api.get<EndpointListResponse>("/endpoints");
  return data;
}

export async function fetchEndpointRisk(hostname: string): Promise<RiskResponse> {
  const { data } = await api.get<RiskResponse>(`/endpoints/${hostname}/risk`);
  return data;
}

export async function fetchEndpointExplanation(
  hostname: string,
): Promise<ExplanationResponse> {
  const { data } = await api.get<ExplanationResponse>(
    `/endpoints/${hostname}/explanation`,
  );
  return data;
}

export async function fetchTelemetry(
  hostname: string,
  limit = 40,
): Promise<TelemetryResponse> {
  const { data } = await api.get<TelemetryResponse>(`/telemetry/${hostname}`, {
    params: { limit },
  });
  return data;
}

export async function fetchIncidents(status?: IncidentStatus): Promise<IncidentListResponse> {
  const { data } = await api.get<IncidentListResponse>("/incidents", {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function updateIncidentStatus(
  incidentId: string,
  status: IncidentStatus,
): Promise<Incident> {
  const { data } = await api.patch<Incident>(`/incidents/${incidentId}`, { status });
  return data;
}

export async function triggerCompromise(
  hostname = "HOST-042",
): Promise<SimulationActionResponse> {
  const { data } = await api.post<SimulationActionResponse>(
    "/simulation/compromise",
    null,
    { params: { hostname } },
  );
  return data;
}

export async function triggerReset(): Promise<SimulationResetResponse> {
  const { data } = await api.post<SimulationResetResponse>("/simulation/reset");
  return data;
}
