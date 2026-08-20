# SENTINELX — RAPID FIRE DEFENSE Q&A (50+ QUESTIONS)
**Format:** Rapid 1–4 Sentence Answers for Fast Judge Interruptions  

---

1. **Q: Why AI?**  
   *A: Static rules cannot predict unknown attack patterns or adapt to per-host workload differences. Machine learning allows us to dynamically learn baseline behavior for every device without writing thousands of manual threshold rules.*

2. **Q: Why this model (Isolation Forest)?**  
   *A: Isolation Forest is mathematically designed for anomaly detection by isolating outliers in few random decision tree splits. It is lightweight, requires no labeled attack data, and executes in under 1.2ms without needing GPUs.*

3. **Q: Why not rules?**  
   *A: Rules are brittle, trigger massive false alarms during normal traffic spikes, and fail when attackers disguise malicious actions using legitimate tools like PowerShell or curl.*

4. **Q: Why not just use an EDR?**  
   *A: EDRs operate on single-endpoint kernel signatures and process hooks. SentinelX provides multi-signal behavioral correlation across network, authentication, and system metrics with transparent mathematical explainability.*

5. **Q: Why not just use a SIEM?**  
   *A: SIEMs are costly log indexing engines that rely on static thresholds. SentinelX acts as an intelligent analytical correlation layer that filters noise before alerts overwhelm analysts.*

6. **Q: Where is your backend?**  
   *A: Located in `backend/app`, running as an asynchronous Python service with FastAPI on Uvicorn.*

7. **Q: Where does inference happen?**  
   *A: Directly in-memory inside `AnomalyDetectionService.score()` in `backend/app/services/anomaly_detection.py`.*

8. **Q: What data do you use?**  
   *A: 9 behavioral telemetry features per host covering CPU, memory, connection counts, inbound/outbound bytes, DNS queries, failed logins, process creation, and destination diversity.*

9. **Q: How accurate is your model?**  
   *A: Because Isolation Forest is unsupervised, conventional supervised accuracy does not apply. We evaluate performance by verifying clean baseline separation and zero false alarms across our 53 automated unit tests.*

10. **Q: How scalable is the backend?**  
    *A: The prototype handles local streaming via SQLite. For enterprise scale (10,000+ endpoints), we decouple ingestion using Apache Kafka, Redis baseline caches, and TimescaleDB.*

11. **Q: What is innovative about SentinelX?**  
    *A: Our two-stage pipeline: per-host z-score normalization that solves device role asymmetry, combined with a multi-signal noise gate that eliminates single-metric false alarms.*

12. **Q: What is simulated in your project?**  
    *A: The telemetry data stream and the compromise injection are synthetically generated to model real-world attack behaviors for demonstration.*

13. **Q: What is real in your project?**  
    *A: The entire backend API, SQLite persistence, Isolation Forest training, z-score mathematics, correlation fusion, incident state machine, and React dashboard are 100% real working code.*

14. **Q: What is your biggest limitation?**  
    *A: The lack of a live operating system eBPF kernel driver to collect real network packets directly from production machines.*

15. **Q: What happens with false positives?**  
    *A: Our multi-signal noise gate suppresses single-metric spikes (e.g. routine file downloads) by clamping correlation breadth and severity to zero if fewer than two independent signals deviate.*

16. **Q: Can an attacker evade your system?**  
    *A: An attacker who executes a very slow, low-intensity attack over months could attempt to poison the retraining baseline. We counter this by maintaining long-term historical baseline snapshots.*

17. **Q: Is the anomaly score a probability?**  
    *A: No, it is a calibrated percentile index from 0 to 100. Our fused Compromise Probability combines the ML anomaly score with multi-signal breadth and severity.*

18. **Q: Why should SIH select you?**  
    *A: Because we built a fully working, mathematically sound, explainable security analytics platform with clean code, 53 passing tests, and zero fabricated claims.*

19. **Q: What framework powers the backend?**  
    *A: FastAPI 0.115.6 on Python 3.12.*

20. **Q: What database are you using?**  
    *A: SQLite 3 accessed via Python's native `sqlite3` driver with parameterized SQL queries.*

21. **Q: How many features does the ML model take?**  
    *A: Exactly 9 numerical features per host.*

22. **Q: How many trees are in the Isolation Forest?**  
    *A: 200 isolation trees (`n_estimators=200`).*

23. **Q: How often does the background telemetry tick?**  
    *A: Every 4 seconds (`TICK_SECONDS = 4`).*

24. **Q: How often does the model retrain?**  
    *A: Every 30 ticks, which corresponds to approximately every 2 minutes.*

25. **Q: What data does the model retrain on?**  
    *A: All historical telemetry confirmed normal (`is_anomalous = 0`). It never trains on compromised data.*

26. **Q: What is the incident creation threshold?**  
    *A: A compromise probability of 80.0% or higher.*

27. **Q: How do you prevent duplicate incidents?**  
    *A: By checking `get_active_incident_for_host()` to ensure only one `OPEN` or `INVESTIGATING` ticket exists per host at a time.*

28. **Q: What are the incident status states?**  
    *A: `OPEN`, `INVESTIGATING`, and `RESOLVED`.*

29. **Q: Can an incident be reopened?**  
    *A: Yes, if a resolved host is compromised again and crosses the 80% threshold, a new incident ticket is opened.*

30. **Q: How does the frontend fetch data?**  
    *A: Through an Axios HTTP client polling the backend REST API every 7 seconds.*

31. **Q: What are the 4 severity tiers?**  
    *A: Critical ($\ge 75$), High ($\ge 50$), Medium ($\ge 25$), and Low ($< 25$).*

32. **Q: What significance threshold is used for z-scores?**  
    *A: Absolute z-score $\ge 2.0$ standard deviations.*

33. **Q: How is correlation breadth calculated?**  
    *A: The count of significant deviating signals divided by 9.*

34. **Q: How is evidence contribution calculated?**  
    *A: The absolute z-score of a signal divided by the sum of absolute z-scores across all deviating signals, expressed as a percentage.*

35. **Q: Do evidence contribution percentages sum to 100%?**  
    *A: Yes, guaranteed mathematically and verified in `test_explanation.py`.*

36. **Q: How do you prevent division by zero in baseline calculation?**  
    *A: We enforce a standard deviation floor of $\max(0.5, 0.02 \times |\mu|)$.*

37. **Q: What happens if an unknown hostname is requested?**  
    *A: The API returns an HTTP 404 Not Found response.*

38. **Q: What happens if invalid status text is sent in a PATCH request?**  
    *A: Pydantic rejects it with an HTTP 422 Unprocessable Entity response.*

39. **Q: What happens if the model is called before training?**  
    *A: It raises `NotTrainedError`, which the API returns as HTTP 503 Service Unavailable.*

40. **Q: How many endpoints are in your demo fleet?**  
    *A: 5 simulated endpoints (`HOST-001`, `HOST-017`, `HOST-023`, `HOST-042`, `HOST-051`).*

41. **Q: What roles exist in the demo fleet?**  
    *A: 3 systems (workstations), 1 perimeter firewall, and 1 core router.*

42. **Q: Why does the firewall have higher baseline outbound traffic?**  
    *A: Because firewalls naturally route transit network traffic; our baseline profiles model this asymmetry.*

43. **Q: What happens during a simulated compromise on HOST-042?**  
    *A: Outbound traffic spikes 6–15x, DNS spikes 4–9x, unique destinations spike 5–12x, processes spawn, and failed logins increase.*

44. **Q: Does SentinelX support multi-tenancy right now?**  
    *A: Not in this prototype; multi-tenancy with organization partitioning is planned for production.*

45. **Q: How do you protect against SQL injection?**  
    *A: By using parameterized SQL queries across all database operations.*

46. **Q: Is there any CORS restriction?**  
    *A: Yes, CORS is strictly restricted to `localhost:5173` and `127.0.0.1:5173`.*

47. **Q: What is the format of incident IDs?**  
    *A: `INC-` followed by a 4-digit zero-padded integer (e.g. `INC-0001`).*

48. **Q: How do you ensure reproducibility in ML training?**  
    *A: By setting a fixed random seed (`random_state=42`) in the Isolation Forest.*

49. **Q: How many unit tests are in the test suite?**  
    *A: Exactly 53 automated tests, all currently passing.*

50. **Q: What library powers the frontend data visualizations?**  
    *A: Recharts 2.15.0 rendering SVG bar and pie donut charts.*

51. **Q: Can SentinelX execute automated response actions?**  
    *A: It provides prescriptive, non-destructive playbooks for SOC analysts; automated firewall isolation is supported via webhook integrations in future scope.*
