"""Unit tests for AnomalyDetectionService, independent of the API/DB.

Uses hand-built synthetic telemetry rows so behaviour can be checked against
known-good and known-bad inputs directly, and so we can prove the score is
computed from features (not keyed on hostname).
"""

import random

import pytest

from app.services.anomaly_detection import AnomalyDetectionService, NotTrainedError

FEATURE_DEFAULTS = dict(
    cpu_usage=20.0,
    memory_usage=35.0,
    network_connections=12,
    inbound_bytes=18000,
    outbound_bytes=4500,
    dns_queries=12,
    failed_logins=0,
    successful_logins=0,
    new_processes=1,
    unique_destinations=6,
)


def make_row(hostname: str, timestamp: str, **overrides) -> dict:
    row = {**FEATURE_DEFAULTS, "hostname": hostname, "timestamp": timestamp, "is_anomalous": 0}
    row.update(overrides)
    return row


def make_normal_rows(hostname: str, n: int, rng: random.Random, **base_overrides) -> list[dict]:
    rows = []
    for i in range(n):
        jitter = {
            "cpu_usage": FEATURE_DEFAULTS["cpu_usage"] + rng.gauss(0, 2),
            "memory_usage": FEATURE_DEFAULTS["memory_usage"] + rng.gauss(0, 2),
            "network_connections": max(1, round(FEATURE_DEFAULTS["network_connections"] + rng.gauss(0, 1.5))),
            "inbound_bytes": max(0, round(FEATURE_DEFAULTS["inbound_bytes"] + rng.gauss(0, 1500))),
            "outbound_bytes": max(0, round(FEATURE_DEFAULTS["outbound_bytes"] + rng.gauss(0, 400))),
            "dns_queries": max(0, round(FEATURE_DEFAULTS["dns_queries"] + rng.gauss(0, 2))),
            "new_processes": max(0, round(rng.gauss(1, 0.5))),
            "unique_destinations": max(1, round(FEATURE_DEFAULTS["unique_destinations"] + rng.gauss(0, 1))),
        }
        jitter.update(base_overrides)
        rows.append(make_row(hostname, f"2026-01-01T00:{i:02d}:00+00:00", **jitter))
    return rows


@pytest.fixture
def trained_service():
    rng = random.Random(42)
    rows = make_normal_rows("HOST-A", 30, rng) + make_normal_rows(
        "HOST-B", 30, rng, network_connections=200, inbound_bytes=250000, outbound_bytes=230000
    )
    service = AnomalyDetectionService()
    service.train(rows)
    return service


def test_score_before_train_raises():
    service = AnomalyDetectionService()
    with pytest.raises(NotTrainedError):
        service.score(make_row("HOST-A", "2026-01-01T00:00:00+00:00"))


def test_train_requires_minimum_samples():
    service = AnomalyDetectionService()
    with pytest.raises(ValueError):
        service.train(make_normal_rows("HOST-A", 2, random.Random(1)))


def test_normal_sample_scores_low(trained_service):
    sample = make_row("HOST-A", "2026-01-01T01:00:00+00:00")
    result = trained_service.score(sample)
    assert result.anomaly_score < 60


def test_realistic_multi_signal_compromise_scores_high(trained_service):
    """A single spiked feature among 9 dimensions is a genuinely hard case
    for IsolationForest with only ~30 samples/host of training data -- that
    is a documented, honest limitation of small-sample vanilla Isolation
    Forest, not something this test pretends around. What the simulated
    compromise actually produces (telemetry_engine._apply_compromise) is a
    coordinated shift across most signal families at once, which is exactly
    the pattern the correlation layer is designed to catch and which the ML
    model *should* score as clearly anomalous."""
    from app.services.telemetry_engine import _apply_compromise

    normal = make_row("HOST-A", "2026-01-01T01:00:00+00:00")
    compromised = _apply_compromise(normal)

    result = trained_service.score(compromised)
    assert result.anomaly_score > 80

    top_features = {d.feature for d in result.deviations[:5]}
    assert top_features & {"outbound_bytes", "dns_queries", "failed_logins", "cpu_usage", "memory_usage"}


def test_same_raw_traffic_is_normal_for_host_b_but_anomalous_for_host_a(trained_service):
    """HOST-B's baseline has ~200 connections/~250KB traffic; HOST-A's is
    ~12 connections/~4.5KB. Scoring the identical raw traffic numbers under
    each hostname must produce very different z-scores purely from each
    host's own learned baseline -- proving deviation is computed from data,
    not a hostname -> score lookup table."""
    raw_traffic = dict(network_connections=205, inbound_bytes=252000, outbound_bytes=228000)

    host_b_sample = make_row("HOST-B", "2026-01-01T01:00:00+00:00", failed_logins=15, **raw_traffic)
    result_b = trained_service.score(host_b_sample)
    z_by_feature_b = {d.feature: d.z_score for d in result_b.deviations}
    assert abs(z_by_feature_b["network_connections"]) < 3
    assert abs(z_by_feature_b["outbound_bytes"]) < 3
    assert z_by_feature_b["failed_logins"] >= 9  # clipped at Z_SCORE_CLIP=10

    host_a_sample = make_row("HOST-A", "2026-01-01T01:00:00+00:00", **raw_traffic)
    result_a = trained_service.score(host_a_sample)
    z_by_feature_a = {d.feature: d.z_score for d in result_a.deviations}
    assert z_by_feature_a["network_connections"] >= 9
    assert z_by_feature_a["outbound_bytes"] >= 9


def test_deviations_are_sorted_by_absolute_z_score(trained_service):
    sample = make_row("HOST-A", "2026-01-01T01:00:00+00:00", outbound_bytes=90000)
    result = trained_service.score(sample)
    abs_zs = [abs(d.z_score) for d in result.deviations]
    assert abs_zs == sorted(abs_zs, reverse=True)
