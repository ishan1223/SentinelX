# SENTINELX — DEMO FORENSICS
**Inspection Goal:** Code-Level Forensics of the Interactive Demo Execution  
**Target Action:** Triggering Compromise on `HOST-042` and Resetting Fleet  

---

## 1. End-to-End Simulation Execution Chain

```text
[Analyst Clicks "Simulate Attack" on Header or DemoMode Console]
                           │
                           ▼
  1. HTTP POST http://localhost:8000/api/simulation/compromise?hostname=HOST-042
     (frontend/src/lib/api.ts: triggerCompromise)
                           │
                           ▼
  2. Router Handler Execution
     (backend/app/api/simulation.py: trigger_compromise)
     ├─ Updates SQLite: UPDATE simulation_state SET compromised=1 WHERE hostname='HOST-042'
     ├─ Invokes immediate sample generator: telemetry_engine.generate_and_persist_state_sample('HOST-042', True)
     └─ Invokes incident detector: incident_management.run_incident_detection()
                           │
                           ▼
  3. Controlled Multi-Signal Distortion
     (backend/app/services/telemetry_engine.py: _apply_compromise)
     ├─ outbound_bytes: multiplied 6–15x + 2,000–8,000 bytes (Data Exfiltration)
     ├─ dns_queries: multiplied 4–9x + 5 queries (C2 Beaconing / Tunnelling)
     ├─ unique_destinations: multiplied 5–12x + 3 distinct IPs (Lateral Reconnaissance)
     ├─ new_processes: increased by 4–12 processes (Dropper Execution)
     ├─ failed_logins: increased by 3–10 attempts (Credential Stuffing)
     └─ cpu_usage / memory_usage: elevated by 15–35% (Malicious Worker Overhead)
                           │
                           ▼
  4. Telemetry Persistence
     (backend/app/db/database.py: insert_telemetry_row)
     └─ Record inserted with is_anomalous = 1
                           │
                           ▼
  5. Anomaly Detection & Scoring
     (backend/app/services/anomaly_detection.py: score)
     ├─ Feature vector normalized against HOST-042 baseline mean & std
     ├─ Z-scores exceed +4.0 to +9.0 standard deviations
     └─ Calibrated Anomaly Score surges from ~5.0 to 85.0–98.0
                           │
                           ▼
  6. Multi-Signal Threat Correlation
     (backend/app/services/threat_correlation.py: assess)
     ├─ Significant deviating signal count = 6 (|z| >= 2.0)
     ├─ Correlation Breadth = min(6/9, 1.0) = 0.67
     ├─ Average Severity = ~6.5 -> Severity Factor = 1.0
     ├─ Compromise Probability = 0.50*(95) + 0.30*(67) + 0.20*(100) = 87.6%
     └─ Severity Tier = "CRITICAL" (>= 75.0)
                           │
                           ▼
  7. Automated Incident Ticket Generation
     (backend/app/services/incident_management.py: run_incident_detection)
     ├─ Compromise probability (87.6%) >= Threshold (80.0%)
     ├─ Active ticket check confirms no existing OPEN/INVESTIGATING ticket for HOST-042
     ├─ Deterministic explanation & playbooks generated via explanation.py: explain()
     └─ New incident ticket inserted into SQLite (e.g. ID: INC-0001, status: OPEN)
                           │
                           ▼
  8. Dashboard UI Reaction (within 1–4 seconds)
     (frontend/src/hooks/useDashboardData.ts)
     ├─ SummaryCards: "At Risk" increments, "Active Incidents" increments to 1
     ├─ EndpointTable: HOST-042 status turns red "High Risk" with 88% progress bar
     ├─ RecentIncidents Feed: INC-0001 card appears with severity badge and playbooks
     ├─ ThreatTimelineChart: Red anomalous event volume bar appears in current bucket
     ├─ RiskDistributionChart: Red "Critical" wedge appears on Donut Chart
     └─ InvestigationPanel: Clicking HOST-042 opens drawer displaying z-score deviation bars
```

---

## 2. What Exactly Changes in Code When Resetting the Simulation?

When clicking **"Reset Fleet"**:
1. `POST /api/simulation/reset` is invoked (`backend/app/api/simulation.py:reset_simulation`).
2. SQLite `simulation_state` is updated: `compromised = 0`, `compromised_since = NULL`.
3. An immediate normal sample is generated via `telemetry_engine.generate_and_persist_state_sample('HOST-042', compromised=False)`.
4. Subsequent ticks from `_telemetry_loop()` generate normal baseline traffic.
5. In the demo mode flow (`useDemoSequence.ts:L95-L101`), any active `OPEN` incidents are automatically patched to `RESOLVED` via `PATCH /api/incidents/{id}`.
6. The dashboard polls, `HOST-042` risk drops back to **0.0–5.0**, and fleet returns to 100% Healthy.
