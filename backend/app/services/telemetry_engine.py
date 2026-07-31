"""Synthetic security telemetry engine.

Generates realistic, internally-correlated behavioural telemetry for a small
fleet of simulated hosts, and implements a controlled "compromise" simulation
that distorts several independent signals at once (outbound traffic, DNS
behaviour, process creation, authentication, destination diversity, resource
usage) — the multi-signal pattern the rest of SentinelX is meant to detect.

Everything here is synthetic. No real host or network data is involved.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import numpy as np

from app.db import database as db

TICK_SECONDS = 4
BACKFILL_POINTS = 60
BACKFILL_INTERVAL_MINUTES = 1


class HostProfile(TypedDict):
    base_cpu: float
    base_mem: float
    base_conn: float
    base_dns: float
    conn_in_bytes: float
    conn_out_bytes: float
    dest_ratio: float
    proc_rate: float
    login_rate: float


# Baseline behavioural profile per host. Firewalls/routers push far more
# connections and bytes but see almost no interactive logins; workstations
# are the opposite. This asymmetry is what makes the correlated-anomaly
# injection below look like a real deviation rather than plain noise.
HOST_PROFILES: dict[str, HostProfile] = {
    "HOST-001": dict(base_cpu=18, base_mem=35, base_conn=12,  base_dns=12, conn_in_bytes=1500, conn_out_bytes=300,  dest_ratio=0.5,  proc_rate=0.6, login_rate=0.08),
    "HOST-017": dict(base_cpu=15, base_mem=32, base_conn=10,  base_dns=10, conn_in_bytes=1400, conn_out_bytes=280,  dest_ratio=0.5,  proc_rate=0.5, login_rate=0.08),
    "HOST-023": dict(base_cpu=32, base_mem=45, base_conn=180, base_dns=40, conn_in_bytes=2200, conn_out_bytes=2000, dest_ratio=0.3,  proc_rate=0.1, login_rate=0.01),
    "HOST-042": dict(base_cpu=20, base_mem=38, base_conn=14,  base_dns=14, conn_in_bytes=1600, conn_out_bytes=320,  dest_ratio=0.5,  proc_rate=0.6, login_rate=0.08),
    "HOST-051": dict(base_cpu=28, base_mem=40, base_conn=220, base_dns=20, conn_in_bytes=3000, conn_out_bytes=2800, dest_ratio=0.25, proc_rate=0.05, login_rate=0.01),
}

# Smoothed activity level per host (0-1), driven as a bounded random walk so
# consecutive samples correlate instead of jumping around independently.
_host_load: dict[str, float] = {h: 0.5 for h in HOST_PROFILES}


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _next_load(hostname: str) -> float:
    # Bounded random walk to simulate smooth, correlated server load variation
    current = _host_load.get(hostname, 0.5)
    current = _clip(current + random.gauss(0, 0.015), 0.3, 0.7)
    _host_load[hostname] = current
    return current


def _generate_normal_sample(hostname: str, timestamp: datetime) -> dict:
    profile = HOST_PROFILES[hostname]
    load = _next_load(hostname)

    cpu_usage = _clip(random.gauss(profile["base_cpu"] + load * 25, 3), 1, 95)
    memory_usage = _clip(random.gauss(profile["base_mem"] + load * 20, 3), 5, 97)

    connections = max(1, round(random.gauss(
        profile["base_conn"] * (0.7 + 0.6 * load), profile["base_conn"] * 0.1 + 1
    )))
    inbound_bytes = max(0, round(connections * profile["conn_in_bytes"] * random.gauss(1, 0.15)))
    outbound_bytes = max(0, round(connections * profile["conn_out_bytes"] * random.gauss(1, 0.15)))
    dns_queries = max(0, round(random.gauss(
        profile["base_dns"] * (0.7 + 0.6 * load), profile["base_dns"] * 0.15 + 1
    )))
    unique_destinations = max(1, round(connections * profile["dest_ratio"] * random.gauss(1, 0.1)))

    failed_logins = int(np.random.poisson(0.03))
    successful_logins = int(np.random.poisson(profile["login_rate"]))
    new_processes = int(np.random.poisson(profile["proc_rate"]))

    return {
        "hostname": hostname,
        "timestamp": timestamp.isoformat(),
        "cpu_usage": round(cpu_usage, 2),
        "memory_usage": round(memory_usage, 2),
        "network_connections": connections,
        "inbound_bytes": inbound_bytes,
        "outbound_bytes": outbound_bytes,
        "dns_queries": dns_queries,
        "failed_logins": failed_logins,
        "successful_logins": successful_logins,
        "new_processes": new_processes,
        "unique_destinations": unique_destinations,
        "is_anomalous": 0,
    }


def _apply_compromise(sample: dict) -> dict:
    """Distort a normal sample across several independent signal families.

    Mirrors real post-compromise behaviour: C2/exfil traffic, DNS
    tunnelling/beaconing, dropper process spawning, credential attacks,
    contact with unfamiliar destinations, and elevated resource usage from
    malicious activity running alongside the legitimate workload.
    """
    sample = dict(sample)

    # Abnormal outbound traffic (exfiltration) — inbound stays roughly
    # normal so the in/out ratio itself becomes a signal. The flat addend
    # guarantees a real deviation even when the baseline sample was small.
    sample["outbound_bytes"] = (
        round(sample["outbound_bytes"] * random.uniform(6, 15)) + random.randint(2000, 8000)
    )
    sample["inbound_bytes"] = round(sample["inbound_bytes"] * random.uniform(1.0, 1.4))

    # Unusual DNS behaviour (beaconing / tunnelling).
    sample["dns_queries"] = round(sample["dns_queries"] * random.uniform(4, 9) + 5)

    # Network destination deviation — many more distinct destinations than
    # the connection count would normally justify.
    sample["network_connections"] = sample["network_connections"] + random.randint(5, 20)
    sample["unique_destinations"] = round(
        sample["unique_destinations"] * random.uniform(5, 12) + 3
    )

    # Unusual process creation (dropper / payload execution).
    sample["new_processes"] = sample["new_processes"] + random.randint(4, 12)

    # Authentication deviation (credential brute-forcing / lateral movement).
    sample["failed_logins"] = sample["failed_logins"] + random.randint(3, 10)

    # Resource deviation from malicious activity running on the host.
    sample["cpu_usage"] = round(_clip(sample["cpu_usage"] + random.uniform(15, 35), 0, 100), 2)
    sample["memory_usage"] = round(_clip(sample["memory_usage"] + random.uniform(10, 25), 0, 100), 2)

    sample["is_anomalous"] = 1
    return sample


def generate_sample(hostname: str, timestamp: datetime, compromised: bool) -> dict:
    sample = _generate_normal_sample(hostname, timestamp)
    if compromised:
        sample = _apply_compromise(sample)
    return sample


def tick_all_hosts() -> None:
    """Generate and persist one telemetry sample per host, honoring current
    simulation state. Called on a timer by the background loop."""
    now = datetime.now(timezone.utc)
    for hostname in HOST_PROFILES:
        state = db.get_simulation_row(hostname)
        compromised = bool(state["compromised"]) if state else False
        sample = generate_sample(hostname, now, compromised)
        db.insert_telemetry_row(sample)
        db.update_endpoint_last_seen(hostname, sample["timestamp"])


def generate_and_persist_state_sample(hostname: str, compromised: bool) -> dict:
    """Immediately generate one sample reflecting a just-changed simulation
    state, so the effect of triggering/resetting is observable right away
    without waiting for the next background tick."""
    now = datetime.now(timezone.utc)
    sample = generate_sample(hostname, now, compromised)
    db.insert_telemetry_row(sample)
    db.update_endpoint_last_seen(hostname, sample["timestamp"])
    return sample


def backfill_all_if_empty() -> None:
    """Seed historical normal telemetry for each host so the API has
    meaningful data immediately after a fresh startup."""
    now = datetime.now(timezone.utc)
    for hostname in HOST_PROFILES:
        if db.count_telemetry_rows(hostname) > 0:
            continue
        start = now - timedelta(minutes=BACKFILL_INTERVAL_MINUTES * BACKFILL_POINTS)
        for i in range(BACKFILL_POINTS):
            ts = start + timedelta(minutes=BACKFILL_INTERVAL_MINUTES * i)
            sample = generate_sample(hostname, ts, compromised=False)
            db.insert_telemetry_row(sample)
        db.update_endpoint_last_seen(hostname, sample["timestamp"])
