# SENTINELX — BACKEND HOSTILE QUESTIONS (40 TARGETED DEFENSE ANSWERS)
**Role:** Backend Engineer Defense  
**Focus:** Pure Backend, Systems Architecture, Concurrency, and Data Pipelines  

---

### 1. Why did you choose this backend framework?
**Answer:** We chose **FastAPI (0.115.6)** because it is natively built on the ASGI specification (`Starlette`), providing high-concurrency asynchronous event handling (`async def _telemetry_loop`), native Pydantic v2 data validation, and automatic OpenAPI schema generation. Flask requires external libraries for async and OpenAPI; Django carries heavy ORM overhead.  
**Code Evidence:** `backend/app/main.py:L1-L68`, `backend/requirements.txt:L1`.

---

### 2. Why this database?
**Answer:** We chose **SQLite 3** via Python's standard `sqlite3` driver with zero external server dependencies, embedded in-process execution (`backend/sentinelx.db`), and sub-millisecond query execution for our 5-host demo fleet.  
**Code Evidence:** `backend/app/db/database.py:L9-L17`.

---

### 3. Why not PostgreSQL?
**Answer:** PostgreSQL is our target production database. However, for a self-contained hackathon prototype, SQLite eliminated external container/daemon setup requirements and network socket latency while fully supporting standard SQL DDL, compound indices, and transactional integrity (`get_connection()`).  
**Code Evidence:** `backend/app/db/database.py:L84-L93`.

---

### 4. Why not MongoDB?
**Answer:** Security telemetry and incident management have strict relational integrity requirements: foreign keys between `telemetry.hostname -> endpoints.id` and `incidents.hostname -> endpoints.id`. Unstructured NoSQL databases like MongoDB lack ACID relational constraints and introduce unnecessary schema validation complexity in the database layer.  
**Code Evidence:** `backend/app/db/database.py:L44, L52, L67`.

---

### 5. How does the frontend communicate with the backend?
**Answer:** Over **HTTP/1.1 REST using JSON payloads**. The frontend Axios client (`frontend/src/lib/api.ts`) polls the backend every 7 seconds (`useDashboardData.ts`) and triggers simulation POST requests.  
**Code Evidence:** `frontend/src/lib/api.ts:L1-L9`, `frontend/src/hooks/useDashboardData.ts:L15-L25`.

---

### 6. What are your APIs?
**Answer:** We have **11 REST endpoints across 7 routers**:
* Health: `GET /api/health`
* Endpoints: `GET /api/endpoints`, `GET /api/endpoints/{hostname}`
* Telemetry: `GET /api/telemetry/{hostname}`
* Simulation: `POST /api/simulation/compromise`, `POST /api/simulation/reset`
* Risk: `GET /api/endpoints/{hostname}/risk`
* Explanation: `GET /api/endpoints/{hostname}/explanation`
* Incidents: `GET /api/incidents`, `GET /api/incidents/{id}`, `PATCH /api/incidents/{id}`  
**Code Evidence:** `backend/app/main.py:L61-L67`.

---

### 7. How do you validate incoming data?
**Answer:** Using **Pydantic v2 schemas** (`backend/app/api/schemas.py`). Every query param, path param, and request body is parsed and strictly validated. For example, `IncidentStatusUpdate` enforces literal `'OPEN' | 'INVESTIGATING' | 'RESOLVED'`, rejecting invalid inputs with HTTP 422.  
**Code Evidence:** `backend/app/api/schemas.py:L138-L139`.

---

### 8. Where is the ML model called?
**Answer:** The model is called inside `AnomalyDetectionService.score(row)` in `backend/app/services/anomaly_detection.py:L142-L174`, which is invoked by `get_threat_assessment()` in `backend/app/api/risk.py:L25` and `run_incident_detection()` in `backend/app/services/incident_management.py:L114`.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L142`, `backend/app/api/risk.py:L25`.

---

### 9. Is ML inference synchronous or asynchronous?
**Answer:** Inference is **synchronous** in memory. Because Isolation Forest scoring on a 9-dimensional vector takes less than 1.2 milliseconds, executing it synchronously in the route handler avoids task context-switching overhead.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L150-L151`.

---

### 10. What happens if inference fails?
**Answer:** If inference is attempted before the model is trained, `AnomalyDetectionService.score()` raises a custom `NotTrainedError`. In `backend/app/api/risk.py:L26-L27`, this is caught and translated to an HTTP `503 Service Unavailable` with a clean error payload. In the background loop, it is caught and skipped safely.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L53-L54`, `backend/app/api/risk.py:L26-L27`.

---

### 11. What happens if the database fails?
**Answer:** The `get_connection()` context manager in `backend/app/db/database.py:L84-L93` guarantees that if any SQL query raises an exception, the transaction is aborted and the connection is closed in the `finally:` block, preventing locked connections. FastAPI catches unhandled exceptions and returns HTTP 500 without crashing the worker process.  
**Code Evidence:** `backend/app/db/database.py:L84-L93`.

---

### 12. How do you handle 1 endpoint?
**Answer:** The background loop ticks that single endpoint every 4 seconds, stores its row in `telemetry`, fits its baseline parameters ($\mu, \sigma$), and scores incoming rows against its baseline.  
**Code Evidence:** `backend/app/services/telemetry_engine.py:L153-L163`.

---

### 13. How would you handle 10,000 endpoints?
**Answer:** We would decouple ingestion from scoring:
1. Endpoints stream JSON payloads over gRPC or HTTPS to an NGINX load balancer.
2. Ingestion service pushes raw events into an **Apache Kafka** cluster partitioned by `hostname`.
3. Worker consumer groups score batches in parallel and update cached Redis baselines.  
**Code Evidence:** Documented in `docs/PROJECT_FORENSIC_AUDIT.md: Section 5`.

---

### 14. How would you handle millions of telemetry events?
**Answer:** We would replace SQLite with **TimescaleDB** (PostgreSQL extension for time-series hypertables) with automated compression chunks and a 30-day tiered retention policy dropping raw events older than 90 days.  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 15. Where is the bottleneck in your current architecture?
**Answer:** In the current prototype, the single SQLite database file write lock is the bottleneck under high concurrent write loads ($>1,000$ writes/sec). Read queries scale cleanly, but high concurrent writes require a multi-threaded database like PostgreSQL.  
**Code Evidence:** `backend/app/db/database.py:L86`.

---

### 16. How would you scale the backend?
**Answer:** By containerizing the FastAPI application with Docker, running multiple Gunicorn worker processes with `UvicornWorker`, placing them behind an NGINX reverse proxy, and using PostgreSQL with connection pooling (PgBouncer).  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 17. Would you use Kafka?
**Answer:** **Yes, in production.** Kafka provides distributed partitioning by `hostname`, ensuring that all telemetry from a single host arrives in strict chronological order at the dedicated worker pod maintaining that host's state.  
**Code Evidence:** `docs/PROJECT_FORENSIC_AUDIT.md`.

---

### 18. Would you use Redis?
**Answer:** **Yes.** Redis would be used for two critical caching functions:
1. Storing active per-host baseline statistics ($\mu_h, \sigma_h$) in Redis In-Memory Hashes for sub-millisecond retrieval by worker nodes.
2. Rate-limiting endpoint check-ins.  
**Code Evidence:** `docs/PROJECT_FORENSIC_AUDIT.md`.

---

### 19. Would you use a message queue?
**Answer:** Yes, RabbitMQ or Redis Streams for lightweight queuing (<5,000 hosts), or Apache Kafka for enterprise fleets (>50,000 hosts).  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 20. How would you separate ingestion from inference?
**Answer:**
* **Ingest Service (FastAPI):** Validates schema, writes event to Kafka topic `raw-telemetry`, returns HTTP 202 Accepted.
* **Inference Service (Python Celery / Kafka Consumer):** Reads stream, fetches cached baseline, scores via Isolation Forest, writes anomalies to `anomalies` topic.  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 21. How would you deploy this?
**Answer:** Using a multi-stage Dockerfile deployed on Kubernetes (EKS/GKE) with Horizontal Pod Autoscaling (HPA) based on CPU utilization and Kafka consumer lag metrics.  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 22. How would you secure the APIs?
**Answer:** Enforce OAuth2 with JWT bearer tokens (`Authorization: Bearer <token>`), RBAC separating SOC Tier-1 analysts (read-only) from Tier-3 responders (write/patch status), and TLS 1.3 termination at the reverse proxy.  
**Code Evidence:** `docs/BACKEND_ENGINEER_MASTER.md: Section K`.

---

### 23. How would you authenticate endpoints?
**Answer:** Using **Mutual TLS (mTLS)** with X.509 certificates generated per endpoint during agent provisioning, rejecting any connection without a valid CA signature.  
**Code Evidence:** `docs/PROJECT_FORENSIC_AUDIT.md`.

---

### 24. How would you prevent telemetry spoofing?
**Answer:** Sign every telemetry payload using HMAC-SHA256 with a unique pre-shared secret per endpoint stored in hardware TPM/Secure Enclave and include an incrementing monotonic sequence number to reject replay attacks.  
**Code Evidence:** `docs/BACKEND_ENGINEER_MASTER.md`.

---

### 25. How do you handle duplicate telemetry?
**Answer:** By adding a unique compound constraint `(hostname, timestamp)` in the database and discarding duplicate sequence timestamps on ingestion.  
**Code Evidence:** `backend/app/db/database.py:L46`.

---

### 26. How do you handle missing telemetry?
**Answer:** If a host does not report for $>30$ seconds, an endpoint health monitor marks its status as `'offline'` in `endpoints.status` and raises an `Agent Offline` alert.  
**Code Evidence:** `backend/app/db/database.py:L24, L128-L133`.

---

### 27. How do you handle malformed telemetry?
**Answer:** Pydantic schema validation rejects malformed types, missing fields, or out-of-range numerical metrics at the API boundary before passing them to the database or ML engine.  
**Code Evidence:** `backend/app/api/schemas.py:L31-L45`.

---

### 28. How do you handle concept drift?
**Answer:** By executing periodic baseline retraining in the background loop (`app/main.py:L31-L32`) every 30 ticks (~2 minutes) using all historical telemetry confirmed normal (`db.fetch_normal_telemetry_rows()`), ensuring the learned baseline adapts to organic load changes.  
**Code Evidence:** `backend/app/main.py:L31-L32`, `backend/app/db/database.py:L162-L170`.

---

### 29. How do you update behavioural baselines?
**Answer:** `AnomalyDetectionService.train()` re-aggregates historical normal telemetry per host, recomputes mean and standard deviation per feature, applies variance floors, and re-fits the Isolation Forest.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L82-L110`.

---

### 30. How do you prevent one anomaly from becoming a false alarm?
**Answer:** We enforce the **Multi-Signal Noise Filter Gate** (`app/services/threat_correlation.py:L76-L83`): a single metric spike (e.g. temporary CPU surge or single failed login) has its correlation breadth and severity factors clamped to **0.0**, keeping compromise probability low (<25%) and preventing false alarms.  
**Code Evidence:** `backend/app/services/threat_correlation.py:L76-L83`.

---

### 31. How is risk calculated?
**Answer:** Through our fusion equation in `threat_correlation.py:L84-L88`:
$$\text{Compromise Probability} = 0.50 \times \text{ML Anomaly Score} + 0.30 \times (\text{Breadth} \times 100) + 0.20 \times (\text{Severity} \times 100)$$  
**Code Evidence:** `backend/app/services/threat_correlation.py:L84-L90`.

---

### 32. Is risk a probability?
**Answer:** It is a calibrated risk index on a scale of $[0.0, 100.0]$ representing our fused confidence of compromise based on mathematical anomaly severity and multi-signal breadth. It is not a frequentist Bayesian probability of binary event occurrence.  
**Code Evidence:** `backend/app/services/threat_correlation.py:L84-L90`.

---

### 33. Where are incidents stored?
**Answer:** In the `incidents` table in SQLite (`sentinelx.db`), serialized with full JSON evidence items and recommended action playbooks.  
**Code Evidence:** `backend/app/db/database.py:L55-L69`.

---

### 34. What is your data retention strategy?
**Answer:** In production: 30 days of high-resolution 5-second telemetry, 90 days of 1-minute aggregated summaries, and 1 year of incident records and forensic evidence logs.  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 35. What happens when an endpoint goes offline?
**Answer:** The `endpoints` table updates `last_seen`. In production, a heartbeat watchdog flags devices with no check-in after 30 seconds as `'disconnected'`.  
**Code Evidence:** `backend/app/db/database.py:L128-L133`.

---

### 36. How would you integrate with a SIEM?
**Answer:** By streaming generated incident tickets over a Syslog / CEF (Common Event Format) forwarder or via webhook POST requests into Splunk HEC (HTTP Event Collector) or Elastic Logstash.  
**Code Evidence:** `docs/ARCHITECTURE.md`.

---

### 37. How would you integrate with an EDR?
**Answer:** By using SentinelX as the analytical behavioral correlation layer that receives telemetry from the EDR agent and sends automated isolation commands back to the EDR API when an incident severity is `CRITICAL`.  
**Code Evidence:** `backend/app/services/explanation.py:L170-L173`.

---

### 38. What makes this different from an EDR?
**Answer:** EDRs focus on kernel-level execution hooks, file hash signatures, and process injection detection on a single host. SentinelX focuses on **fleet-wide multi-signal statistical baseline correlation** and deterministic explainability.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L1-L6`.

---

### 39. What makes this different from a SIEM?
**Answer:** SIEMs rely on pre-written static correlation rules (`IF failed_logins > 5 THEN alert`). SentinelX uses **unsupervised statistical learning (Isolation Forest + Z-Scores)** to learn what is normal for each individual host dynamically without human rule authoring.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L93-L109`.

---

### 40. What part is actually your innovation?
**Answer:** Our core technical innovation is the **Two-Stage Hybrid Pipeline**:
1. Solving **host asymmetry** by converting raw multi-dimensional metrics into per-host z-score normalized feature vectors with dynamic variance floors.
2. Fusing unsupervised Isolation Forest decision paths with an explicit **Multi-Signal Noise Filter Gate** that eliminates single-metric false alarms and produces deterministic, mathematically provable evidence breakdowns.  
**Code Evidence:** `backend/app/services/anomaly_detection.py:L111-L185` and `backend/app/services/threat_correlation.py:L70-L112`.
