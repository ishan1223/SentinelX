from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.core.config import APP_NAME, APP_VERSION

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=APP_NAME,
        version=APP_VERSION,
        simulated_data=True,
    )
