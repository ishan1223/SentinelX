"""API-level tests for endpoints, telemetry, and the compromise simulation.

Tests run in file order against a single shared TestClient/DB (see
conftest.py), so the simulation lifecycle tests intentionally build on each
other: baseline -> compromise -> reset.
"""

REQUIRED_HOSTS = {"HOST-001", "HOST-017", "HOST-023", "HOST-042", "HOST-051"}


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["simulated_data"] is True


def test_list_endpoints_contains_all_required_hosts(client):
    resp = client.get("/api/endpoints")
    assert resp.status_code == 200
    body = resp.json()
    hostnames = {e["id"] for e in body["endpoints"]}
    assert REQUIRED_HOSTS.issubset(hostnames)
    assert body["count"] == len(body["endpoints"])
    assert "notice" in body


def test_get_endpoint_by_hostname(client):
    resp = client.get("/api/endpoints/HOST-042")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "HOST-042"
    assert body["type"] in {"system", "firewall", "router"}


def test_get_unknown_endpoint_returns_404(client):
    resp = client.get("/api/endpoints/HOST-999")
    assert resp.status_code == 404


def test_get_telemetry_returns_backfilled_history(client):
    resp = client.get("/api/telemetry/HOST-001")
    assert resp.status_code == 200
    body = resp.json()
    assert body["hostname"] == "HOST-001"
    assert body["count"] > 0
    sample = body["samples"][0]
    for field in (
        "timestamp", "cpu_usage", "memory_usage", "network_connections",
        "inbound_bytes", "outbound_bytes", "dns_queries", "failed_logins",
        "successful_logins", "new_processes", "unique_destinations", "is_anomalous",
    ):
        assert field in sample
    # History should be in chronological order.
    timestamps = [s["timestamp"] for s in body["samples"]]
    assert timestamps == sorted(timestamps)


def test_get_telemetry_respects_limit(client):
    resp = client.get("/api/telemetry/HOST-001?limit=5")
    assert resp.status_code == 200
    assert resp.json()["count"] <= 5


def test_get_telemetry_unknown_host_404(client):
    resp = client.get("/api/telemetry/HOST-999")
    assert resp.status_code == 404


def test_baseline_host042_and_host001_are_not_anomalous(client):
    for hostname in ("HOST-001", "HOST-042"):
        resp = client.get(f"/api/telemetry/{hostname}")
        latest = resp.json()["samples"][-1]
        assert latest["is_anomalous"] is False


def test_compromise_triggers_multi_signal_anomaly_on_host042(client):
    baseline_resp = client.get("/api/telemetry/HOST-042")
    baseline = baseline_resp.json()["samples"][-1]

    resp = client.post("/api/simulation/compromise")
    assert resp.status_code == 200
    body = resp.json()
    assert body["hostname"] == "HOST-042"
    assert body["compromised"] is True
    assert body["compromised_since"] is not None
    assert len(body["affected_signals"]) == 6
    assert body["sample"]["is_anomalous"] is True

    telemetry_resp = client.get("/api/telemetry/HOST-042")
    latest = telemetry_resp.json()["samples"][-1]
    assert latest["is_anomalous"] is True

    # The telemetry must have actually changed, across independent signals.
    assert latest["outbound_bytes"] > baseline["outbound_bytes"]
    assert latest["dns_queries"] > baseline["dns_queries"]
    assert latest["failed_logins"] > baseline["failed_logins"]
    assert latest["unique_destinations"] > baseline["unique_destinations"]
    assert latest["new_processes"] >= baseline["new_processes"]


def test_compromise_does_not_affect_other_hosts(client):
    resp = client.get("/api/telemetry/HOST-001")
    latest = resp.json()["samples"][-1]
    assert latest["is_anomalous"] is False


def test_compromise_unknown_host_returns_404(client):
    resp = client.post("/api/simulation/compromise?hostname=HOST-999")
    assert resp.status_code == 404


def test_reset_restores_normal_state(client):
    resp = client.post("/api/simulation/reset")
    assert resp.status_code == 200
    body = resp.json()
    assert "HOST-042" in body["reset_hosts"]

    telemetry_resp = client.get("/api/telemetry/HOST-042")
    latest = telemetry_resp.json()["samples"][-1]
    assert latest["is_anomalous"] is False

    endpoint_resp = client.get("/api/endpoints/HOST-042")
    assert endpoint_resp.status_code == 200


def test_reset_is_noop_when_nothing_compromised(client):
    resp = client.post("/api/simulation/reset")
    assert resp.status_code == 200
    assert resp.json()["reset_hosts"] == []
