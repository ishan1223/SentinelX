from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    SimulationActionResponse,
    SimulationResetResponse,
    TelemetrySample,
)
from app.core.config import SIMULATED_DATA_NOTICE
from app.db import database as db
from app.services import telemetry_engine
from app.services.incident_management import run_incident_detection

router = APIRouter()

AFFECTED_SIGNALS = [
    "outbound_bytes (abnormal outbound traffic)",
    "dns_queries (unusual DNS behaviour)",
    "new_processes (unusual process creation)",
    "failed_logins (authentication deviation)",
    "unique_destinations (network destination deviation)",
    "cpu_usage / memory_usage (resource deviation)",
]


@router.post("/simulation/compromise", response_model=SimulationActionResponse)
def trigger_compromise(
    hostname: str = Query(default="HOST-042"),
) -> SimulationActionResponse:
    if db.get_endpoint_row(hostname) is None:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint '{hostname}'")

    since = datetime.now(timezone.utc).isoformat()
    db.set_simulation_compromised(hostname, True, since)
    sample = telemetry_engine.generate_and_persist_state_sample(hostname, compromised=True)
    run_incident_detection()

    return SimulationActionResponse(
        hostname=hostname,
        compromised=True,
        compromised_since=since,
        affected_signals=AFFECTED_SIGNALS,
        sample=TelemetrySample(**{**sample, "is_anomalous": bool(sample["is_anomalous"])}),
    )


@router.post("/simulation/reset", response_model=SimulationResetResponse)
def reset_simulation() -> SimulationResetResponse:
    reset_hosts: list[str] = []
    for row in db.list_simulation_rows():
        if row["compromised"]:
            hostname = row["hostname"]
            db.set_simulation_compromised(hostname, False, None)
            telemetry_engine.generate_and_persist_state_sample(hostname, compromised=False)
            reset_hosts.append(hostname)

    return SimulationResetResponse(
        reset_hosts=reset_hosts,
        notice=SIMULATED_DATA_NOTICE,
    )
