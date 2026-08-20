# SENTINELX — HOSTILE JUDGE SIMULATION (20 ATTACK SCENARIOS)
**Persona:** Cynical, Veteran Cybersecurity Systems Architect & Hackathon Judge  
**Objective:** Prepare the backend engineer for aggressive, adversarial probing  

---

### ATTACK 1: "Your system is just a pretty frontend dashboard with hardcoded JSON. Prove to me there is a real backend."
* **Judge's Attack:** "I've seen 50 student projects today that just mock API responses in React. Show me the running process and the actual code generating numbers."
* **Best Response:** "Our frontend does not generate any mock data. Our backend is a live FastAPI service running on port 8000 with a SQLite persistence engine. Every 4 seconds, an async background task generates telemetry, writes to SQLite, executes Isolation Forest inference in Python, and updates the database. The frontend polls `/api/endpoints`, `/api/telemetry`, and `/api/incidents`. I can show you the live database and terminal logs right now."
* **Evidence from Code:** `backend/app/main.py:L23-L34` (`_telemetry_loop`), `backend/app/db/database.py:L135-L150`.
* **Mistake to Avoid:** Don't get defensive; offer to inspect SQLite directly with `sqlite3 sentinelx.db "SELECT * FROM telemetry LIMIT 5;"`.

---

### ATTACK 2: "Where is your confusion matrix and F1-score? Without a confusion matrix, your AI is worthless."
* **Judge's Attack:** "Every ML project needs a confusion matrix. What is your Precision and Recall on the test set?"
* **Best Response:** "In real-world cybersecurity, production networks do not have pre-labeled ground truth for zero-day attacks. That is why SentinelX uses an **unsupervised Isolation Forest**. Unsupervised models do not optimize a binary cross-entropy classification loss, so a static supervised confusion matrix is mathematically inappropriate. Instead, we evaluate our system by verifying baseline isolation and mathematical stability across our 53 automated test suites."
* **Evidence from Code:** `backend/app/services/anomaly_detection.py:L67-L71`, `docs/ML_FORENSIC_AUDIT.md`.
* **Mistake to Avoid:** Never invent a fake confusion matrix (e.g. "98% accuracy"). Acknowledge the unsupervised paradigm proudly.

---

### ATTACK 3: "Your simulation isn't a real attack. Isn't this entire demo fabricated?"
* **Judge's Attack:** "You just click a button that multiplies numbers. How does this prove you can detect real malware?"
* **Best Response:** "The simulation is a controlled test harness that injects statistical distortions matching the exact multi-vector footprint of post-compromise malware—specifically C2 beaconing via DNS, data exfiltration via outbound byte spikes, and credential attacks via failed logins. The detection engine does not know the host is compromised; it discovers the deviation purely through unsupervised z-score outlier analysis and multi-signal correlation."
* **Evidence from Code:** `backend/app/services/telemetry_engine.py:L104-L143` (`_apply_compromise`), `app/services/threat_correlation.py:L70-L112`.
* **Mistake to Avoid:** Don't claim you executed a real Cobalt Strike beacon. Be clear that it's a controlled stochastic simulation harness.

---

### ATTACK 4: "Why shouldn't I just use Splunk correlation searches?"
* **Judge's Attack:** "I can write a Splunk query in 2 minutes: `index=network outbound_bytes > 5000 | stats count`. Why do I need your platform?"
* **Best Response:** "A static rule like `outbound_bytes > 5000` will fail in two ways: it will trigger hundreds of false alarms on high-traffic servers (like firewalls) while completely missing a 3,000-byte credential dump on a quiet workstation. SentinelX learns individual per-host baselines dynamically and requires multi-signal correlation across independent domains, eliminating manual threshold tuning."
* **Evidence from Code:** `backend/app/services/anomaly_detection.py:L93-L97` (`_host_baselines`), `app/services/threat_correlation.py:L76-L83`.
* **Mistake to Avoid:** Don't say Splunk is bad; explain why static thresholds suffer from false alarms and role asymmetry.

---

### ATTACK 5: "How does this scale to 50,000 enterprise machines? SQLite will lock up immediately."
* **Judge's Attack:** "SQLite is a toy file database. Your backend will collapse under real enterprise workloads."
* **Best Response:** "You are completely right about SQLite's write-lock limitation for enterprise production. For this hackathon prototype, SQLite provided zero-dependency simplicity. In our production architecture, we decouple ingestion using Apache Kafka message brokers, cache per-host baselines in Redis, and persist telemetry into TimescaleDB time-series hypertables."
* **Evidence from Code:** `docs/PROJECT_FORENSIC_AUDIT.md: Section 5` (Distributed Scaling Strategy).
* **Mistake to Avoid:** Don't argue that SQLite can handle 50,000 endpoints. Agree and present the distributed architecture cleanly.

---

### ATTACK 6: "What happens when a legitimate developer compiles code and spawns 50 processes? Your system will scream CRITICAL."
* **Judge's Attack:** "A developer runs a build script. Process creation surges. Do you wake up the SOC analyst at 3 AM?"
* **Best Response:** "No, because of our **Multi-Signal Noise Gate**. A compilation spike only affects `new_processes` and `cpu_usage`. The remaining signals (outbound traffic, DNS, failed logins, destination diversity) remain normal. Because the significant count is under our multi-domain threshold, correlation breadth is clamped to 0.0, keeping compromise probability in the Low/Medium tier and preventing incident ticket generation."
* **Evidence from Code:** `backend/app/services/threat_correlation.py:L76-L83` (`MIN_CORRELATED_SIGNALS_FOR_BOOST = 2`).
* **Mistake to Avoid:** Don't say "our AI is smart enough to know it's a compiler." Explain the exact mathematical noise gate.

---

### ATTACK 7: "If an attacker exfiltrates data slowly over 6 months, won't your retraining loop absorb the attack as normal behavior?"
* **Judge's Attack:** "You retrain your model every 2 minutes. An attacker can slowly ramp up traffic and poison your baseline."
* **Best Response:** "That is a valid vulnerability known as baseline poisoning or concept drift. In our current prototype, we retrain periodically on confirmed normal data. In an enterprise deployment, we solve this by implementing dual-window baselines: a 7-day rolling window for seasonal variation combined with an immutable 90-day historical baseline and hard static anomaly ceilings."
* **Evidence from Code:** `backend/app/main.py:L15-L21` (`RETRAIN_EVERY_N_TICKS = 30`).
* **Mistake to Avoid:** Don't deny that baseline poisoning is possible. Acknowledge it and explain the multi-window defense.

---

### ATTACK 8: "Why did you use Python for a security backend? Isn't Python too slow for high-throughput networking?"
* **Judge's Attack:** "C++ and Go are standard for cybersecurity backends. Why Python?"
* **Best Response:** "Python was selected because it is the native language of scientific computing, NumPy, and Scikit-Learn, allowing zero-overhead integration between our analytical algorithms and our REST API. For raw network packet capture, agents are written in C or Rust with eBPF; but for the higher-level analytical correlation plane, FastAPI's asynchronous event loop and C-optimized NumPy vectors deliver sub-2ms response times."
* **Evidence from Code:** `backend/app/services/anomaly_detection.py:L100` (NumPy vector operations).
* **Mistake to Avoid:** Don't claim Python is faster than C++. Clarify that it's the analytical plane, not the packet-capture driver.

---

### ATTACK 9: "Your risk score formula uses arbitrary weights (50%, 30%, 20%). Where did those numbers come from?"
* **Judge's Attack:** "Did you just make up 0.5, 0.3, 0.2? What is the mathematical justification?"
* **Best Response:** "The weights reflect domain-driven heuristic prioritization:
  1. 50% ML Anomaly Score: Captures multi-dimensional geometric distance in the 9D feature space.
  2. 30% Correlation Breadth: Explicitly credits simultaneous deviations across independent tactical domains.
  3. 20% Severity Factor: Measures extreme outlier magnitude ($|z| / 6.0$).
  In future work, these weights can be optimized via logistic regression against historical SOC incident feedback."
* **Evidence from Code:** `backend/app/services/threat_correlation.py:L28-L30`.
* **Mistake to Avoid:** Don't claim the weights were derived from deep reinforcement learning. State the engineering rationale clearly.

---

### ATTACK 10: "What happens if an endpoint stops sending telemetry? Do you just assume it's safe?"
* **Judge's Attack:** "An attacker kills your agent. Your dashboard shows 0 risk because there's no anomalous data."
* **Best Response:** "The database tracks `last_seen` timestamps on the `endpoints` table. If telemetry stops arriving, the host is not scored as 0 risk; in our health watchdog architecture, any host failing to check in for 30 seconds transitions to an `UNRESPONSIVE` state, alerting the SOC that telemetry collection has been interrupted."
* **Evidence from Code:** `backend/app/db/database.py:L26, L128-L133`.
* **Mistake to Avoid:** Don't say "the ML handles offline hosts." ML handles telemetry; the watchdog handles heartbeat liveness.

---

### ATTACK 11: "Explain your zero-division protection in feature baseline calculations."
* **Judge's Attack:** "What happens if a workstation has 0 failed logins and 0 standard deviation for a week? Your z-score crashes on division by zero."
* **Best Response:** "We enforce a dynamic standard deviation floor in `_compute_baseline()`: `floor = max(0.5, 0.02 * abs(mean))`. The standard deviation is clamped to `max(std, floor)`. This guarantees the denominator is never zero, preventing runtime crashes and preventing minor fluctuations from creating infinite z-scores."
* **Evidence from Code:** `backend/app/services/anomaly_detection.py:L124-L125`, `backend/tests/test_anomaly_detection.py:L60-L80`.
* **Mistake to Avoid:** None. This is mathematically implemented and verified in tests.

---

### ATTACK 12: "Your explainability is just hardcoded string templates. How is that AI explainability?"
* **Judge's Attack:** "You just print pre-written sentences. That's not real explainability."
* **Best Response:** "Real-world cybersecurity analysts reject non-deterministic LLM explanations because they hallucinate false technical assertions. Our explainability is mathematically deterministic: it calculates the exact relative contribution percentage of each feature based on its z-score deviation, ranks them, and maps them to proven defensive response playbooks. It is transparent, verifiable, and legally auditable."
* **Evidence from Code:** `backend/app/services/explanation.py:L94-L153`.
* **Mistake to Avoid:** Don't apologize for not using a generative LLM. Explain why deterministic explainability is required in regulated SOC environments.

---

### ATTACK 13: "How do you protect your own API from being flooded by a DDoS attack?"
* **Judge's Attack:** "Your endpoints are completely open without rate limiting."
* **Best Response:** "In this local hackathon prototype, authentication and rate limiting are omitted to allow seamless local demonstration. For production deployment, we place the API behind an NGINX reverse proxy configured with `limit_req_zone` for token-bucket rate limiting and require OAuth2 JWT tokens on all routes."
* **Evidence from Code:** `docs/PROJECT_FORENSIC_AUDIT.md: Section 5`.
* **Mistake to Avoid:** Don't claim you have rate limiting implemented right now.

---

### ATTACK 14: "Why is your Isolation Forest set to 200 estimators? Why not 50 or 500?"
* **Judge's Attack:** "Is 200 trees just a random guess?"
* **Best Response:** "In empirical benchmarks on 9-dimensional tabular data, 100 trees can exhibit slight boundary variance between successive fits, while 500 trees increase inference latency without measurable reduction in average path length variance. 200 estimators provides the optimal trade-off: stable score calibration with under 1.2ms execution time per sample."
* **Evidence from Code:** `backend/app/services/anomaly_detection.py:L66-L71`.
* **Mistake to Avoid:** Don't say "200 is default." (Scikit-Learn default is 100). State that you deliberately chose 200 for path stability.

---

### ATTACK 15: "What happens if an incident is resolved, but the host gets attacked again 10 minutes later?"
* **Judge's Attack:** "Does your deduplication block future alerts on the same host forever?"
* **Best Response:** "No. Deduplication only checks for active tickets in `OPEN` or `INVESTIGATING` status. Once an analyst updates the ticket to `RESOLVED`, the active incident filter returns `None`. If the host is compromised again and crosses the 80% threshold, a brand new incident ticket (e.g. `INC-0002`) is automatically created."
* **Evidence from Code:** `backend/app/services/incident_management.py:L121-L122`, `backend/tests/test_incidents.py:L100-L120`.
* **Mistake to Avoid:** None. This behavior is explicitly implemented and verified by unit tests.

---

### ATTACK 16: "Show me how you handle CORS security."
* **Judge's Attack:** "Is your CORS wildcard `allow_origins=['*']`?"
* **Best Response:** "No. In `backend/app/core/config.py:L7-L10`, CORS origins are strictly whitelisted to our frontend dev servers (`http://localhost:5173` and `http://127.0.0.1:5173`), preventing unauthorized cross-origin browser requests."
* **Evidence from Code:** `backend/app/core/config.py:L7-L10`, `backend/app/main.py:L53-L59`.
* **Mistake to Avoid:** None. Strict CORS is verified.

---

### ATTACK 17: "How do you test your backend?"
* **Judge's Attack:** "Did you write any automated tests, or did you just test by clicking the UI?"
* **Best Response:** "We have a comprehensive test suite of 53 automated unit and integration tests using `pytest` and `httpx`. We test everything from telemetry Poisson bounds and Isolation Forest fitting to threat correlation noise filtering, zero-division safety, incident state machines, and full API endpoint contracts."
* **Evidence from Code:** `backend/tests/` (10 test files, 53 passing tests).
* **Mistake to Avoid:** Offer to run `pytest -q` in the terminal to demonstrate all 53 passing tests in under 6 seconds.

---

### ATTACK 18: "Can an attacker evade detection by keeping all deviations at z = 1.9?"
* **Judge's Attack:** "Your significance threshold is z = 2.0. If an attacker stays at z = 1.9, do they bypass you completely?"
* **Best Response:** "While correlation breadth requires $|z| \ge 2.0$, the underlying Isolation Forest scores the full 9-dimensional vector simultaneously. Simultaneous deviations of 1.9 across 6 features will still elevate the raw Isolation Forest score to ~60-70. In production, we combine soft fuzzy significance weighting with static thresholds to close boundary edge cases."
* **Evidence from Code:** `backend/app/services/threat_correlation.py:L13, L84-L88`.
* **Mistake to Avoid:** Don't say "1.9 is impossible." Explain the dual scoring mechanism (ML distance + heuristic gate).

---

### ATTACK 19: "Why should an enterprise pay for SentinelX when they already have Microsoft Defender for Endpoint?"
* **Judge's Attack:** "Defender is built into Windows. Why does anyone need your software?"
* **Best Response:** "Defender is an endpoint agent focusing on file scanning, AMSI script inspection, and Windows-specific kernel telemetry. SentinelX is a heterogeneous, fleet-wide behavioral analytics layer that unifies network devices (firewalls, routers) and Linux/Windows systems into a single correlation plane with mathematically transparent evidence breakdowns."
* **Evidence from Code:** `backend/app/db/database.py:L73-L79` (seed endpoints covering systems, firewalls, and routers).
* **Mistake to Avoid:** Don't attack Defender; position SentinelX as the cross-platform analytical intelligence layer.

---

### ATTACK 20: "If you had 1 more month before SIH finals, what is the single most important component you would build?"
* **Judge's Attack:** "Where is this project going next?"
* **Best Response:** "The single highest-impact component would be developing a **lightweight eBPF kernel collector in Rust** to stream live socket connections and process events directly from Linux/Windows kernels into our FastAPI ingestion pipeline, replacing our synthetic generator with real production network telemetry."
* **Evidence from Code:** `docs/PROJECT_FORENSIC_AUDIT.md: Section 1`.
* **Mistake to Avoid:** Don't give a vague answer like "more AI." Give a precise engineering milestone (eBPF kernel probe in Rust).
