# SENTINELX — MASTER JUDGE PRESENTATION & LIVE DEMO SCRIPT
> **A Complete Step-by-Step Spoken Walkthrough for Smart India Hackathon (SIH)**  
> *Follow this exact sequence to demonstrate the platform, explain backend & ML mechanics, and defend under technical questioning.*

---

## 📋 PRE-FLIGHT CHECKLIST (Do this 2 minutes before the judges arrive)

1. **Browser Tabs to Have Open:**
   * Tab 1: **`http://localhost:5173`** (Main React SOC Dashboard)
   * Tab 2: **`http://127.0.0.1:8000/docs`** (FastAPI Swagger Interactive Console)
   * Tab 3: **`https://github.com/ishan1223/SentinelX`** (GitHub Repository)
2. **Terminal Window Ready:**
   * Terminal inside `d:\Sentinelx\backend` with Python venv active.

---

## ⏱️ 5-MINUTE PRESENTATION TIME ALLOCATION

| Phase | Time | Focus Area |
| :--- | :--- | :--- |
| **Phase 1** | `0:00 – 0:45` | **The Hook & Core Problem:** Why EDRs and SIEMs fail (Host Asymmetry & Alert Fatigue) |
| **Phase 2** | `0:45 – 1:30` | **The Architecture:** Per-Host Z-Scores + Isolation Forest + Multi-Signal Noise Gate |
| **Phase 3** | `1:30 – 3:30` | **Live Demo Walkthrough:** Real-time attack simulation, ML detection, and incident generation |
| **Phase 4** | `3:30 – 4:30` | **Deep Investigation:** Slide-out drawer, 100% evidence math, and response playbooks |
| **Phase 5** | `4:30 – 5:00` | **Honest Conclusion & Judge Q&A Transition** |

---

## 🎬 STEP-BY-STEP LIVE WALKTHROUGH

---

### 🔹 STEP 1: Setting the Stage (Steady-State Dashboard)
* **What to Show on Screen:** Main Dashboard at `http://localhost:5173` (Overview Mode).
* **Visual State:** 5 Endpoints, Summary Cards show 100% Fleet Health, 0 Active Incidents, Threat Timeline shows uniform blue bars.

```text
[What is happening in the Backend behind the scenes]:
- Async loop (_telemetry_loop in main.py) ticks every 4 seconds.
- Normal telemetry generated via Poisson & Gaussian distributions.
- Z-scores are near 0.0; Isolation Forest anomaly score < 15/100.
```

🗣️ **EXACT WORDS TO SAY:**
> *"Respected judges, this is **SentinelX**, an AI-powered behavioral compromise detection platform. 
>
> In modern enterprise security, Security Operations Centers (SOCs) face two major crises:
> 1. **Host Asymmetry:** A perimeter firewall pushing gigabytes of traffic is completely normal, but the exact same traffic volume on an HR workstation indicates a massive data breach.
> 2. **Alert Fatigue:** Single-metric spikes (like downloading a game or compiling code) trigger thousands of false alarms in legacy SIEMs.
>
> Right now, you are looking at our live fleet of 5 heterogeneous devices—including workstations, perimeter firewalls, and core routers. Our backend is actively polling every device, computing real-time statistical baselines across 9 telemetry signals. Notice that our fleet health is 100%, and our learned anomaly scores are at zero."*

---

### 🔹 STEP 2: Triggering the Controlled Simulated Compromise
* **What to Show on Screen:** Click the **"Simulate Attack"** quick-action button in the Header (or toggle into **Demo Mode**).
* **Target Device:** `HOST-042` (`WIN10-ENG-42`).

```text
[What is happening in the Backend behind the scenes]:
- POST /api/simulation/compromise?hostname=HOST-042 is executed.
- simulation_state table updates compromised = 1.
- telemetry_engine._apply_compromise() stochastically distorts 6 signals:
  * outbound_bytes: multiplied 6–15x + 2,000–8,000 bytes (Data Exfiltration)
  * dns_queries: multiplied 4–9x (C2 Beaconing / Fast Flux)
  * unique_destinations: multiplied 5–12x (Lateral Reconnaissance)
  * new_processes: increased by +4 to +12 (Dropper / Payload Execution)
  * failed_logins: increased by +3 to +10 (Credential Stuffing)
```

🗣️ **EXACT WORDS TO SAY:**
> *"Now, let's simulate an advanced multi-stage cyber attack on `HOST-042`, an engineering workstation.
>
> In the real world, sophisticated malware doesn't just spike one metric. It opens Command-and-Control beaconing over DNS, executes dropper processes, scans unfamiliar destination IPs, and exfiltrates proprietary data.
>
> When I click **'Simulate Attack'**, our backend immediately injects these correlated multi-signal distortions into the live telemetry stream."*

---

### 🔹 STEP 3: Real-Time Detection & Multi-Signal Noise Gate
* **What to Show on Screen:** Watch the dashboard update dynamically (within 1–4 seconds):
  1. `HOST-042` in the Endpoint Table turns **Red ("High Risk")** with risk progress bar jumping to **88%**.
  2. Summary Cards update: **"At Risk" increments to 1**, Fleet Health drops.
  3. Threat Timeline Chart renders a **red anomalous volume bar**.
  4. Risk Distribution Donut Chart renders a **red "Critical" wedge**.

```text
[What is happening in the Backend behind the scenes]:
1. anomaly_detection.py normalizes HOST-042 telemetry against its own learned baseline:
   z = (x - mean) / max(std, floor) -> Outbound z-score jumps to +8.5, DNS to +6.2.
2. Isolation Forest (200 trees) scores the 9D vector -> Calibrated Anomaly Score = 94.0.
3. threat_correlation.py evaluates the Multi-Signal Noise Gate:
   - Significant deviating signals (|z| >= 2.0) = 6.
   - Since count >= 2, Correlation Breadth & Severity Factors are unlocked!
   - Fused Compromise Probability = 0.50*(94) + 0.30*(67) + 0.20*(100) = 87.6%.
   - Severity Tier classified as CRITICAL.
```

🗣️ **EXACT WORDS TO SAY:**
> *"Look at how the platform responds in real time.
>
> Our backend converted `HOST-042`'s telemetry into **per-host z-scores** and passed them to our unsupervised **Isolation Forest model**. The ML model calculated an anomaly score of over 90.
>
> But here is our core innovation: **The Multi-Signal Noise Gate**. 
> If a developer had merely compiled a software build, only CPU and process creation would spike. SentinelX's noise gate would suppress the alert. But because our engine detected **6 simultaneous, correlated deviations across independent domains**—outbound exfiltration, DNS tunneling, and credential attempts—our fusion formula escalated the compromise probability to **88% Critical**."*

---

### 🔹 STEP 4: Automated Incident Generation & Deduplication
* **What to Show on Screen:** Scroll down to the **Recent Incidents** feed.
* **Visual State:** Incident card **`INC-0001`** appears with `CRITICAL` badge, status `OPEN`, and structured summary narrative.

```text
[What is happening in the Backend behind the scenes]:
- incident_management.py detects compromise_probability >= 80.0%.
- get_active_incident_for_host("HOST-042") confirms no existing active ticket.
- Inserts new row into incidents table with serialized JSON evidence and action playbooks.
- Frontend polling hook useDashboardData fetches GET /api/incidents and renders card.
```

🗣️ **EXACT WORDS TO SAY:**
> *"Because the compromise probability crossed our **80% incident threshold**, SentinelX automatically opened an incident ticket—**`INC-0001`**.
>
> Notice that even as the attack continues to run and telemetry streams every 4 seconds, our backend enforces **active incident deduplication**. It does not spam the analyst with 50 duplicate tickets. It maintains one persistent, stateful incident until resolved."*

---

### 🔹 STEP 5: Deep SOC Forensic Investigation & 100% Evidence Math
* **What to Show on Screen:** Click on the `HOST-042` row in the Endpoint Table.
* **Visual State:** The **Investigation Drawer** slides out from the right side of the screen, displaying:
  * Anomaly Score & Compromise Probability KPI tiles.
  * **Observed Value vs Baseline Deviation Bar Chart**.
  * **Signal Contribution Breakdown (%)**.
  * **Recommended Action Playbooks**.

```text
[What is happening in the Backend behind the scenes]:
- useInvestigation hook fetches GET /api/endpoints/HOST-042/explanation.
- explanation.py computes exact relative contribution shares:
  Contribution_i = (|z_i| / sum(|z|)) * 100%.
- Generates tailored, non-destructive defensive playbooks based on anomalous signal types.
```

🗣️ **EXACT WORDS TO SAY:**
> *"Now, let's step into the shoes of a Tier-1 SOC analyst. When I click on `HOST-042`, our slide-out **Investigation Drawer** opens.
>
> Unlike generative LLMs that hallucinate or deep neural networks that act as unexplainable black boxes, SentinelX provides **deterministic, mathematically provable explainability**:
> 1. **Baseline Comparison:** The bar chart compares the live observed metrics directly against `HOST-042`'s historical learned baseline range.
> 2. **Contribution Breakdown:** It mathematically breaks down the finding—outbound traffic represents 32% of the anomaly, destination diversity represents 24%, DNS beaconing represents 18%, and process creation represents 15%. These contribution shares mathematically sum to **exactly 100%**.
> 3. **Action Playbooks:** It equips the analyst with non-destructive, actionable response steps: isolating the endpoint, inspecting outbound TCP sessions, and preserving volatile memory for forensics."*

---

### 🔹 STEP 6: Incident Remediation & Fleet Reset
* **What to Show on Screen:** 
  1. In the Incident card or drawer, click status **"Investigating"**, then click **"Resolved"**.
  2. Click **"Reset Fleet"** in the top navigation bar.
* **Visual State:** Ticket marks `RESOLVED`, `HOST-042` risk bar drops back to 0%, Summary Cards return to 100% Healthy.

```text
[What is happening in the Backend behind the scenes]:
- PATCH /api/incidents/INC-0001 updates status to RESOLVED and updates updated_at.
- POST /api/simulation/reset sets compromised = 0 in SQLite.
- Immediate normal telemetry sample generated; background loop returns to baseline.
```

🗣️ **EXACT WORDS TO SAY:**
> *"The analyst can update the ticket lifecycle from `OPEN` to `INVESTIGATING` to `RESOLVED`.
>
> When the threat is neutralized and we click **'Reset Fleet'**, our backend resets the simulation state, resumes normal baseline generation, and the dashboard returns to 100% fleet health.
>
> If `HOST-042` is attacked again in the future, our state machine recognizes the resolution and will cleanly generate `INC-0002`."*

---

## 🎯 STEP 7: CLOSING SUMMARY (30 Seconds)

🗣️ **EXACT WORDS TO SAY:**
> *"To summarize:
> * **Backend & ML:** Python 3.12, FastAPI, SQLite, and Scikit-Learn Isolation Forest running inference in under 1.2 milliseconds.
> * **Innovation:** Solving host asymmetry with per-host z-scores, eliminating false positives via our multi-signal noise gate, and providing 100% auditable explainability.
> * **Validation:** All 53 automated unit and integration tests are passing.
>
> Thank you, judges. We are ready for your technical questions, and we invite you to inspect any part of our backend codebase, ML pipeline, or database."*

---

## 🛡️ EMERGENCY "SHOW ME THE CODE" CHEAT SHEET

If the judges interrupt and say: *"Show me the code for that!"*

| If Judge Asks | Open This File | Navigate To |
| :--- | :--- | :--- |
| **"Show me per-host z-scores"** | `backend/app/services/anomaly_detection.py` | Line 131 (`_zscore_vector`) |
| **"Show me the noise gate"** | `backend/app/services/threat_correlation.py` | Line 76 (`if correlated_signal_count >= 2:`) |
| **"Show me the risk formula"** | `backend/app/services/threat_correlation.py` | Line 84 (`compromise_probability = ...`) |
| **"Show me evidence math summing to 100%"** | `backend/app/services/explanation.py` | Line 94 (`_build_evidence`) |
| **"Show me incident deduplication"** | `backend/app/services/incident_management.py` | Line 121 (`get_active_incident_for_host`) |
| **"Show me all 53 passing tests"** | Terminal | Run `.\.venv\Scripts\python -m pytest -q` |
| **"Show me live SQLite tables"** | Terminal | Run `sqlite3 sentinelx.db "SELECT * FROM incidents;"` |
