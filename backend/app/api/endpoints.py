from fastapi import APIRouter, HTTPException

from app.api.schemas import Endpoint, EndpointListResponse
from app.core.config import SIMULATED_DATA_NOTICE
from app.db import database as db

router = APIRouter()


@router.get("/endpoints", response_model=EndpointListResponse)
def list_endpoints() -> EndpointListResponse:
    rows = db.list_endpoint_rows()
    endpoints = [Endpoint(**dict(row)) for row in rows]
    return EndpointListResponse(
        count=len(endpoints),
        endpoints=endpoints,
        notice=SIMULATED_DATA_NOTICE,
    )


@router.get("/endpoints/{hostname}", response_model=Endpoint)
def get_endpoint(hostname: str) -> Endpoint:
    row = db.get_endpoint_row(hostname)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown endpoint '{hostname}'")
    return Endpoint(**dict(row))
