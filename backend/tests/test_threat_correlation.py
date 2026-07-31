"""Unit tests for the rule-based threat-correlation fusion layer."""

from app.services.anomaly_detection import FEATURES, AnomalyResult, FeatureDeviation
from app.services.threat_correlation import assess


def make_result(anomaly_score: float, z_scores: dict[str, float]) -> AnomalyResult:
    # Mirror production: AnomalyResult.deviations always covers every
    # tracked feature (quiet ones included), since correlation breadth is
    # computed as a fraction of the *whole* feature set.
    all_z_scores = {feature: z_scores.get(feature, 0.0) for feature in FEATURES}
    deviations = [
        FeatureDeviation(
            feature=feature,
            value=100.0,
            baseline_mean=50.0,
            baseline_std=10.0,
            z_score=z,
            direction="increase" if z >= 0 else "decrease",
        )
        for feature, z in all_z_scores.items()
    ]
    deviations.sort(key=lambda d: abs(d.z_score), reverse=True)
    return AnomalyResult(
        hostname="HOST-TEST",
        timestamp="2026-01-01T00:00:00+00:00",
        anomaly_score=anomaly_score,
        raw_isolation_score=0.0,
        deviations=deviations,
    )


def test_all_quiet_signals_yield_low_severity_and_no_contributing_signals():
    result = make_result(anomaly_score=5.0, z_scores={"cpu_usage": 0.2, "memory_usage": -0.1})
    assessment = assess(result)
    assert assessment.severity == "low"
    assert assessment.correlated_signal_count == 0
    assert assessment.contributing_signals == []
    assert assessment.compromise_probability < 25


def test_many_severe_correlated_signals_yield_high_or_critical_severity():
    result = make_result(
        anomaly_score=95.0,
        z_scores={
            "outbound_bytes": 9.0,
            "dns_queries": 7.5,
            "new_processes": 6.0,
            "failed_logins": 5.0,
            "unique_destinations": 8.0,
        },
    )
    assessment = assess(result)
    assert assessment.severity in {"high", "critical"}
    assert assessment.correlated_signal_count == 5
    assert assessment.compromise_probability > 75
    assert len(assessment.contributing_signals) == 5
    # Sorted descending by severity.
    zs = [abs(s.z_score) for s in assessment.contributing_signals]
    assert zs == sorted(zs, reverse=True)


def test_single_moderate_deviation_does_not_dominate_the_score():
    result = make_result(anomaly_score=30.0, z_scores={"cpu_usage": 2.5})
    assessment = assess(result)
    assert assessment.correlated_signal_count == 1
    assert assessment.severity in {"low", "medium"}


def test_more_correlated_signals_increase_probability_at_fixed_anomaly_score():
    one_signal = assess(make_result(anomaly_score=50.0, z_scores={"cpu_usage": 4.0}))
    many_signals = assess(
        make_result(
            anomaly_score=50.0,
            z_scores={
                "cpu_usage": 4.0,
                "outbound_bytes": 4.0,
                "dns_queries": 4.0,
                "failed_logins": 4.0,
            },
        )
    )
    assert many_signals.compromise_probability > one_signal.compromise_probability
