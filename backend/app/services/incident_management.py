"""Incident lifecycle management service.

Tracks persistent security incidents, handles deduplication, and
manages analyst workflow status transitions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db import database as db
from app.services.anomaly_detection import NotTrainedError, anomaly_service
from app.services.explanation import explain
from app.services.threat_correlation import assess

STATUS_OPEN = "OPEN"
STATUS_INVESTIGATING = "INVESTIGATING"
STATUS_RESOLVED = "RESOLVED"
VALID_STATUSES = (STATUS_OPEN, STATUS_INVESTIGATING, STATUS_RESOLVED)
ACTIVE_STATUSES = (STATUS_OPEN, STATUS_INVESTIGATING)

INCIDENT_CREATION_THRESHOLD = 80.0


@dataclass
class Incident:
    incident_id: str
    hostname: str
    created_at: str
    updated_at: str
    severity: str
    compromise_probability: float
    anomaly_score: float
    status: str
    summary: str
    evidence: list[dict]
    recommended_actions: list[str]


def _format_incident_id(pk: int) -> str:
    return f"INC-{pk:04d}"


def _parse_incident_id(incident_id: str) -> int | None:
    if not incident_id.startswith("INC-"):
        return None
    try:
        return int(incident_id[len("INC-"):])
    except ValueError:
        return None


def _row_to_incident(row) -> Incident:
    return Incident(
        incident_id=_format_incident_id(row["id"]),
        hostname=row["hostname"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        severity=row["severity"],
        compromise_probability=row["compromise_probability"],
        anomaly_score=row["anomaly_score"],
        status=row["status"],
        summary=row["summary"],
        evidence=json.loads(row["evidence"]),
        recommended_actions=json.loads(row["recommended_actions"]),
    )


def get_incident(incident_id: str) -> Incident | None:
    pk = _parse_incident_id(incident_id)
    if pk is None:
        return None
    row = db.get_incident_row(pk)
    return _row_to_incident(row) if row else None


def list_incidents(status: str | None = None) -> list[Incident]:
    return [_row_to_incident(r) for r in db.list_incident_rows(status)]


def update_status(incident_id: str, status: str) -> Incident | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}', must be one of {VALID_STATUSES}")

    pk = _parse_incident_id(incident_id)
    if pk is None or db.get_incident_row(pk) is None:
        return None

    now = datetime.now(timezone.utc).isoformat()
    db.update_incident_status(pk, status, now)
    return get_incident(incident_id)


def run_incident_detection() -> list[Incident]:
    """Evaluate every host's current risk and open a new incident wherever
    compromise_probability has crossed INCIDENT_CREATION_THRESHOLD *and*
    the host has no existing OPEN/INVESTIGATING incident already tracking
    it. Safe to call repeatedly (every telemetry tick, or right after a
    simulation state change) -- the active-incident check is exactly what
    prevents duplicate incidents while a host stays compromised.
    """
    created: list[Incident] = []

    for endpoint_row in db.list_endpoint_rows():
        hostname = endpoint_row["id"]

        latest = db.fetch_telemetry_rows(hostname, limit=1)
        if not latest:
            continue

        try:
            anomaly_result = anomaly_service.score(latest[0])
        except NotTrainedError:
            continue

        assessment = assess(anomaly_result)
        if assessment.compromise_probability < INCIDENT_CREATION_THRESHOLD:
            continue
        if db.get_active_incident_for_host(hostname) is not None:
            continue

        explanation = explain(assessment)
        now = datetime.now(timezone.utc).isoformat()
        pk = db.insert_incident(
            hostname=hostname,
            created_at=now,
            severity=assessment.severity,
            compromise_probability=assessment.compromise_probability,
            anomaly_score=assessment.anomaly_score,
            summary=explanation.summary,
            evidence_json=json.dumps([vars(e) for e in explanation.evidence]),
            actions_json=json.dumps(explanation.recommended_actions),
        )
        incident = get_incident(_format_incident_id(pk))
        if incident is not None:
            created.append(incident)

    return created
