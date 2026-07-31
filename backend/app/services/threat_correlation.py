"""Threat-correlation service.

Fuses the Isolation Forest anomaly score with per-feature statistical deviations
to compute compromise probability and severity tiers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.anomaly_detection import AnomalyResult, FeatureDeviation

Z_SIGNIFICANCE_THRESHOLD = 2.0
MIN_CORRELATED_SIGNALS_FOR_BOOST = 2
MAX_CONTRIBUTING_SIGNALS = 5
MAX_EXPECTED_AVG_SEVERITY = 6.0  # |z| considered "maximally severe" for scaling

SEVERITY_THRESHOLDS = (
    (75, "critical"),
    (50, "high"),
    (25, "medium"),
)

# Fusion weights: ML anomaly score carries the most weight since it already
# summarizes the full feature vector; correlation breadth and deviation
# severity add explicit credit for the multi-signal pattern a real
# compromise produces.
WEIGHT_ANOMALY_SCORE = 0.5
WEIGHT_CORRELATION_BREADTH = 0.3
WEIGHT_SEVERITY = 0.2


@dataclass
class ContributingSignal:
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: str
    note: str


@dataclass
class ThreatAssessment:
    hostname: str
    timestamp: str
    anomaly_score: float
    compromise_probability: float
    severity: str
    correlated_signal_count: int
    contributing_signals: list[ContributingSignal]


def _severity_label(compromise_probability: float) -> str:
    for threshold, label in SEVERITY_THRESHOLDS:
        if compromise_probability >= threshold:
            return label
    return "low"


def _describe(deviation: FeatureDeviation) -> str:
    return (
        f"{deviation.feature} is {abs(deviation.z_score):.1f} standard deviations "
        f"{deviation.direction}d relative to this host's own normal baseline "
        f"({deviation.value:g} vs. baseline mean {deviation.baseline_mean:g})"
    )


def assess(result: AnomalyResult) -> ThreatAssessment:
    significant = [d for d in result.deviations if abs(d.z_score) >= Z_SIGNIFICANCE_THRESHOLD]

    correlated_signal_count = len(significant)

    # Require at least 2 independent signals to deviate to filter out noise
    if correlated_signal_count >= MIN_CORRELATED_SIGNALS_FOR_BOOST:
        correlation_breadth = min(correlated_signal_count / len(result.deviations), 1.0) if result.deviations else 0.0
        avg_severity = sum(abs(d.z_score) for d in significant) / correlated_signal_count
        severity_factor = min(avg_severity / MAX_EXPECTED_AVG_SEVERITY, 1.0)
    else:
        correlation_breadth = 0.0
        severity_factor = 0.0

    compromise_probability = (
        WEIGHT_ANOMALY_SCORE * result.anomaly_score
        + WEIGHT_CORRELATION_BREADTH * correlation_breadth * 100
        + WEIGHT_SEVERITY * severity_factor * 100
    )
    compromise_probability = round(min(max(compromise_probability, 0.0), 100.0), 2)

    contributing_signals = [
        ContributingSignal(
            feature=d.feature,
            value=d.value,
            baseline_mean=d.baseline_mean,
            baseline_std=d.baseline_std,
            z_score=d.z_score,
            direction=d.direction,
            note=_describe(d),
        )
        for d in significant[:MAX_CONTRIBUTING_SIGNALS]
    ]

    return ThreatAssessment(
        hostname=result.hostname,
        timestamp=result.timestamp,
        anomaly_score=result.anomaly_score,
        compromise_probability=compromise_probability,
        severity=_severity_label(compromise_probability),
        correlated_signal_count=correlated_signal_count,
        contributing_signals=contributing_signals,
    )
