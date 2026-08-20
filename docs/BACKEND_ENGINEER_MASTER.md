# SENTINELX — BACKEND ENGINEER MASTER PREPARATION AUDIT
**Engineer Role:** Backend Engineer  
**System Under Defense:** SentinelX Cybersecurity SOC Platform  
**Target Level:** Hostile Technical Judge Examination & SIH Defense  

---

## A. BACKEND TECHNOLOGY STACK

* **Language:** Python 3.12 (using strict type hints, dataclasses, context managers, and async concurrency).
* **Web Framework:** FastAPI `0.115.6` (`Starlette` underlying core).
* **ASGI Server:** Uvicorn `0.34.0` with `standard` extras (running on `http://127.0.0.1:8000`).
* **Database Engine:** SQLite 3 (Driver: Standard Python `sqlite3`, using `row_factory = sqlite3.Row`).
* **ORM:** **None** (Raw SQL queries with parameterized binding `?` and `:name` dictionaries to eliminate SQL injection).
* **Validation Framework:** Pydantic v2 (`2.10.4`) enforcing strict runtime serialization and deserialization.
* **Machine Learning Library:** `scikit-learn 1.6.0` (`IsolationForest`) and `numpy 2.2.0`.
* **Testing Stack:** `pytest 8.3.4`, `pytest-asyncio 0.25.0`, `httpx 0.28.1` (53 tests total).
* **Middleware:** `fastapi.middleware.cors.CORSMiddleware` (allowing `http://localhost:5173` and `http://127.0.0.1:5173`).
* **External Services:** **None**. The backend is completely self-contained with no external cloud API dependencies.

---

## B. COMPLETE BACKEND FOLDER & FILE BREAKDOWN

### 1. `backend/app/main.py`
* **Purpose:** Application initialization, CORS middleware registration, router mounting, and lifespan management.
* **Important Functions:**
  * `lifespan(app: FastAPI)`: Initializes database tables (`db.init_db()`), runs history backfill (`backfill_all_if_empty()`), trains baseline IsolationForest (`anomaly_service.train()`), and spawns background telemetry loop task.
  * `_telemetry_loop()`: Asynchronous loop running `await asyncio.sleep(4)` that ticks all hosts, executes incident detection, and triggers periodic model retraining every 30 ticks (~2 minutes).
* **Input:** Startup/shutdown ASGI lifecycle events.
* **Output:** Running FastAPI app instance with background async worker task.
* **Dependencies:** `fastapi`, `app.core.config`, `app.db.database`, `app.services.telemetry_engine`, `app.services.anomaly_detection`, `app.services.incident_management`, `app.api.*`.

---

### 2. `backend/app/core/config.py`
* **Purpose:** Central application constants, CORS origin whitelist, and transparency disclaimers.
* **Constants:**
  * `APP_NAME = "SentinelX"`
  * `APP_VERSION = "0.1.0"`
  * `CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]`
  * `SIMULATED_DATA_NOTICE`: Explanatory notice returned on API responses confirming data is synthetic.
* **Dependencies:** None.

---

### 3. `backend/app/db/database.py`
* **Purpose:** SQLite schema definitions, connection lifecycle context manager, seed fleet inventory, and SQL query helpers.
* **Important Functions:**
  * `get_connection()`: Context manager yielding an open `sqlite3.Connection` with `row_factory = sqlite3.Row`, autocommit on clean exit, and guaranteed close.
  * `init_db()`: Executes DDL schema script and seeds 5 initial endpoints (`HOST-001`, `HOST-017`, `HOST-023`, `HOST-042`, `HOST-051`) and simulation states.
  * `insert_telemetry_row(sample: dict)`: Inserts a 13-field telemetry record into `telemetry` table.
  * `fetch_telemetry_rows(hostname: str, limit: int = 100)`: Retrieves the most recent telemetry rows for a host, returned in chronological order.
  * `fetch_normal_telemetry_rows()`: Fetches all historical rows where `is_anomalous = 0` for model retraining.
  * `insert_incident(...)`: Inserts a new security incident record and returns `cursor.lastrowid`.
  * `get_active_incident_for_host(hostname: str)`: Returns latest incident in `OPEN` or `INVESTIGATING` status for deduplication.
  * `update_incident_status(incident_pk: int, status: str, updated_at: str)`: Updates incident workflow status.
* **Dependencies:** `sqlite3`, `pathlib`, `os`, `datetime`.

---

### 4. `backend/app/services/telemetry_engine.py`
* **Purpose:** Synthetic security telemetry generation modeling legitimate host workloads and multi-signal compromise distortions.
* **Important Constants & Structures:**
  * `TICK_SECONDS = 4`, `BACKFILL_POINTS = 60`, `BACKFILL_INTERVAL_MINUTES = 1`.
  * `HOST_PROFILES`: Per-host behavioral parameters (`base_cpu`, `base_mem`, `base_conn`, `base_dns`, `conn_in_bytes`, `conn_out_bytes`, `dest_ratio`, `proc_rate`, `login_rate`).
  * `_host_load`: In-memory bounded random walk state tracking per host (`0.3` to `0.7`).
* **Important Functions:**
  * `_generate_normal_sample(hostname, timestamp)`: Generates baseline sample using Gaussian noise and Poisson rates.
  * `_apply_compromise(sample)`: Distorts 6 independent signal families (multiplies outbound traffic 6-15x, DNS queries 4-9x, destination diversity 5-12x, spawns new processes, injects failed logins, elevates CPU/memory).
  * `tick_all_hosts()`: Background timer tick iterating through fleet to generate and store one telemetry row per host.
  * `generate_and_persist_state_sample(hostname, compromised)`: Immediate synchronous sample generation upon simulation state change.
  * `backfill_all_if_empty()`: Seeds 60 historical normal data points per host on cold startup.
* **Dependencies:** `random`, `numpy`, `datetime`, `app.db.database`.

---

### 5. `backend/app/services/anomaly_detection.py`
* **Purpose:** Per-host baseline normalization and unsupervised machine learning anomaly scoring.
* **Important Constants & Data Structures:**
  * `FEATURES`: 9 monitored metrics (`cpu_usage`, `memory_usage`, `network_connections`, `inbound_bytes`, `outbound_bytes`, `dns_queries`, `failed_logins`, `new_processes`, `unique_destinations`).
  * `MIN_SAMPLES_PER_HOST = 5`, `STD_FLOOR_ABS = 0.5`, `STD_FLOOR_REL = 0.02`, `Z_SCORE_CLIP = 10.0`.
  * `FeatureDeviation`: Dataclass containing `feature`, `value`, `baseline_mean`, `baseline_std`, `z_score`, `direction`.
  * `AnomalyResult`: Dataclass containing `hostname`, `timestamp`, `anomaly_score` (0-100), `raw_isolation_score`, `deviations`.
* **Important Functions:**
  * `train(normal_rows)`: Groups training rows by host, computes baseline mean & std with relative/absolute variance floors, fits `IsolationForest(n_estimators=200, random_state=42)` on pooled z-scores, and records training median and max raw scores.
  * `_compute_baseline(rows)`: Computes mean and standard deviation per feature with variance floors `floor = max(0.5, 0.02 * |mean|)`.
  * `_zscore_vector(row)`: Calculates $z = \text{clip}\left(\frac{x - \mu}{\sigma}, -10, 10\right)$.
  * `score(row)`: Normalizes row against host's baseline, computes raw IsolationForest decision score $-\text{score\_samples}([z])$, normalizes score to $[0, 100]$, and returns sorted feature deviations.
  * `_normalize_score(raw_score)`: Calibrates raw score so training median maps to 0 and training max maps to 100: $\text{score} = \text{clip}\left(\frac{\text{raw} - \text{median}}{\text{max} - \text{median}} \times 100, 0, 100\right)$.
* **Dependencies:** `sklearn.ensemble.IsolationForest`, `numpy`, `dataclasses`, `sqlite3`.

---

### 6. `backend/app/services/threat_correlation.py`
* **Purpose:** Rule-based correlation and multi-signal noise filtering fusing ML anomaly scores into a defensible compromise probability and severity tier.
* **Important Constants & Data Structures:**
  * `Z_SIGNIFICANCE_THRESHOLD = 2.0`: Standard deviations required for a signal to be considered significant.
  * `MIN_CORRELATED_SIGNALS_FOR_BOOST = 2`: Noise gate threshold.
  * `WEIGHT_ANOMALY_SCORE = 0.5`, `WEIGHT_CORRELATION_BREADTH = 0.3`, `WEIGHT_SEVERITY = 0.2`.
  * `SEVERITY_THRESHOLDS = ((75, "critical"), (50, "high"), (25, "medium"))` (else `"low"`).
* **Important Functions:**
  * `assess(result: AnomalyResult) -> ThreatAssessment`: Evaluates significant deviations ($|z| \ge 2.0$). If significant count $\ge 2$, computes correlation breadth $\frac{\text{count}}{9}$ and severity factor $\frac{\bar{|z|}}{6.0}$. Fuses into `compromise_probability` ($0.5 \times \text{ML} + 0.3 \times \text{Breadth} + 0.2 \times \text{Severity}$).
* **Dependencies:** `app.services.anomaly_detection`.

---

### 7. `backend/app/services/explanation.py`
* **Purpose:** Deterministic, evidence-based explainability generating human-readable narrative summaries, relative contribution shares, and analyst action playbooks.
* **Important Structures:**
  * `SIGNAL_LABELS`: Maps metric names to analyst terms (e.g. `outbound_bytes` $\rightarrow$ `outbound_traffic`).
  * `SIGNAL_ACTIONS`: Prescriptive non-destructive investigation playbooks per anomalous metric.
  * `_SEVERITY_BUCKETS`: Deviations $|z| \ge 7.0 \rightarrow \text{severe}$, $\ge 4.0 \rightarrow \text{high}$, else $\text{moderate}$.
* **Important Functions:**
  * `explain(assessment: ThreatAssessment) -> Explanation`: Builds evidence items, computes relative contribution percentage per signal ($\frac{|z_i|}{\sum |z|} \times 100$), creates deterministic narrative summary with attribution caveats, and compiles recommended defense actions.
* **Dependencies:** `app.services.threat_correlation`.

---

### 8. `backend/app/services/incident_management.py`
* **Purpose:** Incident lifecycle state machine, active ticket deduplication, and persistence.
* **Important Constants:**
  * `STATUS_OPEN = "OPEN"`, `STATUS_INVESTIGATING = "INVESTIGATING"`, `STATUS_RESOLVED = "RESOLVED"`.
  * `INCIDENT_CREATION_THRESHOLD = 80.0`.
* **Important Functions:**
  * `run_incident_detection()`: Iterates over active fleet, scores latest telemetry, evaluates compromise probability $\ge 80.0$, checks `get_active_incident_for_host()` to prevent duplicates, and inserts new incident with serialized JSON evidence and action playbooks.
  * `update_status(incident_id: str, status: str)`: Patches incident workflow status and updates `updated_at` timestamp.
  * `list_incidents(status: str | None)`: Queries incident records with optional status filtering.
* **Dependencies:** `app.db.database`, `app.services.anomaly_detection`, `app.services.threat_correlation`, `app.services.explanation`.

---

## C. COMPLETE BACKEND API INVENTORY (11 ENDPOINTS)

| # | HTTP Method | Path | Request Parameters / Body | Response Schema | Source File & Function |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | **GET** | `/api/health` | None | `HealthResponse` (`status`, `service`, `version`, `simulated_data`) | `app/api/health.py:get_health` |
| 2 | **GET** | `/api/endpoints` | None | `EndpointListResponse` (`count`, `endpoints`, `notice`) | `app/api/endpoints.py:list_endpoints` |
| 3 | **GET** | `/api/endpoints/{hostname}` | Path: `hostname` (str) | `Endpoint` (`id`, `name`, `type`, `ip_address`, `status`, `risk_score`, `last_seen`) | `app/api/endpoints.py:get_endpoint` |
| 4 | **GET** | `/api/telemetry/{hostname}` | Path: `hostname`, Query: `limit` (int, default 100, 1-1000) | `TelemetryResponse` (`hostname`, `count`, `samples`, `notice`) | `app/api/telemetry.py:get_telemetry` |
| 5 | **GET** | `/api/endpoints/{hostname}/risk` | Path: `hostname` (str) | `RiskResponse` (`hostname`, `timestamp`, `anomaly_score`, `compromise_probability`, `severity`, `correlated_signal_count`, `contributing_signals`, `model_info`, `notice`) | `app/api/risk.py:get_endpoint_risk` |
| 6 | **GET** | `/api/endpoints/{hostname}/explanation` | Path: `hostname` (str) | `ExplanationResponse` (`hostname`, `timestamp`, `severity`, `summary`, `evidence`, `recommended_actions`, `notice`) | `app/api/explanation.py:get_endpoint_explanation` |
| 7 | **GET** | `/api/incidents` | Query: `status` (optional str: `OPEN`, `INVESTIGATING`, `RESOLVED`) | `IncidentListResponse` (`count`, `incidents`, `notice`) | `app/api/incidents.py:list_incidents` |
| 8 | **GET** | `/api/incidents/{incident_id}` | Path: `incident_id` (str, e.g. `INC-0001`) | `IncidentResponse` (`incident_id`, `hostname`, `created_at`, `updated_at`, `severity`, `compromise_probability`, `anomaly_score`, `status`, `summary`, `evidence`, `recommended_actions`) | `app/api/incidents.py:get_incident` |
| 9 | **PATCH** | `/api/incidents/{incident_id}` | Path: `incident_id`, Body: `IncidentStatusUpdate` (`status`: `OPEN` \| `INVESTIGATING` \| `RESOLVED`) | `IncidentResponse` | `app/api/incidents.py:update_incident_status` |
| 10 | **POST** | `/api/simulation/compromise` | Query: `hostname` (str, default `"HOST-042"`) | `SimulationActionResponse` (`hostname`, `compromised`, `compromised_since`, `affected_signals`, `sample`) | `app/api/simulation.py:trigger_compromise` |
| 11 | **POST** | `/api/simulation/reset` | None | `SimulationResetResponse` (`reset_hosts`, `notice`) | `app/api/simulation.py:reset_simulation` |

---

## D. REQUEST LIFECYCLE FORENSICS

### Trace: Analyst views Risk for Host `HOST-042` (`GET /api/endpoints/HOST-042/risk`)

```text
1. Frontend Client
   └─ Axios GET http://localhost:8000/api/endpoints/HOST-042/risk (frontend/src/lib/api.ts: fetchEndpointRisk)

2. Uvicorn Server & FastAPI Middleware
   └─ CORS Middleware validates origin (backend/app/main.py:L53-L59)
   └─ Router routes request to app/api/risk.py: get_endpoint_risk(hostname="HOST-042")

3. Validation & Data Fetching (backend/app/api/risk.py: get_threat_assessment)
   └─ Database check: db.get_endpoint_row("HOST-042") -> Returns SQLite row or 404
   └─ Database query: db.fetch_telemetry_rows("HOST-042", limit=1) -> Returns latest telemetry row

4. Feature Engineering & ML Scoring (backend/app/services/anomaly_detection.py: score)
   └─ Baseline extraction: _baseline_for("HOST-042") -> Retrieves host mean & std for 9 features
   └─ Z-Score conversion: _zscore_vector(row) -> Calculates z = (x - mean)/std clipped to [-10, 10]
   └─ Model inference: IsolationForest.score_samples([z_vector]) -> Returns raw decision score
   └─ Score calibration: _normalize_score(raw_score) -> Maps score against training distribution to [0, 100]
   └─ Deviation sorting: Generates FeatureDeviation objects sorted descending by |z_score|

5. Threat Correlation & Fusion (backend/app/services/threat_correlation.py: assess)
   └─ Noise gate evaluation: Filters deviations with |z| >= 2.0
   └─ Multi-signal fusion: compromise_prob = 0.5*ML + 0.3*Breadth*100 + 0.2*Severity*100
   └─ Severity classification: Maps score to "low", "medium", "high", or "critical"

6. Response Assembly & Serialization (backend/app/api/risk.py: build_risk_response)
   └─ Pydantic serialization: RiskResponse model validated against schema
   └─ HTTP 200 JSON returned to frontend
```

---

## E. TELEMETRY PIPELINE FORENSICS

### 1. Monitored Telemetry Schema (12 Fields):
1. `hostname` (TEXT): Host ID (e.g. `HOST-042`)
2. `timestamp` (TEXT): ISO-8601 UTC timestamp
3. `cpu_usage` (REAL, %): Host CPU utilization (1.0 to 100.0)
4. `memory_usage` (REAL, %): Host RAM utilization (5.0 to 100.0)
5. `network_connections` (INTEGER): Active socket connection count
6. `inbound_bytes` (INTEGER): Bytes received in interval
7. `outbound_bytes` (INTEGER): Bytes sent in interval
8. `dns_queries` (INTEGER): DNS lookup requests
9. `failed_logins` (INTEGER): Failed authentication attempts (Poisson distributed)
10. `successful_logins` (INTEGER): Successful authentications (Poisson distributed)
11. `new_processes` (INTEGER): New process executions spawned (Poisson distributed)
12. `unique_destinations` (INTEGER): Distinct remote IP addresses contacted

### 2. Distinction: Synthetic vs Real vs Simulated:
* **Synthetic:** Normal steady-state background telemetry generated algorithmically using per-host role distributions and smoothed random walks (`backend/app/services/telemetry_engine.py:L66-L101`).
* **Simulated:** Controlled compromise state triggered on demand via POST `/api/simulation/compromise` that programmatically injects multi-signal skew across 6 dimensions (`telemetry_engine.py:L104-L143`).
* **Real:** **NOT IMPLEMENTED**. No live kernel agents (eBPF) or operating system collectors are hooked up in this prototype.

---

## F. DATABASE FORENSICS

### Database Engine: SQLite 3 (`backend/sentinelx.db`)

#### 1. `endpoints` Table
* **Columns:** `id` (TEXT PK), `name` (TEXT), `type` (TEXT: `'system'`, `'firewall'`, `'router'`), `ip_address` (TEXT), `status` (TEXT), `risk_score` (REAL), `last_seen` (TEXT).
* **Purpose:** Fleet inventory metadata and current operational status.

#### 2. `telemetry` Table
* **Columns:** `id` (INTEGER PK AUTOINCREMENT), `hostname` (TEXT FK), `timestamp` (TEXT), `cpu_usage` (REAL), `memory_usage` (REAL), `network_connections` (INTEGER), `inbound_bytes` (INTEGER), `outbound_bytes` (INTEGER), `dns_queries` (INTEGER), `failed_logins` (INTEGER), `successful_logins` (INTEGER), `new_processes` (INTEGER), `unique_destinations` (INTEGER), `is_anomalous` (INTEGER).
* **Indices:** `CREATE INDEX IF NOT EXISTS idx_telemetry_hostname_ts ON telemetry (hostname, timestamp);`
* **Purpose:** Time-series telemetry logs for each host.

#### 3. `simulation_state` Table
* **Columns:** `hostname` (TEXT PK FK), `compromised` (INTEGER), `compromised_since` (TEXT).
* **Purpose:** Tracks ground truth simulation status per host.

#### 4. `incidents` Table
* **Columns:** `id` (INTEGER PK AUTOINCREMENT), `hostname` (TEXT FK), `created_at` (TEXT), `updated_at` (TEXT), `severity` (TEXT), `compromise_probability` (REAL), `anomaly_score` (REAL), `status` (TEXT: `'OPEN'`, `'INVESTIGATING'`, `'RESOLVED'`), `summary` (TEXT), `evidence` (TEXT JSON), `recommended_actions` (TEXT JSON).
* **Indices:** `CREATE INDEX IF NOT EXISTS idx_incidents_hostname_status ON incidents (hostname, status);`
* **Purpose:** Persistent tracking of high-confidence security incidents and analyst triage state.

---

## G. RISK SCORING MATHEMATICAL FORMULATION

The risk calculation in SentinelX is computed inside `backend/app/services/threat_correlation.py:L70-L112`:

### 1. Significant Signal Filtering:
A signal $i$ is significant if its absolute z-score meets the significance threshold:
$$|z_i| \ge 2.0$$

### 2. Multi-Signal Noise Gate:
Let $k = |\{i \mid |z_i| \ge 2.0\}|$ be the count of significant signals.
* If $k < 2$:
  $$\text{Correlation Breadth} = 0.0, \quad \text{Severity Factor} = 0.0$$
  $$\text{Compromise Probability} = 0.5 \times \text{Anomaly Score}$$
* If $k \ge 2$:
  $$\text{Correlation Breadth} = \min\left(\frac{k}{9}, 1.0\right)$$
  $$\text{Average Severity} = \frac{1}{k} \sum_{i=1}^{k} |z_i|$$
  $$\text{Severity Factor} = \min\left(\frac{\text{Average Severity}}{6.0}, 1.0\right)$$

### 3. Fusion Equation:
$$\text{Compromise Probability} = \text{clip}\left(0.50 \cdot A + 0.30 \cdot (B \times 100) + 0.20 \cdot (S \times 100), 0.0, 100.0\right)$$
Where:
* $A$ = Calibrated ML Anomaly Score ($0-100$)
* $B$ = Correlation Breadth ($0-1.0$)
* $S$ = Severity Factor ($0-1.0$)

### 4. Severity Tier Mapping:
* $\text{Compromise Probability} \ge 75.0 \rightarrow \mathbf{CRITICAL}$
* $\text{Compromise Probability} \ge 50.0 \rightarrow \mathbf{HIGH}$
* $\text{Compromise Probability} \ge 25.0 \rightarrow \mathbf{MEDIUM}$
* $\text{Compromise Probability} < 25.0 \rightarrow \mathbf{LOW}$

---

## H. INCIDENT GENERATION & DEDUPLICATION

* **Trigger Condition:** `compromise_probability >= 80.0` (`INCIDENT_CREATION_THRESHOLD` in `app/services/incident_management.py:L24`).
* **Deduplication Guard:** `get_active_incident_for_host(hostname)` checks if there is already an existing ticket with `status IN ('OPEN', 'INVESTIGATING')`. If an active ticket exists, **no new ticket is created**.
* **Reopening Logic:** If a previous ticket was marked `RESOLVED` and the host experiences a new compromise crossing the $80.0$ threshold, a new incident ticket (e.g. `INC-0002`) is opened.

---

## I. ERROR HANDLING AUDIT

1. **Unknown Host Parameter:** Returns HTTP `404 Not Found` (`{"detail": "Unknown endpoint 'HOST-999'"}`).
2. **Missing Telemetry on Host:** Returns HTTP `404 Not Found` (`{"detail": "No telemetry recorded yet for 'HOST-001'"}`).
3. **Model Inference before Training:** Raises `NotTrainedError` caught by router and returned as HTTP `503 Service Unavailable`.
4. **Invalid Status Transition in PATCH:** Returns HTTP `422 Unprocessable Entity` if status is not one of `('OPEN', 'INVESTIGATING', 'RESOLVED')`.
5. **Zero Baseline Division Safety:** In `app/services/explanation.py:L85-L91`, if baseline mean is 0 (e.g. failed logins on quiet workstation), percent change returns `None` instead of throwing `ZeroDivisionError`.

---

## J. SECURITY POSTURE AUDIT TABLE

| Security Control | Status | Forensic Finding in Codebase |
| :--- | :--- | :--- |
| **SQL Injection Protection** | **IMPLEMENTED** | Parameterized SQL queries (`?` and `:name`) across all database operations. |
| **CORS Policy** | **IMPLEMENTED** | Strict origin whitelist restricted to `localhost:5173` and `127.0.0.1:5173`. |
| **Input Validation** | **IMPLEMENTED** | Pydantic schemas enforce type checking, string literals, and boundary limits. |
| **Authentication (JWT/OAuth)**| **NOT IMPLEMENTED** | All API routes are currently public without token verification. |
| **Authorization / RBAC** | **NOT IMPLEMENTED** | No role separation between admin and viewer in backend routes. |
| **Rate Limiting** | **NOT IMPLEMENTED** | No rate limiting middleware configured on endpoints. |
| **Secrets Management** | **NOT IMPLEMENTED / N/A** | No external third-party API keys or sensitive database passwords required. |
| **mTLS / Endpoint Signing**| **NOT IMPLEMENTED** | Telemetry ingestion endpoint is not secured with client TLS certificates. |
