"""API-level verification of the ML risk scoring and correlation endpoints.

Runs after tests/test_api.py (alphabetical collection order), which leaves
the simulation state reset to normal -- so HOST-042 starts here as a normal,
uncompromised host.
"""


def test_risk_endpoint_unknown_host_404(client):
    resp = client.get("/api/endpoints/HOST-999/risk")
    assert resp.status_code == 404


def test_risk_endpoint_structure(client):
    resp = client.get("/api/endpoints/HOST-001/risk")
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "hostname", "timestamp", "anomaly_score", "compromise_probability",
        "severity", "correlated_signal_count", "contributing_signals", "model_info",
    ):
        assert field in body
    assert body["severity"] in {"low", "medium", "high", "critical"}
    assert 0 <= body["anomaly_score"] <= 100
    assert 0 <= body["compromise_probability"] <= 100
    assert body["model_info"]["training_samples"] > 0
    assert body["model_info"]["trained_at"] is not None


def test_normal_compromise_reset_risk_sequence(client):
    # 1. NORMAL -> low risk.
    baseline = client.get("/api/endpoints/HOST-042/risk").json()
    assert baseline["compromise_probability"] < 40
    assert baseline["severity"] in {"low", "medium"}

    # 2. SIMULATE COMPROMISE -> materially higher risk, driven by real
    # multi-signal deviation, not a hardcoded value for this hostname.
    compromise_resp = client.post("/api/simulation/compromise")
    assert compromise_resp.status_code == 200

    compromised = client.get("/api/endpoints/HOST-042/risk").json()
    assert compromised["compromise_probability"] > baseline["compromise_probability"] + 20
    assert compromised["severity"] in {"high", "critical"}
    assert compromised["correlated_signal_count"] >= 3
    contributing_features = {s["feature"] for s in compromised["contributing_signals"]}
    assert contributing_features & {
        "outbound_bytes", "dns_queries", "new_processes", "failed_logins", "unique_destinations",
    }

    # 3. RESET -> normal/low risk again.
    reset_resp = client.post("/api/simulation/reset")
    assert reset_resp.status_code == 200

    after_reset = client.get("/api/endpoints/HOST-042/risk").json()
    assert after_reset["compromise_probability"] < compromised["compromise_probability"] - 20
    assert after_reset["severity"] in {"low", "medium"}

    # Note: Clean up the incident opened by this test so it doesn't leak into
    # subsequent test cases.
    open_incidents = client.get("/api/incidents?status=OPEN").json()["incidents"]
    for incident in open_incidents:
        if incident["hostname"] == "HOST-042":
            client.patch(f"/api/incidents/{incident['incident_id']}", json={"status": "RESOLVED"})
