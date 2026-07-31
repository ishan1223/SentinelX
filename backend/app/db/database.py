"""SQLite persistence layer for SentinelX.

The database stores a small fleet of *simulated* endpoints (systems,
firewalls, routers), their behavioural telemetry history, and the current
controlled-simulation state (normal vs. compromised) per host. All data is
synthetically generated — see app.services.telemetry_engine.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "sentinelx.db"
DB_PATH = Path(os.environ.get("SENTINELX_DB_PATH", str(_DEFAULT_DB_PATH)))

SCHEMA = """
CREATE TABLE IF NOT EXISTS endpoints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('system', 'firewall', 'router')),
    ip_address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'monitoring',
    risk_score REAL NOT NULL DEFAULT 0.0,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    cpu_usage REAL NOT NULL,
    memory_usage REAL NOT NULL,
    network_connections INTEGER NOT NULL,
    inbound_bytes INTEGER NOT NULL,
    outbound_bytes INTEGER NOT NULL,
    dns_queries INTEGER NOT NULL,
    failed_logins INTEGER NOT NULL,
    successful_logins INTEGER NOT NULL,
    new_processes INTEGER NOT NULL,
    unique_destinations INTEGER NOT NULL,
    is_anomalous INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (hostname) REFERENCES endpoints (id)
);
CREATE INDEX IF NOT EXISTS idx_telemetry_hostname_ts ON telemetry (hostname, timestamp);

CREATE TABLE IF NOT EXISTS simulation_state (
    hostname TEXT PRIMARY KEY,
    compromised INTEGER NOT NULL DEFAULT 0,
    compromised_since TEXT,
    FOREIGN KEY (hostname) REFERENCES endpoints (id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    severity TEXT NOT NULL,
    compromise_probability REAL NOT NULL,
    anomaly_score REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED')),
    summary TEXT NOT NULL,
    evidence TEXT NOT NULL,
    recommended_actions TEXT NOT NULL,
    FOREIGN KEY (hostname) REFERENCES endpoints (id)
);
CREATE INDEX IF NOT EXISTS idx_incidents_hostname_status ON incidents (hostname, status);
"""

# (id/hostname, name, type, ip_address, status, risk_score)
SEED_ENDPOINTS = [
    ("HOST-001", "WIN10-FIN-01",  "system",   "10.20.1.11",  "monitoring", 0.0),
    ("HOST-017", "WIN11-HR-17",   "system",   "10.20.1.27",  "monitoring", 0.0),
    ("HOST-023", "PERIM-FW-023",  "firewall", "10.20.0.1",   "monitoring", 0.0),
    ("HOST-042", "WIN10-ENG-42",  "system",   "10.20.1.52",  "monitoring", 0.0),
    ("HOST-051", "CORE-RTR-051",  "router",   "10.20.0.254", "monitoring", 0.0),
]

HOSTNAMES = [row[0] for row in SEED_ENDPOINTS]


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)

        count = conn.execute("SELECT COUNT(*) AS c FROM endpoints").fetchone()["c"]
        if count == 0:
            now = datetime.now(timezone.utc).isoformat()
            conn.executemany(
                "INSERT INTO endpoints (id, name, type, ip_address, status, risk_score, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(*row, now) for row in SEED_ENDPOINTS],
            )

        for hostname in HOSTNAMES:
            conn.execute(
                "INSERT OR IGNORE INTO simulation_state (hostname, compromised, compromised_since) "
                "VALUES (?, 0, NULL)",
                (hostname,),
            )


def get_endpoint_row(hostname: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM endpoints WHERE id = ?", (hostname,)
        ).fetchone()


def list_endpoint_rows() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM endpoints ORDER BY id").fetchall()


def update_endpoint_last_seen(hostname: str, timestamp: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE endpoints SET last_seen = ? WHERE id = ?", (timestamp, hostname)
        )


def insert_telemetry_row(sample: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO telemetry (
                hostname, timestamp, cpu_usage, memory_usage, network_connections,
                inbound_bytes, outbound_bytes, dns_queries, failed_logins,
                successful_logins, new_processes, unique_destinations, is_anomalous
            ) VALUES (
                :hostname, :timestamp, :cpu_usage, :memory_usage, :network_connections,
                :inbound_bytes, :outbound_bytes, :dns_queries, :failed_logins,
                :successful_logins, :new_processes, :unique_destinations, :is_anomalous
            )
            """,
            sample,
        )


def fetch_telemetry_rows(hostname: str, limit: int = 100) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM telemetry WHERE hostname = ? ORDER BY timestamp DESC LIMIT ?",
            (hostname, limit),
        ).fetchall()
    return list(reversed(rows))


def fetch_normal_telemetry_rows() -> list[sqlite3.Row]:
    """All telemetry rows across the fleet known (from simulation ground
    truth) to be non-anomalous. Used only to curate the anomaly detector's
    training set — never consulted at inference time."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM telemetry WHERE is_anomalous = 0 ORDER BY hostname, timestamp"
        ).fetchall()


def count_telemetry_rows(hostname: str) -> int:
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS c FROM telemetry WHERE hostname = ?", (hostname,)
        ).fetchone()["c"]


def get_simulation_row(hostname: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM simulation_state WHERE hostname = ?", (hostname,)
        ).fetchone()


def list_simulation_rows() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM simulation_state").fetchall()


def set_simulation_compromised(hostname: str, compromised: bool, since: str | None) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE simulation_state SET compromised = ?, compromised_since = ? WHERE hostname = ?",
            (1 if compromised else 0, since, hostname),
        )


def insert_incident(
    hostname: str,
    created_at: str,
    severity: str,
    compromise_probability: float,
    anomaly_score: float,
    summary: str,
    evidence_json: str,
    actions_json: str,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents (
                hostname, created_at, updated_at, severity, compromise_probability,
                anomaly_score, status, summary, evidence, recommended_actions
            ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)
            """,
            (
                hostname, created_at, created_at, severity, compromise_probability,
                anomaly_score, summary, evidence_json, actions_json,
            ),
        )
        return cursor.lastrowid


def get_incident_row(incident_pk: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_pk,)).fetchone()


def list_incident_rows(status: str | None = None) -> list[sqlite3.Row]:
    with get_connection() as conn:
        if status:
            return conn.execute(
                "SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        return conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()


def get_active_incident_for_host(hostname: str) -> sqlite3.Row | None:
    """The most recent OPEN or INVESTIGATING incident for a host, if any.
    Used to decide whether a new incident should be opened — see
    app.services.incident_management.run_incident_detection."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM incidents WHERE hostname = ? AND status IN ('OPEN', 'INVESTIGATING') "
            "ORDER BY created_at DESC LIMIT 1",
            (hostname,),
        ).fetchone()


def update_incident_status(incident_pk: int, status: str, updated_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (status, updated_at, incident_pk),
        )
