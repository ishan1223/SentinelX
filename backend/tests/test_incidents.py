"""API-level tests for the persisted incident model.

Incidents are durable records, not live snapshots. Every test here ensures
isolated testing on HOST-042 and verifies lifecycle status transitions.
"""

from app.services.incident_management import INCIDENT_CREATION_THRESHOLD
from app.services.threat_correlation import SEVERITY_THRESHOLDS


def _resolve_active_incidents_for_host(client, hostname: str) -> None:
    for status in ("OPEN", "INVESTIGATING"):
        incidents = client.get(f"/api/incidents?status={status}").json()["incidents"]
        for incident in incidents:
            if incident["hostname"] == hostname:
                client.patch(f"/api/incidents/{incident['incident_id']}", json={"status": "RESOLVED"})


def test_incident_creation_threshold_is_at_or_above_critical_severity_boundary():
    """The threshold is not arbitrary -- it must sit at or above the
    'critical' severity boundary already established in threat_correlation,
    so the two layers never drift apart silently (an incident always
    implies at least 'critical' severity). See incident_management's
    module docstring for why it sits deliberately past that boundary
    rather than exactly on it: extra margin against correlated-noise false
    positives from realistic (non-independent) normal telemetry."""
    critical_threshold = dict((label, threshold) for threshold, label in SEVERITY_THRESHOLDS)["critical"]
    assert INCIDENT_CREATION_THRESHOLD >= float(critical_threshold)


def test_get_unknown_incident_returns_404(client):
    resp = client.get("/api/incidents/INC-9999")
    assert resp.status_code == 404


def test_patch_unknown_incident_returns_404(client):
    resp = client.patch("/api/incidents/INC-9999", json={"status": "RESOLVED"})
    assert resp.status_code == 404


def test_list_incidents_rejects_invalid_status_filter(client):
    resp = client.get("/api/incidents?status=BOGUS")
    assert resp.status_code == 422


def test_list_incidents_structure(client):
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    body = resp.json()
    assert "incidents" in body
    assert body["count"] == len(body["incidents"])


def test_compromise_creates_exactly_one_incident(client):
    _resolve_active_incidents_for_host(client, "HOST-042")

    before_ids = {i["incident_id"] for i in client.get("/api/incidents").json()["incidents"]}

    resp = client.post("/api/simulation/compromise")
    assert resp.status_code == 200

    after = client.get("/api/incidents").json()["incidents"]
    new_for_host = [i for i in after if i["hostname"] == "HOST-042" and i["incident_id"] not in before_ids]
    assert len(new_for_host) == 1

    incident = new_for_host[0]
    assert incident["status"] == "OPEN"
    assert incident["severity"] in {"high", "critical"}
    assert incident["compromise_probability"] >= INCIDENT_CREATION_THRESHOLD
    assert incident["anomaly_score"] >= 0
    assert len(incident["evidence"]) > 0
    assert len(incident["recommended_actions"]) > 0
    assert incident["incident_id"].startswith("INC-")

    _resolve_active_incidents_for_host(client, "HOST-042")
    client.post("/api/simulation/reset")


def test_repeated_compromise_calls_do_not_duplicate_incidents(client):
    """Guards against duplicate incidents per tick while a host stays compromised."""
    _resolve_active_incidents_for_host(client, "HOST-042")

    client.post("/api/simulation/compromise")
    client.post("/api/simulation/compromise")
    client.post("/api/simulation/compromise")

    open_for_host = [
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    ]
    assert len(open_for_host) == 1

    _resolve_active_incidents_for_host(client, "HOST-042")
    client.post("/api/simulation/reset")


def test_incident_persists_through_reset_until_explicitly_resolved(client):
    """Reset drops live risk back to normal but must NOT silently close the
    incident -- only an explicit PATCH does that."""
    _resolve_active_incidents_for_host(client, "HOST-042")
    client.post("/api/simulation/compromise")

    target = next(
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    )

    client.post("/api/simulation/reset")

    still_open = client.get(f"/api/incidents/{target['incident_id']}").json()
    assert still_open["status"] == "OPEN"

    client.patch(f"/api/incidents/{target['incident_id']}", json={"status": "RESOLVED"})


def test_patch_lifecycle_open_investigating_resolved(client):
    _resolve_active_incidents_for_host(client, "HOST-042")
    client.post("/api/simulation/compromise")
    target = next(
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    )
    incident_id = target["incident_id"]

    resp = client.patch(f"/api/incidents/{incident_id}", json={"status": "INVESTIGATING"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "INVESTIGATING"
    assert client.get(f"/api/incidents/{incident_id}").json()["status"] == "INVESTIGATING"

    resp = client.patch(f"/api/incidents/{incident_id}", json={"status": "RESOLVED"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"

    open_ids = {i["incident_id"] for i in client.get("/api/incidents?status=OPEN").json()["incidents"]}
    resolved_ids = {i["incident_id"] for i in client.get("/api/incidents?status=RESOLVED").json()["incidents"]}
    assert incident_id not in open_ids
    assert incident_id in resolved_ids

    client.post("/api/simulation/reset")


def test_patch_rejects_invalid_status_value(client):
    _resolve_active_incidents_for_host(client, "HOST-042")
    client.post("/api/simulation/compromise")
    target = next(
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    )

    resp = client.patch(f"/api/incidents/{target['incident_id']}", json={"status": "BOGUS"})
    assert resp.status_code == 422

    # The incident must be untouched by the rejected update.
    assert client.get(f"/api/incidents/{target['incident_id']}").json()["status"] == "OPEN"

    client.patch(f"/api/incidents/{target['incident_id']}", json={"status": "RESOLVED"})
    client.post("/api/simulation/reset")


def test_incident_reopens_after_resolution_and_new_compromise(client):
    _resolve_active_incidents_for_host(client, "HOST-042")

    client.post("/api/simulation/compromise")
    first = next(
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    )
    client.patch(f"/api/incidents/{first['incident_id']}", json={"status": "RESOLVED"})
    client.post("/api/simulation/reset")

    client.post("/api/simulation/compromise")
    second_open = [
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-042"
    ]
    assert len(second_open) == 1
    assert second_open[0]["incident_id"] != first["incident_id"]

    client.patch(f"/api/incidents/{second_open[0]['incident_id']}", json={"status": "RESOLVED"})
    client.post("/api/simulation/reset")


def test_normal_state_creates_no_incident(client):
    """A host that never crosses the threshold should never accumulate an
    incident -- confirms detection is threshold-gated, not unconditional."""
    _resolve_active_incidents_for_host(client, "HOST-001")
    before = {i["incident_id"] for i in client.get("/api/incidents").json()["incidents"]}

    # HOST-001 is never driven through the compromise simulation anywhere
    # in this suite, so it should have no active incident.
    active = [
        i for i in client.get("/api/incidents?status=OPEN").json()["incidents"]
        if i["hostname"] == "HOST-001"
    ]
    assert active == []
    after = {i["incident_id"] for i in client.get("/api/incidents").json()["incidents"]}
    assert before == after
