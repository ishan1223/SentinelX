from fastapi import APIRouter, HTTPException

from app.api.schemas import ContributingSignalOut, ModelInfo, RiskResponse
from app.core.config import SIMULATED_DATA_NOTICE
from app.db import database as db
from app.services.anomaly_detection import NotTrainedError, anomaly_service
from app.services.threat_correlation import ThreatAssessment, assess

router = APIRouter()

MODEL_METHOD = "IsolationForest over per-host z-scored behavioural features + rule-based multi-signal correlation"


def get_threat_assessment(hostname: str) -> ThreatAssessment:
    """Shared by /risk and /explanation: fetch latest telemetry for a host
    and run it through the anomaly-detection + correlation pipeline."""
    if db.get_endpoint_row(hostname) is None:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint '{hostname}'")

    latest = db.fetch_telemetry_rows(hostname, limit=1)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No telemetry recorded yet for '{hostname}'")

    try:
        anomaly_result = anomaly_service.score(latest[0])
    except NotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return assess(anomaly_result)


def build_risk_response(hostname: str) -> RiskResponse:
    assessment = get_threat_assessment(hostname)

    return RiskResponse(
        hostname=assessment.hostname,
        timestamp=assessment.timestamp,
        anomaly_score=assessment.anomaly_score,
        compromise_probability=assessment.compromise_probability,
        severity=assessment.severity,
        correlated_signal_count=assessment.correlated_signal_count,
        contributing_signals=[
            ContributingSignalOut(**vars(s)) for s in assessment.contributing_signals
        ],
        model_info=ModelInfo(
            method=MODEL_METHOD,
            trained_at=anomaly_service.trained_at,
            training_samples=anomaly_service.n_training_samples,
        ),
        notice=SIMULATED_DATA_NOTICE,
    )


@router.get("/endpoints/{hostname}/risk", response_model=RiskResponse)
def get_endpoint_risk(hostname: str) -> RiskResponse:
    return build_risk_response(hostname)
