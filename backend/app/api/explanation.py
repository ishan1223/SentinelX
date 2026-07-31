from fastapi import APIRouter

from app.api.risk import get_threat_assessment
from app.api.schemas import EvidenceItemOut, ExplanationResponse
from app.core.config import SIMULATED_DATA_NOTICE
from app.services.explanation import explain

router = APIRouter()


@router.get("/endpoints/{hostname}/explanation", response_model=ExplanationResponse)
def get_endpoint_explanation(hostname: str) -> ExplanationResponse:
    assessment = get_threat_assessment(hostname)
    explanation = explain(assessment)

    return ExplanationResponse(
        hostname=explanation.hostname,
        timestamp=explanation.timestamp,
        severity=explanation.severity,
        summary=explanation.summary,
        evidence=[EvidenceItemOut(**vars(e)) for e in explanation.evidence],
        recommended_actions=explanation.recommended_actions,
        notice=SIMULATED_DATA_NOTICE,
    )
