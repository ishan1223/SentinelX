# SENTINELX — BACKEND ENGINEER PRESENTATION SCRIPT
**Spoken Duration:** 75–90 Seconds  
**Tone:** Technical, Crisp, Honest, Student Engineer Persona  

---

### [0:00 – 0:15] INTRODUCTION & ROLE
"Hi judges, I am the backend engineer for SentinelX. I built our asynchronous ingestion pipeline, our SQLite persistence layer, our per-host normalization engine, and the REST APIs connecting our machine learning pipeline to the frontend SOC dashboard."

---

### [0:15 – 0:35] BACKEND ARCHITECTURE & TELEMETRY FLOW
"Our backend is built on **FastAPI and Python 3.12**. In the background, an asynchronous telemetry loop continuously streams 9-dimensional behavioral metrics across our fleet. 

In enterprise environments, a firewall pushing gigabytes of traffic is normal, while the exact same traffic on a workstation is a critical breach. To solve this host asymmetry, our backend normalizes raw telemetry into **per-host z-scores** with dynamic variance floors before passing it to our machine learning model."

---

### [0:35 – 0:55] ML INTEGRATION & CORRELATION FUSION
"For detection, we use an unsupervised **Isolation Forest with 200 trees**. Rather than alerting on single noisy spikes, our threat correlation engine enforces a **multi-signal noise gate**—it requires simultaneous statistical deviations across independent signal families, like DNS queries, outbound bytes, and process creation, before elevating risk. 

When compromise probability crosses 80%, our backend automatically opens deduplicated incident tickets with deterministic percentage evidence breakdowns and actionable response playbooks."

---

### [0:55 – 1:15] LIVE DEMO & REST APIS
"During our live demo, clicking 'Simulate Attack' hits our `POST /api/simulation/compromise` endpoint. The backend skews 6 telemetry signals in real time, scores the anomaly in under 2 milliseconds, updates SQLite, and surfaces the live incident on the dashboard via our 11 REST API endpoints."

---

### [1:15 – 1:30] HONEST LIMITATION & FUTURE WORK
"Our prototype currently operates on synthetic telemetry rather than live kernel drivers. Our immediate next milestone is writing a lightweight **Rust eBPF kernel agent** to stream live socket and process events directly into our ingestion pipeline. 

All 53 unit and integration tests are passing, and I am ready to dive into the code and database with you."
