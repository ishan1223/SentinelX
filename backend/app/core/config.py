"""Central configuration for the SentinelX backend."""

APP_NAME = "SentinelX"
APP_VERSION = "0.1.0"

# Frontend dev server origins allowed to call this API.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# NOTE: SentinelX operates entirely on simulated/synthetic telemetry for this
# prototype. No real network traffic, real hosts, or real IoC feeds are used.
SIMULATED_DATA_NOTICE = (
    "All telemetry, endpoints, and alerts in this system are synthetically "
    "generated for demonstration purposes. No real network or host data is "
    "collected or analyzed."
)
