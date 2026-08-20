# SENTINELX — MACHINE LEARNING FORENSIC AUDIT
**Model Type:** Unsupervised Behavioural Anomaly Isolation  
**Library:** `scikit-learn 1.6.0` (`sklearn.ensemble.IsolationForest`) & `numpy 2.2.0`  
**Target Level:** Defense under Statistical & ML Judge Scrutiny  

---

## 1. The Core ML Model Specification

* **Algorithm:** `IsolationForest` (`sklearn.ensemble.IsolationForest`)
* **File:** `backend/app/services/anomaly_detection.py:L67-L71`
* **Instantiated Hyperparameters:**
  * `n_estimators`: `200` (Ensemble of 200 random isolation decision trees)
  * `max_samples`: `"auto"` (Draws $\min(256, n)$ samples per tree)
  * `contamination`: `"auto"` (Threshold determined dynamically via decision function)
  * `random_state`: `42` (Deterministic reproducibility)
  * `bootstrap`: `False`

---

## 2. Feature Engineering & Mathematical Formulation

### The 9 Input Feature Vectors:
$$\mathbf{x} = \begin{bmatrix} x_{\text{cpu}} \\ x_{\text{mem}} \\ x_{\text{conn}} \\ x_{\text{in\_bytes}} \\ x_{\text{out\_bytes}} \\ x_{\text{dns}} \\ x_{\text{failed\_logins}} \\ x_{\text{new\_proc}} \\ x_{\text{uniq\_dest}} \end{bmatrix} \in \mathbb{R}^9$$

### Per-Host Learned Baseline Curation:
In `backend/app/services/anomaly_detection.py:L111-L126`, for each host $h$ and each feature $j$:
$$\mu_{h, j} = \frac{1}{N} \sum_{i=1}^{N} x_{i, j}, \qquad \sigma_{h, j} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_{i, j} - \mu_{h, j})^2}$$

### Dynamic Standard Deviation Variance Floor:
To prevent zero-variance blowup (e.g. a workstation with 0 failed logins for days):
$$\sigma_{\text{floor}} = \max\left(0.5, 0.02 \times |\mu_{h, j}|\right)$$
$$\sigma_{h, j}^{\text{adj}} = \max\left(\sigma_{h, j}, \sigma_{\text{floor}}\right)$$

### Per-Host Z-Score Transformation:
$$z_j = \text{clip}\left(\frac{x_j - \mu_{h, j}}{\sigma_{h, j}^{\text{adj}}}, -10.0, +10.0\right)$$

---

## 3. Why Per-Host Normalization Is Critical (Host Asymmetry)

A core defense point against judges asking *"Why not train directly on raw network metrics?"*:

* **The Problem:** In an enterprise network, a Perimeter Firewall (`HOST-023`) routinely pushes 200+ network connections and millions of outbound bytes per minute. Conversely, an HR Workstation (`HOST-017`) normally pushes 10 connections and 300 bytes.
* **If Raw Metrics Were Used:** The model would flag every firewall as permanently anomalous and miss massive exfiltration on workstations.
* **SentinelX Solution:** By converting raw values into **per-host z-scores** before feeding them to the Isolation Forest, the model evaluates **deviation relative to that specific device's role**, making an identical raw increase of 5,000 bytes highly anomalous on `HOST-017` but completely normal on `HOST-023`.

---

## 4. Score Calibration Formulation

Isolation Forest outputs an unbounded raw anomaly score via `score_samples()`:
$$\text{raw\_score} = - \text{score\_samples}(\mathbf{z})$$

To make this interpretable on a stable $[0, 100]$ scale for SOC analysts:
1. During training on normal fleet data, the service computes:
   * $\text{Median Raw Score} = M_{\text{train}}$
   * $\text{Max Raw Score} = X_{\text{train}}$
2. During inference on incoming telemetry:
   $$\text{Anomaly Score} = \text{clip}\left(\frac{\text{raw\_score} - M_{\text{train}}}{X_{\text{train}} - M_{\text{train}}} \times 100, 0.0, 100.0\right)$$
* Normal steady-state behavior centers near **0–15**.
* Significant anomalous multi-signal deviations spike to **70–100**.

---

## 5. Truthful ML Evaluation & Metric Audit

### ⚠️ IMPORTANT DEFENSE REMINDER FOR JUDGES:
**SentinelX's core anomaly detector is an UNSUPERVISED model.**

| Metric | Status in Codebase | Forensic Reality |
| :--- | :--- | :--- |
| **Accuracy** | **NOT APPLICABLE** | Unsupervised Isolation Forest does not train on binary labeled classification loss. |
| **Confusion Matrix** | **NOT COMPUTED IN CODE** | No static test-split ground truth confusion matrix is stored in repository. |
| **Precision / Recall / F1** | **NOT COMPUTED IN CODE** | Claiming static "99.4% F1-score" would be a fabrication. |
| **ROC-AUC / PR-AUC** | **NOT COMPUTED IN CODE** | Not evaluated on offline benchmark datasets (e.g. KDD99/CICIDS). |
| **Unit Test Coverage** | **VERIFIED (100%)** | 53 unit tests verify mathematical bounds, std floors, isolation scoring, and noise rejection. |

### Verified Codebase Parameters:
* `MIN_SAMPLES_PER_HOST = 5`
* `STD_FLOOR_ABS = 0.5`
* `STD_FLOOR_REL = 0.02` (2% of feature baseline mean)
* `Z_SCORE_CLIP = 10.0`
* `Z_SIGNIFICANCE_THRESHOLD = 2.0`
* `MIN_CORRELATED_SIGNALS_FOR_BOOST = 2`
* `INCIDENT_CREATION_THRESHOLD = 80.0`
* `WEIGHT_ANOMALY_SCORE = 0.5`
* `WEIGHT_CORRELATION_BREADTH = 0.3`
* `WEIGHT_SEVERITY = 0.2`
