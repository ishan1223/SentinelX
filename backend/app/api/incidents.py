from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    EvidenceItemOut,
    IncidentListResponse,
    IncidentResponse,
    IncidentStatusUpdate,
)
from app.core.config import SIMULATED_DATA_NOTICE
from app.services import incident_management as im

router = APIRouter()


def _to_response(incident: im.Incident) -> IncidentResponse:
    return IncidentResponse(
        incident_id=incident.incident_id,
        hostname=incident.hostname,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        severity=incident.severity,
        compromise_probability=incident.compromise_probability,
        anomaly_score=incident.anomaly_score,
        status=incident.status,
        summary=incident.summary,
        evidence=[EvidenceItemOut(**e) for e in incident.evidence],
        recommended_actions=incident.recommended_actions,
    )


@router.get("/incidents", response_model=IncidentListResponse)
def list_incidents(status: str | None = Query(default=None)) -> IncidentListResponse:
    if status is not None and status not in im.VALID_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status filter '{status}', must be one of {im.VALID_STATUSES}",
        )
    incidents = im.list_incidents(status)
    return IncidentListResponse(
        count=len(incidents),
        incidents=[_to_response(i) for i in incidents],
        notice=SIMULATED_DATA_NOTICE,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str) -> IncidentResponse:
    incident = im.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Unknown incident '{incident_id}'")
    return _to_response(incident)


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
def update_incident_status(incident_id: str, body: IncidentStatusUpdate) -> IncidentResponse:
    incident = im.update_status(incident_id, body.status)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Unknown incident '{incident_id}'")
    return _to_response(incident)
