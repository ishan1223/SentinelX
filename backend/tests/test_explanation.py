"""Unit tests for the deterministic evidence-based explanation generator."""

from app.services.explanation import explain
from app.services.threat_correlation import ContributingSignal, ThreatAssessment

FORBIDDEN_SUBSTRINGS = [
    "cve-", "CVE-", "trojan", "ransomware", "cobalt strike", "apt29", "apt ",
    "mimikatz", "emotet", "wannacry", "backdoor.", "malware family",
]


def make_assessment(severity: str, signals: list[ContributingSignal]) -> ThreatAssessment:
    return ThreatAssessment(
        hostname="HOST-TEST",
        timestamp="2026-01-01T00:00:00+00:00",
        anomaly_score=90.0,
        compromise_probability=90.0,
        severity=severity,
        correlated_signal_count=len(signals),
        contributing_signals=signals,
    )


def make_signal(feature, value, mean, std, z) -> ContributingSignal:
    return ContributingSignal(
        feature=feature,
        value=value,
        baseline_mean=mean,
        baseline_std=std,
        z_score=z,
        direction="increase" if z >= 0 else "decrease",
        note=f"{feature} deviated",
    )


def test_no_evidence_produces_reassuring_summary_and_no_drastic_actions():
    assessment = make_assessment("low", [])
    result = explain(assessment)

    assert result.evidence == []
    assert "baseline" in result.summary.lower()
    assert result.recommended_actions == ["Continue routine monitoring. No anomalous behaviour detected."]
    assert result.severity == "LOW"


def test_evidence_fields_are_all_derived_from_input_signal():
    signal = make_signal("outbound_bytes", 73218.0, 4988.08, 850.0, 10.0)
    assessment = make_assessment("critical", [signal])
    result = explain(assessment)

    item = result.evidence[0]
    assert item.signal == "outbound_traffic"  # friendly label, not raw feature name
    assert item.observed == 73218.0
    assert item.baseline == 4988.08
    assert item.baseline_range == (4988.08 - 850.0, 4988.08 + 850.0)
    assert item.deviation == 10.0
    assert item.direction == "increase"
    assert item.severity == "severe"  # |z| >= 7


def test_contribution_percentages_sum_to_100_across_evidence():
    signals = [
        make_signal("outbound_bytes", 100, 10, 5, 8.0),
        make_signal("dns_queries", 100, 10, 5, 6.0),
        make_signal("failed_logins", 5, 0, 0.5, 4.0),
    ]
    assessment = make_assessment("critical", signals)
    result = explain(assessment)

    total_contribution = sum(e.contribution for e in result.evidence)
    assert abs(total_contribution - 100.0) < 0.5

    # The largest |z| carries the largest share.
    assert result.evidence[0].contribution >= result.evidence[1].contribution >= result.evidence[2].contribution


def test_zero_baseline_mean_reports_none_percent_not_infinity():
    signal = make_signal("failed_logins", 10.0, 0.0, 0.5, 10.0)
    assessment = make_assessment("critical", [signal])
    result = explain(assessment)
    assert result.evidence[0].deviation_pct is None


def test_recommended_actions_match_affected_signal_categories():
    signals = [
        make_signal("outbound_bytes", 73218.0, 4988.08, 850.0, 10.0),
        make_signal("new_processes", 9, 0.65, 1.0, 8.0),
    ]
    assessment = make_assessment("critical", signals)
    result = explain(assessment)

    actions_text = " ".join(result.recommended_actions).lower()
    assert "outbound" in actions_text
    assert "process" in actions_text
    assert "isolate" in actions_text
    assert "preserve" in actions_text
    # Never a destructive/automatic action -- only investigate/inspect/isolate/preserve.
    assert not any(word in actions_text for word in ["delete", "kill process", "reformat", "wipe", "shutdown"])


def test_medium_severity_recommends_monitoring_not_isolation():
    signal = make_signal("cpu_usage", 80, 20, 5, 4.0)
    other = make_signal("memory_usage", 75, 35, 5, 3.5)
    assessment = make_assessment("medium", [signal, other])
    result = explain(assessment)

    actions_text = " ".join(result.recommended_actions).lower()
    assert "isolate" not in actions_text
    assert "monitoring" in actions_text


def test_explanation_never_contains_fabricated_attribution():
    signals = [
        make_signal("outbound_bytes", 73218.0, 4988.08, 850.0, 10.0),
        make_signal("dns_queries", 135, 15.25, 12.0, 10.0),
        make_signal("failed_logins", 10, 0.0, 0.5, 10.0),
    ]
    assessment = make_assessment("critical", signals)
    result = explain(assessment)

    full_text = (result.summary + " ".join(result.recommended_actions)).lower()
    for term in FORBIDDEN_SUBSTRINGS:
        assert term.lower() not in full_text


def test_explanation_changes_with_different_telemetry():
    """Same host, two different evidence sets -> materially different
    explanations. Guards against a static/templated non-response."""
    quiet = make_assessment("low", [])
    loud = make_assessment(
        "critical",
        [
            make_signal("outbound_bytes", 73218.0, 4988.08, 850.0, 10.0),
            make_signal("dns_queries", 135, 15.25, 12.0, 10.0),
        ],
    )

    quiet_explanation = explain(quiet)
    loud_explanation = explain(loud)

    assert quiet_explanation.summary != loud_explanation.summary
    assert quiet_explanation.recommended_actions != loud_explanation.recommended_actions
    assert len(quiet_explanation.evidence) == 0
    assert len(loud_explanation.evidence) == 2
