# SENTINELX BACKEND ENGINEER — MASTER CHEAT SHEET
**Author:** Backend Engineer  
**Purpose:** Compact, High-Density Personal Revision for Smart India Hackathon  

---

## 1. MY ROLE
"I am the backend engineer for SentinelX. I designed and implemented the asynchronous FastAPI service, the SQLite persistence layer, the per-host z-score normalization pipeline, the threat correlation fusion engine, and the REST APIs connecting our ML models to the SOC dashboard."

---

## 2. PROJECT IN ONE SENTENCE
"SentinelX is an AI-powered security analytics platform that detects multi-signal enterprise compromises by evaluating host-normalized statistical telemetry deviations using an unsupervised Isolation Forest and a noise-filtering correlation engine."

---

## 3. PROJECT IN 30 SECONDS
"Traditional EDRs rely on file signatures and predefined rules, leaving them blind to zero-day attacks and legitimate credential abuse. SentinelX solves this by learning individual baseline behavior for every network host across 9 telemetry signals. When an attack occurs, our two-stage pipeline normalizes deviations into per-host z-scores, scores them via an Isolation Forest, filters out single-metric noise, and delivers mathematically explainable incident tickets to SOC analysts in real time."

---

## 4. PROJECT IN 60 SECONDS
"In an enterprise environment, a firewall pushing gigabytes of traffic is normal, but the same traffic on an HR workstation is a critical breach. SentinelX solves this host asymmetry problem. Our backend ingests multi-dimensional host telemetry, transforms metrics into per-host z-scores, and feeds them into an unsupervised Isolation Forest. 

To eliminate false alarms, our correlation engine enforces a multi-signal noise gate—requiring simultaneous deviations across independent signal families like DNS, outbound traffic, and process spawning before escalating an incident. When compromise probability exceeds 80%, SentinelX automatically creates deduplicated incident tickets complete with percentage evidence contribution breakdowns and actionable response playbooks."

---

## 5. MY BACKEND ARCHITECTURE
```text
FastAPI Lifespan -> SQLite Init -> Backfill History (60 samples/host)
       │
       ▼
Background Async Loop (ticks every 4s) -> Ingests Telemetry -> SQLite
       │
       ▼
Anomaly Detection Service (Computes Z-Scores -> IsolationForest Inference)
       │
       ▼
Threat Correlation Engine (50% ML + 30% Breadth + 20% Severity)
       │
       ▼
Incident Management Service (Threshold >= 80.0 -> Deduplication Check -> Open Ticket)
       │
       ▼
11 REST API Endpoints -> JSON over HTTP -> React Dashboard
```

---

## 6. MY API ENDPOINTS (11 ENDPOINTS)
1. `GET /api/health` — Health check and prototype transparency notice.
2. `GET /api/endpoints` — Fleet inventory list.
3. `GET /api/endpoints/{hostname}` — Individual endpoint metadata.
4. `GET /api/telemetry/{hostname}` — Historical telemetry log (limit query).
5. `GET /api/endpoints/{hostname}/risk` — Current ML anomaly score & compromise probability.
6. `GET /api/endpoints/{hostname}/explanation` — Narrative summary, evidence items & playbooks.
7. `GET /api/incidents` — Incident tickets with optional status filter.
8. `GET /api/incidents/{id}` — Specific incident ticket details.
9. `PATCH /api/incidents/{id}` — Analyst workflow status update (`OPEN`/`INVESTIGATING`/`RESOLVED`).
10. `POST /api/simulation/compromise` — Injects multi-signal compromise skew.
11. `POST /api/simulation/reset` — Resets fleet to clean baseline.

---

## 7. MY DATABASE
* **Engine:** SQLite 3 (`backend/sentinelx.db`), raw `sqlite3` driver with parameterized queries.
* **4 Tables:**
  1. `endpoints`: Host ID, role, IP, status, last_seen.
  2. `telemetry`: 12 metrics + `is_anomalous` with index on `(hostname, timestamp)`.
  3. `simulation_state`: `compromised` boolean and timestamp.
  4. `incidents`: Severity, scores, status (`OPEN`/`INVESTIGATING`/`RESOLVED`), JSON evidence, JSON playbooks.

---

## 8. TELEMETRY
* **Source:** Synthetic engine in `app/services/telemetry_engine.py`.
* **9 ML Features:** `cpu_usage`, `memory_usage`, `network_connections`, `inbound_bytes`, `outbound_bytes`, `dns_queries`, `failed_logins`, `new_processes`, `unique_destinations`.

---

## 9. ML INTEGRATION
* **Model:** Unsupervised `IsolationForest` (`n_estimators=200`, `random_state=42`).
* **Normalization:** Per-host z-score $z = \text{clip}\left(\frac{x - \mu}{\sigma}, -10, 10\right)$ with variance floor $\max(0.5, 0.02 \times |\mu|)$.
* **Calibration:** Linear mapping mapping training median to 0 and training max to 100.

---

## 10. RISK PIPELINE
$$\text{Compromise Probability} = 0.50 \cdot (\text{ML Score}) + 0.30 \cdot (\text{Breadth} \times 100) + 0.20 \cdot (\text{Severity} \times 100)$$
* **Noise Gate:** If significant deviations ($|z| \ge 2.0$) are $<2$, Breadth and Severity are clamped to 0.0.
* **Tiers:** $\ge 75$ Critical, $\ge 50$ High, $\ge 25$ Medium, $<25$ Low.

---

## 11. INCIDENT PIPELINE
* **Threshold:** Compromise Probability $\ge 80.0$.
* **Deduplication:** Checks `get_active_incident_for_host()`. If `OPEN` or `INVESTIGATING` exists, suppresses duplicates.
* **Lifecycle:** `OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED`.

---

## 12. DEMO
* Clicking "Simulate Attack" executes `POST /api/simulation/compromise?hostname=HOST-042`.
* Multiplies outbound bytes 6-15x, DNS 4-9x, destination diversity 5-12x, spawns processes, injects failed logins.
* Anomaly score surges to $>90$, compromise probability hits $>85\%$, and incident `INC-0001` is opened.

---

## 13. ACTUAL ML RESULTS
* **Unsupervised Model:** No static labeled test-set accuracy exists in the repository.
* **Verified Metric:** 53/53 automated unit tests pass, verifying baseline separation, noise rejection, and mathematical bounds.

---

## 14. BIGGEST STRENGTH
"Our two-stage per-host z-score normalization that solves host asymmetry and our multi-signal noise gate that eliminates single-metric false alarms."

---

## 15. BIGGEST WEAKNESS
"The current prototype uses synthetic telemetry generated in software rather than live kernel eBPF collectors."

---

## 16. WHAT IS NOT IMPLEMENTED
1. Live eBPF kernel agents / PCAP ingestion.
2. User authentication (JWT / OAuth2).
3. Distributed message queues (Kafka / Redis Streams).
4. Multi-tenant database partitioning.

---

## 17. FUTURE SCOPE
1. Lightweight Rust/eBPF kernel telemetry agents for Linux/Windows.
2. Apache Kafka streaming ingestion with TimescaleDB time-series storage.
3. Automated SOAR containment playbooks via firewall API integrations.

---

## 18. FIVE SENTENCES I SHOULD MEMORIZE
1. "We normalize all features to per-host z-scores before running Isolation Forest to ensure device role asymmetry is respected."
2. "Our correlation layer enforces a strict noise gate requiring at least two independent signal deviations before escalating an alert."
3. "All 11 API endpoints are strictly validated using Pydantic v2 schemas and parameterized SQLite queries to prevent injection attacks."
4. "Our incident engine performs active ticket deduplication to prevent SOC alert fatigue during prolonged attacks."
5. "Our model is unsupervised; we evaluate statistical baseline separation and mathematical bounds across 53 automated unit tests."

---

## 19. FIVE THINGS I MUST NEVER CLAIM
1. ❌ **NEVER CLAIM** "We have 99.4% accuracy" (Isolation Forest is unsupervised; no labeled accuracy exists).
2. ❌ **NEVER CLAIM** "This is live network traffic from real computers" (It is a synthetic telemetry generator).
3. ❌ **NEVER CLAIM** "We replace CrowdStrike or Splunk" (We are a specialized behavioral correlation layer).
4. ❌ **NEVER CLAIM** "Our backend uses Kafka and Kubernetes right now" (Our current demo runs on async FastAPI and SQLite).
5. ❌ **NEVER CLAIM** "We detect specific malware names" (We detect behavioral deviations and explicitly caveat attribution in summaries).

---

## 20. TEN MOST LIKELY JUDGE QUESTIONS & SHORT ANSWERS
1. **Q: What is your backend framework?**  
   *A: FastAPI with Python 3.12, running asynchronously on Uvicorn.*
2. **Q: Where is your model executed?**  
   *A: In-memory inside `AnomalyDetectionService.score()` taking $<1.2\text{ms}$ per host.*
3. **Q: What database are you using?**  
   *A: SQLite 3 using parameterized queries with zero ORM overhead.*
4. **Q: How do you prevent single metric false alarms?**  
   *A: Our multi-signal noise gate requires at least 2 independent signals with $|z| \ge 2.0$ to boost risk.*
5. **Q: How is risk calculated?**  
   *A: $0.50 \times \text{ML Anomaly Score} + 0.30 \times \text{Correlation Breadth} + 0.20 \times \text{Severity Factor}$.*
6. **Q: Where does the telemetry come from?**  
   *A: Synthetically generated via Poisson and Gaussian distributions modeling 5 distinct host roles.*
7. **Q: How does the system handle zero-variance features?**  
   *A: We apply a standard deviation floor $\max(0.5, 0.02 \times |\mu|)$ to prevent zero division.*
8. **Q: What triggers an incident ticket?**  
   *A: Compromise probability $\ge 80.0\%$ combined with an active ticket deduplication check.*
9. **Q: How do you handle concept drift?**  
   *A: The background loop retrains the Isolation Forest every 30 ticks (~2 minutes) on confirmed normal history.*
10. **Q: How would you scale to 10,000 hosts?**  
    *A: Decouple ingestion via Apache Kafka, process with stateless Celery/FastAPI workers, and persist in TimescaleDB.*
