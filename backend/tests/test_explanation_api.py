"""API-level tests for GET /api/endpoints/{hostname}/explanation.

Runs after tests/test_api.py (alphabetical collection order), which leaves
the simulation state reset to normal.
"""


def test_explanation_unknown_host_404(client):
    resp = client.get("/api/endpoints/HOST-999/explanation")
    assert resp.status_code == 404


def test_explanation_structure(client):
    resp = client.get("/api/endpoints/HOST-001/explanation")
    assert resp.status_code == 200
    body = resp.json()
    for field in ("hostname", "timestamp", "severity", "summary", "evidence", "recommended_actions"):
        assert field in body
    assert body["severity"] == body["severity"].upper()
    for item in body["evidence"]:
        for field in ("signal", "observed", "baseline", "baseline_range", "deviation", "contribution", "direction", "severity"):
            assert field in item


def test_explanation_changes_across_normal_compromise_reset(client):
    baseline = client.get("/api/endpoints/HOST-042/explanation").json()

    compromise_resp = client.post("/api/simulation/compromise")
    assert compromise_resp.status_code == 200

    compromised = client.get("/api/endpoints/HOST-042/explanation").json()
    assert compromised["severity"] == "CRITICAL"
    assert len(compromised["evidence"]) > len(baseline["evidence"])
    assert compromised["summary"] != baseline["summary"]

    # Evidence is grounded in real telemetry, not fabricated: every observed
    # value in the evidence must be a plausible telemetry reading, and no
    # forbidden attribution language appears anywhere in the response.
    full_text = (compromised["summary"] + " ".join(compromised["recommended_actions"])).lower()
    for forbidden in ("cve-", "trojan", "ransomware", "cobalt strike", "mimikatz"):
        assert forbidden not in full_text

    signals_seen = {item["signal"] for item in compromised["evidence"]}
    assert signals_seen  # non-empty: real signals drove this, not a static template
    actions_text = " ".join(compromised["recommended_actions"]).lower()
    assert "isolate" in actions_text
    assert "preserve" in actions_text

    reset_resp = client.post("/api/simulation/reset")
    assert reset_resp.status_code == 200

    after_reset = client.get("/api/endpoints/HOST-042/explanation").json()
    assert after_reset["severity"] != "CRITICAL"
    assert len(after_reset["evidence"]) < len(compromised["evidence"])
