from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import TelemetryResponse, TelemetrySample
from app.core.config import SIMULATED_DATA_NOTICE
from app.db import database as db

router = APIRouter()


@router.get("/telemetry/{hostname}", response_model=TelemetryResponse)
def get_telemetry(
    hostname: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> TelemetryResponse:
    if db.get_endpoint_row(hostname) is None:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint '{hostname}'")

    rows = db.fetch_telemetry_rows(hostname, limit=limit)
    samples = [
        TelemetrySample(**{**dict(row), "is_anomalous": bool(row["is_anomalous"])})
        for row in rows
    ]
    return TelemetryResponse(
        hostname=hostname,
        count=len(samples),
        samples=samples,
        notice=SIMULATED_DATA_NOTICE,
    )
