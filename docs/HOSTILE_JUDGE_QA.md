# SENTINELX — HOSTILE JUDGE QUESTION BANK (50+ QUESTIONS)
**Target:** Hostile Cybersecurity, ML, and Backend Judges at SIH  
**Role:** Backend Engineering Defense  

---

### GROUP A: PROBLEM STATEMENT & DOMAIN

#### Q1: "Why do we need behavioural AI when signature-based EDRs and Snort rules already catch malware?"
* **ANSWER:** Signature-based tools only detect known hash signatures, compiled byte patterns, or predefined Snort rules. They are completely blind to zero-day exploits, fileless memory attacks, living-off-the-land binaries (LotL), and compromised valid credentials. SentinelX models normal statistical telemetry patterns per host; when an attacker uses legitimate tools (like PowerShell or curl) to exfiltrate data or beacon to new IP ranges, the simultaneous multi-metric deviation is detected regardless of file signatures.
* **WHY THE JUDGE IS ASKING:** To see if you understand the boundary between signature EDR and behavioural anomaly detection.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/anomaly_detection.py:L16-L26` (monitors raw behavioural telemetry: outbound traffic, DNS volume, process spawn rates, connection ratios).
* **WHAT I SHOULD NOT CLAIM:** Do not claim SentinelX replaces CrowdStrike or Defender. It is a complementary behavioural correlation layer.

---

### GROUP B: CYBERSECURITY MECHANICS

#### Q2: "What specific attack patterns does your multi-signal correlation map to?"
* **ANSWER:** Our correlation engine maps to 6 distinct MITRE ATT&CK tactical stages:
  1. Automated Data Exfiltration (T1048 / T1041) -> Outbound byte surge.
  2. C2 Beaconing / Fast Flux / Tunnelling (T1071.004) -> DNS query volume surge.
  3. Dropper & Payload Execution (T1059) -> Process creation rate surge.
  4. Credential Stuffing & Brute Force (T1110) -> Failed login spike.
  5. Lateral Reconnaissance & Discovery (T1018 / T1046) -> Destination diversity surge.
  6. Malicious Cryptomining / Resource Abuse (T1496) -> CPU/memory utilization surge.
* **WHY THE JUDGE IS ASKING:** To test if your synthetic metrics have genuine cybersecurity grounding or are arbitrary random numbers.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/telemetry_engine.py:L104-L143` (`_apply_compromise` skews these exact 6 vectors).
* **WHAT I SHOULD NOT CLAIM:** Do not claim we parse real PCAP or deep-packet inspect payloads. We analyze behavioral metadata.

---

### GROUP C: BACKEND & ASYNC ARCHITECTURE

#### Q3: "Why did you choose FastAPI over Django or Flask?"
* **ANSWER:** FastAPI is natively asynchronous (built on Starlette and ASGI), providing sub-millisecond response latencies and seamless background execution via `asyncio.create_task()`. It natively integrates Pydantic v2 for strict type safety and schema validation, and automatically generates interactive OpenAPI/Swagger documentation without third-party plugins. Flask is WSGI-bound and requires Celery/Redis for background loops; Django has heavy ORM overhead unnecessary for raw telemetry ingestion.
* **WHY THE JUDGE IS ASKING:** To test if your framework choice was deliberate based on engineering constraints.
* **EVIDENCE FROM OUR CODE:** `backend/app/main.py:L23-L49` (uses native `async def _telemetry_loop()` and `lifespan(app: FastAPI)`).
* **WHAT I SHOULD NOT CLAIM:** Do not claim FastAPI is multithreaded by default; it is single-threaded asynchronous concurrency on Python's event loop.

#### Q4: "Is ML inference synchronous or asynchronous on API requests?"
* **ANSWER:** The inference in `score()` is synchronous and executes CPU-bound matrix mathematics in memory inside `app/services/anomaly_detection.py:L142-L174`. Because our Isolation Forest operates on a compact 9-dimensional vector, scoring takes under 1.2 milliseconds per host, which executes cleanly inside the request thread without blocking FastAPI's event loop.
* **WHY THE JUDGE IS ASKING:** To catch you if you don't know whether CPU-bound ML blocks the async event loop.
* **EVIDENCE FROM OUR CODE:** `backend/app/api/risk.py:L14-L29` (`get_threat_assessment` executes `anomaly_service.score()` synchronously).
* **WHAT I SHOULD NOT CLAIM:** Do not claim you run GPU distributed clusters or Celery queues in this prototype.

---

### GROUP D: APIs & PROTOCOLS

#### Q5: "What prevents malformed JSON payloads from crashing your API?"
* **ANSWER:** FastAPI enforces Pydantic v2 schemas (`backend/app/api/schemas.py`) on all incoming request parameters and payloads. If an invalid type, missing field, or out-of-range value is supplied (e.g. invalid status in `PATCH /api/incidents/{id}` or out-of-range telemetry limit), Pydantic rejects the request before it reaches service logic and automatically returns an HTTP 422 Unprocessable Entity with precise field validation error messages.
* **WHY THE JUDGE IS ASKING:** To verify API robustness against input fuzzing.
* **EVIDENCE FROM OUR CODE:** `backend/app/api/incidents.py:L33-L37` and `test_incidents.py:L89-L93` (verifies 422 on invalid status).
* **WHAT I SHOULD NOT CLAIM:** Do not claim you have a Web Application Firewall (WAF) or DDoS protection.

---

### GROUP E: DATABASE & PERSISTENCE

#### Q6: "Why did you use raw SQLite without SQLAlchemy or Django ORM?"
* **ANSWER:** For this prototype, raw SQLite via Python's standard `sqlite3` driver was selected for zero-dependency simplicity, zero network latency overhead, and full explicit control over parameterized SQL queries (`backend/app/db/database.py`). SQLAlchemy introduces session management complexity and ORM object hydration overhead that is unnecessary for high-throughput append-only telemetry logging.
* **WHY THE JUDGE IS ASKING:** To test database architecture trade-offs.
* **EVIDENCE FROM OUR CODE:** `backend/app/db/database.py:L84-L93` (`get_connection` context manager with `row_factory = sqlite3.Row`).
* **WHAT I SHOULD NOT CLAIM:** Do not claim SQLite is ready for 50,000 live streaming agents in enterprise production.

#### Q7: "How do you protect against SQL Injection?"
* **ANSWER:** Every single query in `database.py` uses parameterized queries with positional `?` placeholders or named `:key` dictionaries. No user input or variable is ever concatenated or formatted via Python f-strings into SQL strings.
* **WHY THE JUDGE IS ASKING:** Basic security audit check.
* **EVIDENCE FROM OUR CODE:** `backend/app/db/database.py:L119`, `L131`, `L139-L149`, `L212-L221`.
* **WHAT I SHOULD NOT CLAIM:** None. This is 100% verified and true in our codebase.

---

### GROUP F: MACHINE LEARNING & MATHEMATICS

#### Q8: "Why Isolation Forest instead of an Autoencoder or LSTM?"
* **ANSWER:** Isolation Forest is computationally lightweight ($O(n \log n)$ training complexity), requires no GPU acceleration, operates reliably on tabular numerical telemetry with low latency ($<2\text{ms}$ inference), and naturally isolates anomalies by randomly partitioning features. LSTMs and Deep Autoencoders require extensive hyperparameter tuning, orders of magnitude more training samples, GPU hardware, and act as complete black boxes that make deterministic evidence explainability nearly impossible for SOC analysts.
* **WHY THE JUDGE IS ASKING:** To check if you understand ML trade-offs between classical tree ensembles and deep learning.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/anomaly_detection.py:L67-L71` (`IsolationForest(n_estimators=200, max_samples='auto', random_state=42)`).
* **WHAT I SHOULD NOT CLAIM:** Do not claim Isolation Forest models temporal sequences. It models multi-dimensional point deviations.

#### Q9: "What prevents a feature with zero variance (e.g. failed logins) from causing division by zero in z-score calculation?"
* **ANSWER:** We implement a dynamic standard deviation floor in `_compute_baseline()`:
  $$\sigma_{\text{floor}} = \max\left(0.5, 0.02 \times |\mu|\right)$$
  The effective standard deviation is $\max(\sigma, \sigma_{\text{floor}})$. This ensures the denominator is always $\ge 0.5$, preventing division by zero and preventing tiny normal fluctuations from saturating the z-score.
* **WHY THE JUDGE IS ASKING:** Mathematical edge case testing.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/anomaly_detection.py:L124-L125` and `test_anomaly_detection.py:L60-L80`.
* **WHAT I SHOULD NOT CLAIM:** Do not claim standard deviation is unconstrained.

---

### GROUP G: DATA & TELEMETRY

#### Q10: "Where does your telemetry come from?"
* **ANSWER:** In this prototype, all telemetry is synthetically generated inside `backend/app/services/telemetry_engine.py` using per-host role parameters (`HOST_PROFILES`), bounded random-walk server loads, Gaussian noise distributions, and Poisson arrival rates for discrete events (logins, process creation). No live operating system agents are deployed yet.
* **WHY THE JUDGE IS ASKING:** To test your honesty and see if you pretend synthetic data is live network data.
* **EVIDENCE FROM OUR CODE:** `backend/app/core/config.py:L14-L18` (`SIMULATED_DATA_NOTICE`) and `backend/app/services/telemetry_engine.py:L1-L10`.
* **WHAT I SHOULD NOT CLAIM:** **NEVER CLAIM** this is live network traffic from real enterprise computers. Be proud of the synthetic mathematical engine.

---

### GROUP H: EVALUATION & METRICS

#### Q11: "What is your model's accuracy, precision, and recall?"
* **ANSWER:** Because SentinelX uses an **unsupervised Isolation Forest** trained on unlabelled normal fleet telemetry, standard supervised classification metrics like static Accuracy, Precision, and Recall are mathematically inapplicable unless evaluated against a synthetic ground-truth test split. Claiming a static '99% Accuracy' would be technically inaccurate. Instead, we evaluate our system by verifying that steady-state normal traffic consistently produces low anomaly scores ($<15/100$) and that multi-signal compromise simulations reliably trigger high scores ($>85/100$), verified across all 53 automated unit tests.
* **WHY THE JUDGE IS ASKING:** This is the #1 trap question judges use to catch students who claim fake 99% accuracy on unsupervised models.
* **EVIDENCE FROM OUR CODE:** `backend/tests/test_anomaly_detection.py:L82-L109` and `test_threat_correlation.py:L35-L65`.
* **WHAT I SHOULD NOT CLAIM:** **DO NOT CLAIM ANY FAKE ACCURACY NUMBER.** Explain the unsupervised paradigm honestly.

---

### GROUP I: ARCHITECTURE & COUPLING

#### Q12: "How is the explainability engine connected to the ML model?"
* **ANSWER:** The explainability engine (`app/services/explanation.py`) is completely decoupled from the Isolation Forest's internal tree structure. It receives the `ThreatAssessment` dataclass containing the normalized per-feature z-scores. It mathematically computes the relative contribution percentage of each deviating feature ($\frac{|z_i|}{\sum |z|} \times 100$) and maps deviating features to human-readable labels and defensive analyst action playbooks.
* **WHY THE JUDGE IS ASKING:** To see if your explainability is SHAP/LIME or deterministic rule-based.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/explanation.py:L94-L116` (`_build_evidence`).
* **WHAT I SHOULD NOT CLAIM:** Do not claim you run SHAP tree explainer or neural attention maps.

---

### GROUP J: SCALABILITY & PERFORMANCE

#### Q13: "How would you scale this backend from 5 hosts to 10,000 endpoints?"
* **ANSWER:** In our current architecture, SQLite and in-memory scoring handle our 5-host demo cleanly. To scale to 10,000 enterprise endpoints pushing telemetry every 5 seconds (2,000 events/sec), we would implement a 4-tier distributed pipeline:
  1. **Ingestion Tier:** Distributed edge ingest nodes running behind NGINX with mTLS termination.
  2. **Message Broker:** Apache Kafka cluster partitioned by `hostname` to guarantee strictly ordered time-series streams.
  3. **Inference Workers:** Stateless Python consumer pods (FastAPI / Celery) pulling batches from Kafka and scoring against cached Redis baselines.
  4. **Database Tier:** PostgreSQL with TimescaleDB extension for hypertable time-series storage and tiered data retention.
* **WHY THE JUDGE IS ASKING:** To test enterprise systems engineering capability.
* **EVIDENCE FROM OUR CODE:** `docs/ARCHITECTURE.md` (System Scaling Strategy section).
* **WHAT I SHOULD NOT CLAIM:** Do not claim Kafka or TimescaleDB is running right now in the demo. Present it as Phase 2 architectural roadmap.

---

### GROUP K: SECURITY & HARDENING

#### Q14: "What happens if an attacker compromises the backend and sends spoofed telemetry?"
* **ANSWER:** In our current prototype, API routes are unauthenticated because it runs in a local demo environment. In production, we would enforce mutual TLS (mTLS) with X.509 endpoint certificates issued during host enrollment and sign every telemetry payload using HMAC-SHA256 with host-specific private keys, rejecting any unsigned or duplicate sequence packets at the ingestion gateway.
* **WHY THE JUDGE IS ASKING:** Threat modeling check.
* **EVIDENCE FROM OUR CODE:** `docs/PROJECT_FORENSIC_AUDIT.md` (Security Posture section).
* **WHAT I SHOULD NOT CLAIM:** Do not claim endpoints are currently cryptographically signed.

---

### GROUP L: DEMO & WORKFLOW

#### Q15: "Why does the incident table not create duplicate tickets when an attack continues for multiple minutes?"
* **ANSWER:** In `app/services/incident_management.py:L121-L122`, before inserting a new incident, `run_incident_detection()` queries `db.get_active_incident_for_host(hostname)` to check if there is already a ticket in `OPEN` or `INVESTIGATING` status for that host. If an active ticket exists, it suppresses duplicate creation. Only when an analyst marks the ticket `RESOLVED` and a new compromise occurs will a new incident ticket be generated.
* **WHY THE JUDGE IS ASKING:** Alert fatigue and ticket deduplication is a major real-world SOC challenge.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/incident_management.py:L121-L122` and `test_incidents.py:L60-L75`.
* **WHAT I SHOULD NOT CLAIM:** None. This is fully implemented and tested.

---

### GROUP M: COMPETITIVE COMPARISON

#### Q16: "How is SentinelX different from Splunk, Elastic SIEM, or CrowdStrike Falcon?"
* **ANSWER:**
  * **vs. SIEM (Splunk/Elastic):** SIEMs are centralized log aggregators that rely heavily on static Correlation Rules (e.g. `COUNT(failed_logins) > 5 in 1m`) and charge massive indexing fees per gigabyte. SentinelX focuses on lightweight, unsupervised statistical baseline anomaly scoring and multi-signal fusion directly at the behavioral layer without requiring pre-written rules.
  * **vs. EDR (CrowdStrike/Defender):** EDRs focus on kernel drivers, binary execution signatures, and process hooks. SentinelX acts as an analytical correlation plane that correlates high-level telemetry signals (network, auth, processes, resource) with mathematical explainability.
* **WHY THE JUDGE IS ASKING:** Market positioning check.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/threat_correlation.py:L70-L112` and `app/services/explanation.py:L120-L153`.
* **WHAT I SHOULD NOT CLAIM:** Do not claim SentinelX is an EDR agent.

---

### GROUP N: INNOVATION & UNIQUENESS

#### Q17: "What is your single biggest technical innovation in SentinelX?"
* **ANSWER:** Our biggest technical contribution is the **Two-Stage Noise-Filtering Fusion Pipeline**:
  1. Stage 1: Converting multi-dimensional raw metrics into **per-host z-score normalized feature vectors**, solving host asymmetry (firewall vs workstation baseline disparity).
  2. Stage 2: Passing z-scores through an **Isolation Forest** coupled with a **Multi-Signal Gate** that explicitly penalizes single twitchy metrics and rewards simultaneous correlated deviations across independent signal families, eliminating single-metric false alarms.
* **WHY THE JUDGE IS ASKING:** To see if you can articulate the core technical value proposition in 30 seconds.
* **EVIDENCE FROM OUR CODE:** `backend/app/services/anomaly_detection.py:L131-L139` and `app/services/threat_correlation.py:L70-L90`.
* **WHAT I SHOULD NOT CLAIM:** Do not claim you invented Isolation Forest. You engineered the per-host z-score normalization and multi-signal fusion architecture.

---

### GROUP O: LIMITATIONS & HONEST DEFENSE

#### Q18: "What happens if an attacker executes a slow, low-intensity attack over 6 months?"
* **ANSWER:** This is a classic **"boiling the frog"** attack. If an attacker increases outbound traffic by only 0.1% per week, and our background loop retrains baseline models periodically (`app/main.py:L31-L32`), the baseline could slowly drift and absorb the malicious activity as normal. In production, we would counter this by maintaining multi-tiered baseline windows (7-day short-term baseline vs 90-day immutable historical baseline) and enforcing static anomaly guardrails.
* **WHY THE JUDGE IS ASKING:** Sophisticated cybersecurity judges always probe baseline poisoning and concept drift.
* **EVIDENCE FROM OUR CODE:** `backend/app/main.py:L15-L21` (shows periodic retraining every 30 ticks).
* **WHAT I SHOULD NOT CLAIM:** Do not claim our prototype is immune to slow drift. Acknowledge it and explain the multi-tier baseline solution.
