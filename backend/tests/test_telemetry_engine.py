"""White-box tests for the synthetic telemetry generator itself.

These check the generation logic directly so the multi-signal compromise
invariants are verified deterministically, independent of the API layer.
"""

from datetime import datetime, timezone

from app.services import telemetry_engine as engine

REQUIRED_FIELDS = {
    "hostname", "timestamp", "cpu_usage", "memory_usage", "network_connections",
    "inbound_bytes", "outbound_bytes", "dns_queries", "failed_logins",
    "successful_logins", "new_processes", "unique_destinations", "is_anomalous",
}


def test_normal_sample_has_required_fields_and_sane_ranges():
    sample = engine._generate_normal_sample("HOST-001", datetime.now(timezone.utc))
    assert REQUIRED_FIELDS.issubset(sample.keys())
    assert sample["is_anomalous"] == 0
    assert 0 <= sample["cpu_usage"] <= 100
    assert 0 <= sample["memory_usage"] <= 100
    assert sample["network_connections"] >= 1
    assert sample["inbound_bytes"] >= 0
    assert sample["outbound_bytes"] >= 0


def test_compromise_increases_every_targeted_signal():
    baseline = engine._generate_normal_sample("HOST-042", datetime.now(timezone.utc))
    compromised = engine._apply_compromise(baseline)

    assert compromised["is_anomalous"] == 1
    # Each of the six independent signal families named in the spec must move.
    assert compromised["outbound_bytes"] > baseline["outbound_bytes"]
    assert compromised["dns_queries"] > baseline["dns_queries"]
    assert compromised["new_processes"] > baseline["new_processes"]
    assert compromised["failed_logins"] > baseline["failed_logins"]
    assert compromised["unique_destinations"] > baseline["unique_destinations"]
    assert compromised["cpu_usage"] > baseline["cpu_usage"]
    assert compromised["memory_usage"] > baseline["memory_usage"]
    # Original fields (hostname/timestamp) are preserved, not fabricated.
    assert compromised["hostname"] == baseline["hostname"]
    assert compromised["timestamp"] == baseline["timestamp"]


def test_compromise_is_repeatably_directional_across_many_draws():
    # Guards against a one-off lucky random draw masking a broken invariant.
    for _ in range(50):
        baseline = engine._generate_normal_sample("HOST-042", datetime.now(timezone.utc))
        compromised = engine._apply_compromise(baseline)
        assert compromised["outbound_bytes"] > baseline["outbound_bytes"]
        assert compromised["dns_queries"] > baseline["dns_queries"]
        assert compromised["new_processes"] > baseline["new_processes"]
        assert compromised["failed_logins"] > baseline["failed_logins"]
        assert compromised["unique_destinations"] > baseline["unique_destinations"]


def test_generate_sample_normal_vs_compromised_flag():
    ts = datetime.now(timezone.utc)
    normal = engine.generate_sample("HOST-017", ts, compromised=False)
    anomalous = engine.generate_sample("HOST-017", ts, compromised=True)
    assert normal["is_anomalous"] == 0
    assert anomalous["is_anomalous"] == 1
