# SENTINELX — PROJECT FORENSIC AUDIT
**Inspection Timestamp:** 2026-08-20  
**Target Repository:** `SentinelX`  
**Role:** Backend Engineering Forensic Audit & SIH Technical Defense Preparation  

---

## 1. Executive Summary & Forensic Truth Matrix

| Dimension | Forensic Reality in Repository | Audit Classification |
| :--- | :--- | :--- |
| **Frontend** | React 19.0.0, Vite 6.0.5, TypeScript 5.6.2, Tailwind CSS 4.0.0, Recharts 2.15.0, Axios 1.7.9 | **IMPLEMENTED** |
| **Backend** | Python 3.12, FastAPI 0.115.6, Uvicorn 0.34.0, Pydantic 2.10.4, Scikit-Learn 1.6.0, NumPy 2.2.0 | **IMPLEMENTED** |
| **Database** | SQLite 3 (Raw `sqlite3` driver with parameterized queries, no ORM), path `backend/sentinelx.db` | **IMPLEMENTED** |
| **Machine Learning** | Unsupervised `IsolationForest` (200 trees) fitted on per-host z-score normalized vectors (9 features) | **IMPLEMENTED** |
| **Telemetry Generation** | Synthetic telemetry generator (Poisson + Gaussian + Bounded random walk) ticking every 4 seconds | **SIMULATED / CONTROLLED FOR DEMONSTRATION** |
| **Real Network Ingestion**| eBPF, PCAP, Sysmon, Windows Event Log, NetFlow, Zeek/Suricata ingestion pipelines | **NOT IMPLEMENTED IN CURRENT PROJECT** |
| **Authentication / IAM** | JWT, OAuth2, API Keys, RBAC, User login tables | **NOT IMPLEMENTED IN CURRENT PROJECT** |
| **Asynchronous Broker** | Kafka, RabbitMQ, Redis Streams, Celery workers | **NOT IMPLEMENTED IN CURRENT PROJECT** |
| **Test Suite** | 53 unit and integration tests using `pytest 8.3.4` and `httpx 0.28.1` (100% passing) | **IMPLEMENTED** |

---

## 2. Complete Repository File Structure

```text
d:\Sentinelx\
│
├── .gitignore                          <- Configured to ignore DB, venv, caches, and local presentation guides
├── README.md                           <- Project overview, quickstart, architecture summary
│
├── backend\
│   ├── sentinelx.db                    <- Local SQLite database instance (auto-created on startup)
│   ├── requirements.txt                <- Core runtime dependencies (fastapi, uvicorn, scikit-learn, numpy, pydantic)
│   ├── requirements-dev.txt            <- Development dependencies (pytest, pytest-asyncio, httpx)
│   │
│   ├── app\
│   │   ├── __init__.py
│   │   ├── main.py                     <- FastAPI app entrypoint, CORS setup, lifespan startup & background loop
│   │   │
│   │   ├── core\
│   │   │   ├── __init__.py
│   │   │   └── config.py               <- App constants, CORS origins, synthetic data notice
│   │   │
│   │   ├── db\
│   │   │   ├── __init__.py
│   │   │   └── database.py             <- SQLite schema (4 tables), connection manager, seed fleet, raw SQL helpers
│   │   │
│   │   ├── services\
│   │   │   ├── __init__.py
│   │   │   ├── telemetry_engine.py     <- Host profiles, random walk load, compromise skew, background tick
│   │   │   ├── anomaly_detection.py    <- IsolationForest service, per-host z-scores, std floors, calibration
│   │   │   ├── threat_correlation.py   <- Heuristic fusion (ML score + breadth + severity), noise filtering gate
│   │   │   ├── explanation.py          <- Evidence items, delta %, contribution share %, action playbooks
│   │   │   └── incident_management.py  <- Incident lifecycle (OPEN->INVESTIGATING->RESOLVED), deduplication guard
│   │   │
│   │   └── api\
│   │       ├── __init__.py
│   │       ├── schemas.py              <- Pydantic request and response models
│   │       ├── health.py               <- GET /api/health
│   │       ├── endpoints.py            <- GET /api/endpoints, GET /api/endpoints/{hostname}
│   │       ├── telemetry.py            <- GET /api/telemetry/{hostname}
│   │       ├── risk.py                 <- GET /api/endpoints/{hostname}/risk
│   │       ├── explanation.py          <- GET /api/endpoints/{hostname}/explanation
│   │       ├── incidents.py            <- GET /api/incidents, GET /api/incidents/{id}, PATCH /api/incidents/{id}
│   │       └── simulation.py           <- POST /api/simulation/compromise, POST /api/simulation/reset
│   │
│   └── tests\
│       ├── __init__.py
│       ├── conftest.py                 <- Temp DB fixtures, test app client setup
│       ├── test_telemetry_engine.py    <- Baseline ranges, Poisson rates, compromise skew tests
│       ├── test_anomaly_detection.py   <- IsolationForest training, z-scores, std floors, score calibration
│       ├── test_threat_correlation.py  <- Noise filter gate (|z|>=2.0, count>=2), probability weighting
│       ├── test_explanation.py         <- Summary builder, evidence contribution sums to 100%, zero division guard
│       ├── test_incidents.py           <- Incident lifecycle, status patch, deduplication guard, reopening
│       ├── test_api.py                 <- Full REST endpoint contract tests
│       ├── test_risk.py                <- /risk route contracts and 404/503 error handling
│       └── test_explanation_api.py     <- /explanation route integration tests
│
├── frontend\
│   ├── index.html                      <- HTML5 shell with Google Font Inter
│   ├── package.json                    <- Dependencies: react 19, vite 6, tailwindcss 4, recharts 2, lucide-react
│   ├── package-lock.json
│   ├── tsconfig.json                   <- TypeScript project references
│   ├── tsconfig.app.json               <- Strict TypeScript compiler configuration
│   ├── tsconfig.node.json
│   ├── vite.config.ts                  <- Vite bundling configuration with React plugin
│   ├── .oxlintrc.json                  <- Oxlint React & TypeScript linting rules
│   │
│   ├── public\
│   │   ├── favicon.svg                 <- SVG Shield Icon
│   │   └── icons.svg                   <- SVG vector sprite sheet
│   │
│   └── src\
│       ├── main.tsx                    <- React DOM root mounting
│       ├── App.tsx                     <- SOC Dashboard layout, active drawer state, live polling coordination
│       ├── index.css                   <- Tailwind CSS dark theme tokens, scrollbars, micro-animations
│       │
│       ├── lib\
│       │   ├── api.ts                  <- Axios HTTP client, API method wrappers, TypeScript interfaces
│       │   ├── format.ts               <- Byte formatting, relative timestamps, absolute dates
│       │   └── severity.ts             <- Severity color mapping, badges, and status tier classifications
│       │
│       ├── hooks\
│       │   ├── useDashboardData.ts     <- 7s polling interval, fleet risk aggregation via Promise.allSettled
│       │   ├── useTelemetryTimeline.ts <- 1-minute time bucket aggregation for Recharts timeline
│       │   ├── useInvestigation.ts     <- On-demand host investigation drawer data fetcher
│       │   └── useDemoSequence.ts      <- Guided 6-stage automated demonstration orchestrator
│       │
│       └── components\
│           ├── Header.tsx              <- SOC banner, live polling heartbeat pulse, simulation triggers
│           ├── SummaryCards.tsx        <- Fleet KPI metrics (Fleet Size, Healthy, At Risk, Active Incidents)
│           ├── EndpointTable.tsx       <- Interactive fleet inventory, role badges, risk progress bars
│           ├── RecentIncidents.tsx     <- Live incident feed, status transition buttons, severity tags
│           ├── ThreatTimelineChart.tsx <- Recharts BarChart (normal vs anomalous event volume)
│           ├── RiskDistributionChart.tsx <- Recharts Donut PieChart (Low, Medium, High, Critical)
│           ├── InvestigationPanel.tsx  <- Slide-out drawer with baseline deviation charts and action playbooks
│           ├── DemoMode.tsx            <- 6-stage interactive walkthrough console with live narrative logs
│           ├── Panel.tsx               <- Reusable glassmorphic UI container
│           ├── SeverityBadge.tsx       <- Color-coded severity badge
│           ├── StatusLegend.tsx        <- SOC status legend indicators
│           ├── StateNotice.tsx         <- Loading spinners and error alerts
│           └── ValueProps.tsx          <- 3 architectural differentiator banners
│
└── docs\
    ├── ARCHITECTURE.md                 <- High-level system architecture specification
    ├── PRESENTATION.md                 <- 5-minute timed presentation script
    └── PRESENTATION_MASTER_GUIDE.md    <- Master file-by-file breakdown and Judge Q&A guide (local only)
```

---

## 3. Verified Dependencies & Runtimes

### Backend Runtime (`backend/requirements.txt` & `backend/requirements-dev.txt`)
```text
fastapi>=0.115.0        (Verified in environment: 0.115.6)
uvicorn[standard]>=0.32.0 (Verified in environment: 0.34.0)
scikit-learn>=1.5.0     (Verified in environment: 1.6.0)
numpy>=1.26.0           (Verified in environment: 2.2.0)
pydantic>=2.9.0         (Verified in environment: 2.10.4)
pytest>=8.0.0           (Verified in environment: 8.3.4)
pytest-asyncio>=0.23.0  (Verified in environment: 0.25.0)
httpx>=0.27.0           (Verified in environment: 0.28.1)
```

### Frontend Runtime (`frontend/package.json`)
```json
{
  "dependencies": {
    "axios": "^1.7.9",
    "clsx": "^2.1.1",
    "lucide-react": "^1.16.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "recharts": "^2.15.0",
    "tailwind-merge": "^3.0.1"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "oxlint": "^0.15.0",
    "tailwindcss": "^4.0.0",
    "typescript": "~5.6.2",
    "vite": "^6.0.5"
  }
}
```

---

## 4. Architectural Data Flow & Component Linkage

```text
[telemetry_engine.py] (Host Profiles + Random Walk Load + Compromise Skew)
        │
        ▼ (tick every 4s)
[SQLite DB: telemetry table]
        │
        ├─────────────────────────────────────────┐
        ▼ (Initial 60 samples/host)               ▼ (Latest 1 sample/host)
[anomaly_detection.py]                     [anomaly_detection.py: score()]
 (Computes per-host baseline mean/std)            │
 (Fits IsolationForest on Z-Scores)               ▼ (Normalized Z-Vector)
        │                                  [IsolationForest Model Inference]
        │                                         │
        ▼                                         ▼ (0-100 Anomaly Score + Deviations)
[threat_correlation.py: assess()] ◄───────────────┘
 (Heuristic Fusion: 50% ML Score + 30% Breadth + 20% Severity)
 (Noise Filter Gate: requires |z| >= 2.0 and count >= 2)
        │
        ├───► [explanation.py: explain()] ──► Evidence items + Playbooks
        │
        ▼ (if compromise_probability >= 80.0 AND no active incident)
[incident_management.py: run_incident_detection()]
        │
        ▼ (Insert into SQLite: incidents table)
[FastAPI REST API: 11 Endpoints in app/api/]
        │
        ▲ (HTTP REST / JSON Polling every 7s)
[Axios Client: frontend/src/lib/api.ts]
        │
        ├──► [useDashboardData.ts] ────────► SummaryCards, EndpointTable, Charts
        ├──► [useInvestigation.ts] ──────► Slide-out InvestigationPanel Drawer
        └──► [useDemoSequence.ts]  ──────► 6-Stage DemoMode Orchestrator
```

---

## 5. Answers to the 20 Core Architectural Questions

1. **What is the frontend?**  
   A Single-Page Application (SPA) built in React 19, TypeScript 5.6, Vite 6, Tailwind CSS 4, and Recharts.
2. **What is the backend?**  
   An asynchronous Python REST API service built with FastAPI and Uvicorn.
3. **What language is the backend written in?**  
   Python 3.12 (using type hints and dataclasses).
4. **What framework?**  
   FastAPI 0.115.6.
5. **What database?**  
   SQLite 3 accessed via Python's standard `sqlite3` library (file path `backend/sentinelx.db`).
6. **What ML framework?**  
   `scikit-learn` 1.6.0 and `numpy` 2.2.0.
7. **What ML models?**  
   Unsupervised `IsolationForest` (`n_estimators=200`, `max_samples='auto'`, `random_state=42`).
8. **Where are models loaded?**  
   Instantiated in memory as a module singleton in `backend/app/services/anomaly_detection.py` (`anomaly_service = AnomalyDetectionService()`).
9. **Where does inference happen?**  
   Synchronously in memory inside `AnomalyDetectionService.score()` in `backend/app/services/anomaly_detection.py:L142-L174`.
10. **How does frontend communicate with backend?**  
    Via HTTP REST calls (JSON payloads) over Axios (`frontend/src/lib/api.ts`) polling `http://localhost:8000/api` every 7 seconds.
11. **What APIs exist?**  
    11 REST endpoints across 7 routers: `/api/health`, `/api/endpoints`, `/api/endpoints/{hostname}`, `/api/telemetry/{hostname}`, `/api/endpoints/{hostname}/risk`, `/api/endpoints/{hostname}/explanation`, `/api/incidents` (GET), `/api/incidents/{id}` (GET), `/api/incidents/{id}` (PATCH), `/api/simulation/compromise` (POST), `/api/simulation/reset` (POST).
12. **Where does telemetry come from?**  
    Synthetically generated in `backend/app/services/telemetry_engine.py` using per-host profile baselines, Gaussian noise, and Poisson distributions.
13. **Where is telemetry processed?**  
    In `backend/app/services/telemetry_engine.py` (generation) and `backend/app/db/database.py` (persistence in `telemetry` table).
14. **Where is feature engineering performed?**  
    In `backend/app/services/anomaly_detection.py` inside `_zscore_vector()` (`z = (x - mean) / std`, clipped to `[-10, 10]`).
15. **Where does anomaly detection happen?**  
    In `backend/app/services/anomaly_detection.py` inside `AnomalyDetectionService.score()`.
16. **Where is risk calculated?**  
    In `backend/app/services/threat_correlation.py` inside `assess()`.
17. **Where are incidents created?**  
    In `backend/app/services/incident_management.py` inside `run_incident_detection()`.
18. **Where is explanation generated?**  
    In `backend/app/services/explanation.py` inside `explain()`.
19. **Where are results stored?**  
    In SQLite tables `telemetry`, `incidents`, `endpoints`, and `simulation_state` in `backend/sentinelx.db`.
20. **Where are results returned to frontend?**  
    Through FastAPI route handlers in `backend/app/api/` serialized as Pydantic models to JSON over HTTP.
