# SENTINELX — "SHOW ME THE CODE" DEFENSE REFERENCE
**Target:** Live Code Inspection During Hackathon Defense  
**Purpose:** Instantly navigate to exact files, functions, and lines when judges demand proof  

---

### CLAIM 1: "You normalize telemetry relative to each individual host's baseline."
* **FILE:** `backend/app/services/anomaly_detection.py`
* **FUNCTION:** `_zscore_vector(row)`
* **LINES:** `L131 - L139`
* **CODE SNIPPET:**
  ```python
  def _zscore_vector(self, row: dict) -> np.ndarray:
      baseline = self._baseline_for(row["hostname"])
      z = []
      for feature in FEATURES:
          mean, std = baseline[feature]
          score = (row[feature] - mean) / std
          z.append(float(np.clip(score, -Z_SCORE_CLIP, Z_SCORE_CLIP)))
      return np.array(z)
  ```
* **EXPLANATION:** Demonstrates how raw metrics are transformed into per-host z-scores before passing to the Isolation Forest, ensuring workstations and firewalls are judged against their own historical means.

---

### CLAIM 2: "You have a noise-filtering gate that ignores single-metric spikes."
* **FILE:** `backend/app/services/threat_correlation.py`
* **FUNCTION:** `assess(result: AnomalyResult)`
* **LINES:** `L70 - L83`
* **CODE SNIPPET:**
  ```python
  significant = [d for d in result.deviations if abs(d.z_score) >= Z_SIGNIFICANCE_THRESHOLD]
  correlated_signal_count = len(significant)

  # Require at least 2 independent signals to deviate to filter out noise
  if correlated_signal_count >= MIN_CORRELATED_SIGNALS_FOR_BOOST:
      correlation_breadth = min(correlated_signal_count / len(result.deviations), 1.0) if result.deviations else 0.0
      avg_severity = sum(abs(d.z_score) for d in significant) / correlated_signal_count
      severity_factor = min(avg_severity / MAX_EXPECTED_AVG_SEVERITY, 1.0)
  else:
      correlation_breadth = 0.0
      severity_factor = 0.0
  ```
* **EXPLANATION:** Proves that if fewer than 2 independent signals deviate by $|z| \ge 2.0$, correlation breadth and severity factors are zeroed out, preventing single noisy metrics from triggering alerts.

---

### CLAIM 3: "You calculate a fused compromise probability using explicit weights."
* **FILE:** `backend/app/services/threat_correlation.py`
* **FUNCTION:** `assess(result: AnomalyResult)`
* **LINES:** `L84 - L90`
* **CODE SNIPPET:**
  ```python
  compromise_probability = (
      WEIGHT_ANOMALY_SCORE * result.anomaly_score
      + WEIGHT_CORRELATION_BREADTH * correlation_breadth * 100
      + WEIGHT_SEVERITY * severity_factor * 100
  )
  compromise_probability = round(min(max(compromise_probability, 0.0), 100.0), 2)
  ```
* **EXPLANATION:** Proves the exact 50% ML score + 30% correlation breadth + 20% severity weighting formula.

---

### CLAIM 4: "Your explainability engine computes exact percentage contribution shares."
* **FILE:** `backend/app/services/explanation.py`
* **FUNCTION:** `_build_evidence(signals)`
* **LINES:** `L94 - L116`
* **CODE SNIPPET:**
  ```python
  total_weight = sum(abs(s.z_score) for s in signals)
  evidence = []
  for s in signals:
      contribution = (abs(s.z_score) / total_weight * 100) if total_weight else 0.0
      ...
  ```
* **EXPLANATION:** Proves that feature deviations are converted into mathematically balanced contribution percentages summing to 100% across evidence items.

---

### CLAIM 5: "Your system prevents duplicate incident creation while an attack is active."
* **FILE:** `backend/app/services/incident_management.py`
* **FUNCTION:** `run_incident_detection()`
* **LINES:** `L120 - L124`
* **CODE SNIPPET:**
  ```python
  if assessment.compromise_probability < INCIDENT_CREATION_THRESHOLD:
      continue
  if db.get_active_incident_for_host(hostname) is not None:
      continue
  ```
* **EXPLANATION:** Proves that even if compromise probability remains $\ge 80.0$ for 50 ticks, only 1 ticket is created as long as an active (`OPEN` or `INVESTIGATING`) incident exists.

---

### CLAIM 6: "You automatically retrain the baseline model periodically in the background."
* **FILE:** `backend/app/main.py`
* **FUNCTION:** `_telemetry_loop()`
* **LINES:** `L30 - L33`
* **CODE SNIPPET:**
  ```python
  tick_count += 1
  if tick_count % RETRAIN_EVERY_N_TICKS == 0:
      anomaly_service.train(db.fetch_normal_telemetry_rows())
  ```
* **EXPLANATION:** Proves that every 30 ticks (~2 minutes at 4s intervals), the Isolation Forest is re-fitted on all confirmed normal historical telemetry.

---

### CLAIM 7: "You use parameterized SQL queries to eliminate SQL injection."
* **FILE:** `backend/app/db/database.py`
* **FUNCTION:** `insert_telemetry_row(sample)` & `insert_incident(...)`
* **LINES:** `L137 - L150`, `L210 - L222`
* **CODE SNIPPET:**
  ```python
  conn.execute(
      """
      INSERT INTO telemetry (
          hostname, timestamp, cpu_usage, memory_usage, ...
      ) VALUES (
          :hostname, :timestamp, :cpu_usage, :memory_usage, ...
      )
      """,
      sample,
  )
  ```
* **EXPLANATION:** Proves that no string formatting (`f"INSERT INTO..."`) is used, eliminating SQL injection vulnerabilities.

---

### CLAIM 8: "Your simulation directly skews multi-signal parameters."
* **FILE:** `backend/app/services/telemetry_engine.py`
* **FUNCTION:** `_apply_compromise(sample)`
* **LINES:** `L104 - L143`
* **CODE SNIPPET:**
  ```python
  sample["outbound_bytes"] = (
      round(sample["outbound_bytes"] * random.uniform(6, 15)) + random.randint(2000, 8000)
  )
  sample["dns_queries"] = round(sample["dns_queries"] * random.uniform(4, 9) + 5)
  sample["unique_destinations"] = round(sample["unique_destinations"] * random.uniform(5, 12) + 3)
  sample["new_processes"] = sample["new_processes"] + random.randint(4, 12)
  sample["failed_logins"] = sample["failed_logins"] + random.randint(3, 10)
  sample["is_anomalous"] = 1
  ```
* **EXPLANATION:** Proves the exact stochastic multipliers used to distort 6 independent telemetry signals during a simulated attack.
