import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import endpoints, explanation, health, incidents, risk, simulation, telemetry
from app.core.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.db import database as db
from app.services.anomaly_detection import anomaly_service
from app.services.incident_management import run_incident_detection
from app.services.telemetry_engine import TICK_SECONDS, backfill_all_if_empty, tick_all_hosts

# Re-fit the anomaly baseline periodically from all telemetry confirmed
# normal so far (never anything currently flagged as compromised -- see
# database.fetch_normal_telemetry_rows). This lets the learned baseline
# keep pace with legitimate variation the initial backfill window didn't
# happen to cover, instead of staying frozen at startup's snapshot.
RETRAIN_EVERY_N_TICKS = 30  # ~2 minutes at TICK_SECONDS=4s


async def _telemetry_loop() -> None:
    tick_count = 0
    while True:
        await asyncio.sleep(TICK_SECONDS)
        tick_all_hosts()
        run_incident_detection()

        tick_count += 1
        if tick_count % RETRAIN_EVERY_N_TICKS == 0:
            anomaly_service.train(db.fetch_normal_telemetry_rows())


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    backfill_all_if_empty()
    anomaly_service.train(db.fetch_normal_telemetry_rows())

    task = None
    if not os.environ.get("SENTINELX_DISABLE_TELEMETRY_LOOP"):
        task = asyncio.create_task(_telemetry_loop())

    yield

    if task is not None:
        task.cancel()


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(endpoints.router, prefix="/api", tags=["endpoints"])
app.include_router(telemetry.router, prefix="/api", tags=["telemetry"])
app.include_router(simulation.router, prefix="/api", tags=["simulation"])
app.include_router(risk.router, prefix="/api", tags=["risk"])
app.include_router(incidents.router, prefix="/api", tags=["incidents"])
app.include_router(explanation.router, prefix="/api", tags=["explanation"])
