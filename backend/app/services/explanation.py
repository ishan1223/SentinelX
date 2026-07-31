"""Evidence-based explainability service.

Generates structured explanations and recommended response actions
directly from telemetry deviations and baseline statistics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.threat_correlation import ContributingSignal, ThreatAssessment

# Friendly, human-readable label per raw telemetry feature. Deliberately
# generic/behavioural ("outbound_traffic") rather than implying any
# particular threat category.
SIGNAL_LABELS: dict[str, str] = {
    "cpu_usage": "cpu_utilization",
    "memory_usage": "memory_utilization",
    "network_connections": "network_connection_count",
    "inbound_bytes": "inbound_traffic",
    "outbound_bytes": "outbound_traffic",
    "dns_queries": "dns_query_volume",
    "failed_logins": "failed_authentication",
    "new_processes": "process_creation",
    "unique_destinations": "destination_diversity",
}

# Defensive, non-destructive investigative action per raw feature. Never an
# automatic remediation -- these are recommendations for a human analyst.
SIGNAL_ACTIONS: dict[str, str] = {
    "outbound_bytes": "Inspect outbound network connections for unauthorized or unexpected data transfer.",
    "inbound_bytes": "Inspect inbound network connections for unexpected sources.",
    "dns_queries": "Review DNS query logs for unusual domains or query patterns.",
    "unique_destinations": "Review network destination logs for unfamiliar or high-risk endpoints.",
    "new_processes": "Investigate newly created processes on the endpoint for legitimacy.",
    "failed_logins": "Review authentication logs for brute-force or credential-stuffing activity.",
    "network_connections": "Review active network connections and sessions for unauthorized activity.",
    "cpu_usage": "Review running workloads for unauthorized or resource-intensive processes.",
    "memory_usage": "Review running workloads for unauthorized or resource-intensive processes.",
}

# Bucket labels for a single signal's own deviation magnitude, purely a
# readout of |z-score| -- not a separate judgement call.
_SEVERITY_BUCKETS = (
    (7.0, "severe"),
    (4.0, "high"),
    (0.0, "moderate"),
)


@dataclass
class EvidenceItem:
    signal: str
    observed: float
    baseline: float
    baseline_range: tuple[float, float]
    deviation: float  # standard deviations from baseline (z-score)
    deviation_pct: float | None  # % change from baseline mean; None if baseline mean is 0
    contribution: float  # % share of total evidence weight, sums to ~100 across items
    direction: str
    severity: str


@dataclass
class Explanation:
    hostname: str
    timestamp: str
    severity: str
    summary: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)


def _signal_label(feature: str) -> str:
    return SIGNAL_LABELS.get(feature, feature)


def _signal_severity(abs_z: float) -> str:
    for threshold, label in _SEVERITY_BUCKETS:
        if abs_z >= threshold:
            return label
    return "moderate"


def _deviation_pct(signal: ContributingSignal) -> float | None:
    if signal.baseline_mean == 0:
        # No meaningful baseline to divide by (e.g. a host that normally
        # never has failed logins) -- the z-score already captures the
        # deviation; percent-change is undefined, not "infinite risk".
        return None
    return (signal.value - signal.baseline_mean) / abs(signal.baseline_mean) * 100


def _build_evidence(signals: list[ContributingSignal]) -> list[EvidenceItem]:
    total_weight = sum(abs(s.z_score) for s in signals)
    evidence = []
    for s in signals:
        contribution = (abs(s.z_score) / total_weight * 100) if total_weight else 0.0
        pct = _deviation_pct(s)
        evidence.append(
            EvidenceItem(
                signal=_signal_label(s.feature),
                observed=s.value,
                baseline=s.baseline_mean,
                baseline_range=(
                    round(s.baseline_mean - s.baseline_std, 2),
                    round(s.baseline_mean + s.baseline_std, 2),
                ),
                deviation=s.z_score,
                deviation_pct=round(pct, 1) if pct is not None else None,
                contribution=round(contribution, 1),
                direction=s.direction,
                severity=_signal_severity(abs(s.z_score)),
            )
        )
    return evidence


def _summary(hostname: str, severity: str, evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return (
            f"{hostname} currently matches its established behavioural baseline. "
            f"No significant deviation was observed across the monitored signals; "
            f"no investigative action is required at this time."
        )

    ranked = sorted(evidence, key=lambda e: e.contribution, reverse=True)
    signal_phrases = [
        f"{e.signal} ({'+' if e.direction == 'increase' else '-'}{abs(e.deviation):.1f} std dev, "
        f"{e.contribution:.0f}% of the finding)"
        for e in ranked
    ]
    joined = "; ".join(signal_phrases)

    lead = (
        f"{hostname} shows a {severity.upper()} severity behavioural deviation across "
        f"{len(evidence)} correlated signal{'s' if len(evidence) != 1 else ''}: {joined}."
    )

    if len(evidence) >= 2:
        caveat = (
            " This pattern of simultaneous deviation across independent signal families is a "
            "behavioural indicator consistent with possible compromise; it is not a confirmed "
            "attribution -- no specific malware, vulnerability, or attack technique is asserted "
            "based on telemetry alone."
        )
    else:
        caveat = (
            " A single deviating signal can also reflect legitimate load variation; correlate "
            "with additional context before treating this as confirmed malicious activity."
        )

    return lead + caveat


def _recommended_actions(severity: str, evidence: list[EvidenceItem], raw_features: list[str]) -> list[str]:
    if not evidence:
        return ["Continue routine monitoring. No anomalous behaviour detected."]

    actions: list[str] = []
    seen: set[str] = set()
    for feature in raw_features:
        action = SIGNAL_ACTIONS.get(feature)
        if action and action not in seen:
            actions.append(action)
            seen.add(action)

    if severity == "medium":
        actions.append("Increase monitoring frequency and alerting sensitivity for this endpoint.")
    elif severity in ("high", "critical"):
        actions.append("Isolate endpoint from the network pending investigation.")
        actions.append("Preserve telemetry and current system state for forensic investigation.")

    return actions


def explain(assessment: ThreatAssessment) -> Explanation:
    evidence = _build_evidence(assessment.contributing_signals)
    raw_features = [s.feature for s in assessment.contributing_signals]

    return Explanation(
        hostname=assessment.hostname,
        timestamp=assessment.timestamp,
        severity=assessment.severity.upper(),
        summary=_summary(assessment.hostname, assessment.severity, evidence),
        evidence=evidence,
        recommended_actions=_recommended_actions(assessment.severity, evidence, raw_features),
    )
