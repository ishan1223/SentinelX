"""Behavioural anomaly detection for SentinelX.

Learns per-host baselines from telemetry history and detects statistical
deviations using host-normalized z-scores and an unsupervised Isolation Forest.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = [
    "cpu_usage",
    "memory_usage",
    "network_connections",
    "inbound_bytes",
    "outbound_bytes",
    "dns_queries",
    "failed_logins",
    "new_processes",
    "unique_destinations",
]

MIN_SAMPLES_PER_HOST = 5
STD_FLOOR_ABS = 0.5
STD_FLOOR_REL = 0.02  # at least 2% of the feature's own baseline mean
Z_SCORE_CLIP = 10.0


@dataclass
class FeatureDeviation:
    feature: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: str  # "increase" | "decrease"


@dataclass
class AnomalyResult:
    hostname: str
    timestamp: str
    anomaly_score: float  # 0-100, percentile-calibrated against training baseline
    raw_isolation_score: float
    deviations: list[FeatureDeviation] = field(default_factory=list)


class NotTrainedError(RuntimeError):
    pass


class AnomalyDetectionService:
    """Modular, retrainable behavioural anomaly detector.

    Usage:
        service = AnomalyDetectionService()
        service.train(db.fetch_normal_telemetry_rows())
        result = service.score(latest_telemetry_row)
    """

    def __init__(self, n_estimators: int = 200, random_state: int = 42) -> None:
        self._model = IsolationForest(
            n_estimators=n_estimators,
            max_samples="auto",
            random_state=random_state,
        )
        self._host_baselines: dict[str, dict[str, tuple[float, float]]] = {}
        self._global_baseline: dict[str, tuple[float, float]] = {}
        self._train_score_median: float | None = None
        self._train_score_max: float | None = None
        self.trained_at: str | None = None
        self.n_training_samples: int = 0
        self.is_trained: bool = False

    # -- training -----------------------------------------------------

    def train(self, normal_rows: list[sqlite3.Row | dict]) -> None:
        rows = [dict(r) for r in normal_rows]
        if len(rows) < MIN_SAMPLES_PER_HOST:
            raise ValueError(
                f"Need at least {MIN_SAMPLES_PER_HOST} normal telemetry samples to train, got {len(rows)}"
            )

        by_host: dict[str, list[dict]] = {}
        for row in rows:
            by_host.setdefault(row["hostname"], []).append(row)

        self._host_baselines = {
            hostname: self._compute_baseline(host_rows)
            for hostname, host_rows in by_host.items()
            if len(host_rows) >= MIN_SAMPLES_PER_HOST
        }
        self._global_baseline = self._compute_baseline(rows)

        z_matrix = np.array([self._zscore_vector(row) for row in rows])

        self._model.fit(z_matrix)
        raw_scores = -self._model.score_samples(z_matrix)
        self._train_score_median = float(np.median(raw_scores))
        self._train_score_max = float(raw_scores.max())

        self.trained_at = datetime.now(timezone.utc).isoformat()
        self.n_training_samples = len(rows)
        self.is_trained = True

    @staticmethod
    def _compute_baseline(rows: list[dict]) -> dict[str, tuple[float, float]]:
        # The floor must scale with the feature's own magnitude: an
        # absolute-only floor is negligible for count-like features (0/1
        # failed logins) but would let byte-scale features (tens of
        # thousands) saturate the z-score clip from tiny, meaningless
        # fluctuations whenever a feature happens to look near-constant in
        # the training window.
        baseline = {}
        for feature in FEATURES:
            values = np.array([row[feature] for row in rows], dtype=float)
            mean = float(values.mean())
            std = float(values.std())
            floor = max(STD_FLOOR_ABS, STD_FLOOR_REL * abs(mean))
            baseline[feature] = (mean, max(std, floor))
        return baseline

    def _baseline_for(self, hostname: str) -> dict[str, tuple[float, float]]:
        return self._host_baselines.get(hostname, self._global_baseline)

    def _zscore_vector(self, row: dict) -> np.ndarray:
        baseline = self._baseline_for(row["hostname"])
        z = []
        for feature in FEATURES:
            mean, std = baseline[feature]
            score = (row[feature] - mean) / std
            z.append(float(np.clip(score, -Z_SCORE_CLIP, Z_SCORE_CLIP)))
        return np.array(z)

    # -- inference ------------------------------------------------------

    def score(self, row: sqlite3.Row | dict) -> AnomalyResult:
        if not self.is_trained:
            raise NotTrainedError("AnomalyDetectionService.train() must be called before score()")

        row = dict(row)
        baseline = self._baseline_for(row["hostname"])
        z_vector = self._zscore_vector(row)

        raw_score = float(-self._model.score_samples([z_vector])[0])
        anomaly_score = self._normalize_score(raw_score)

        deviations = []
        for feature, z in zip(FEATURES, z_vector):
            mean, std = baseline[feature]
            deviations.append(
                FeatureDeviation(
                    feature=feature,
                    value=float(row[feature]),
                    baseline_mean=round(mean, 2),
                    baseline_std=round(std, 2),
                    z_score=round(float(z), 2),
                    direction="increase" if z >= 0 else "decrease",
                )
            )
        deviations.sort(key=lambda d: abs(d.z_score), reverse=True)

        return AnomalyResult(
            hostname=row["hostname"],
            timestamp=row["timestamp"],
            anomaly_score=round(anomaly_score, 2),
            raw_isolation_score=round(raw_score, 4),
            deviations=deviations,
        )

    def _normalize_score(self, raw_score: float) -> float:
        """Linear calibration mapping training median to 0 and training max to 100."""
        if self._train_score_median is None or self._train_score_max is None:
            return 0.0
        spread = self._train_score_max - self._train_score_median
        if spread <= 0:
            return 0.0
        anomaly_score = (raw_score - self._train_score_median) / spread * 100
        return float(np.clip(anomaly_score, 0, 100))


# Process-wide singleton — trained once at startup from historical normal
# telemetry (see app.main lifespan). A single instance is intentional: this
# is one modular service shared by the /risk and /incidents endpoints.
anomaly_service = AnomalyDetectionService()
