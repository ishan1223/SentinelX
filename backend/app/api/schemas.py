"""Pydantic response/request models for the API."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    simulated_data: bool


class Endpoint(BaseModel):
    id: str
    name: str
    type: Literal["system", "firewall", "router"]
    ip_address: str
    status: str
    risk_score: float
    last_seen: str


class EndpointListResponse(BaseModel):
    count: int
    endpoints: list[Endpoint]
    notice: str


class TelemetrySample(BaseModel):
    hostname: str
    timestamp: str
    cpu_usage: float
    memory_usage: float
    network_connections: int
    inbound_bytes: int
    outbound_bytes: int
    dns_queries: int
    failed_logins: int
    successful_logins: int
    new_processes: int
    unique_destinations: int
    is_anomalous: bool


class TelemetryResponse(BaseModel):
    hostname: str
    count: int
    samples: list[TelemetrySample]
    notice: str


class SimulationActionResponse(BaseModel):
    hostname: str
    compromised: bool
    compromised_since: str | None
    affected_signals: list[str]
    sample: TelemetrySample


class SimulationResetResponse(BaseModel):
    reset_hosts: list[str]
    notice: str


class ContributingSignalOut(BaseModel):
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: Literal["increase", "decrease"]
    note: str


class ModelInfo(BaseModel):
    method: str
    trained_at: str | None
    training_samples: int


class RiskResponse(BaseModel):
    hostname: str
    timestamp: str
    anomaly_score: float
    compromise_probability: float
    severity: Literal["low", "medium", "high", "critical"]
    correlated_signal_count: int
    contributing_signals: list[ContributingSignalOut]
    model_info: ModelInfo
    notice: str


class EvidenceItemOut(BaseModel):
    signal: str
    observed: float
    baseline: float
    baseline_range: tuple[float, float]
    deviation: float
    deviation_pct: float | None
    contribution: float
    direction: Literal["increase", "decrease"]
    severity: str


class ExplanationResponse(BaseModel):
    hostname: str
    timestamp: str
    severity: str
    summary: str
    evidence: list[EvidenceItemOut]
    recommended_actions: list[str]
    notice: str


class IncidentResponse(BaseModel):
    incident_id: str
    hostname: str
    created_at: str
    updated_at: str
    severity: str
    compromise_probability: float
    anomaly_score: float
    status: Literal["OPEN", "INVESTIGATING", "RESOLVED"]
    summary: str
    evidence: list[EvidenceItemOut]
    recommended_actions: list[str]


class IncidentListResponse(BaseModel):
    count: int
    incidents: list[IncidentResponse]
    notice: str


class IncidentStatusUpdate(BaseModel):
    status: Literal["OPEN", "INVESTIGATING", "RESOLVED"]
