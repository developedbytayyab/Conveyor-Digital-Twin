"""Hybrid threshold + Isolation Forest anomaly detection."""
from __future__ import annotations
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["temperature_c", "vibration_mm_s", "motor_current_a", "belt_speed_m_s", "package_rate_min"]
LIMITS = {"temperature_c": 75.0, "vibration_mm_s": 7.0, "motor_current_a": 18.0}


def detect_anomalies(data: pd.DataFrame, contamination: float = 0.06, seed: int = 42) -> pd.DataFrame:
    missing = set(FEATURES) - set(data.columns)
    if missing:
        raise ValueError(f"Missing sensor columns: {', '.join(sorted(missing))}")
    if data.empty:
        raise ValueError("Sensor data cannot be empty")
    if not 0.001 <= contamination <= 0.25:
        raise ValueError("contamination must be between 0.001 and 0.25")
    out = data.copy()
    x = out[FEATURES].astype(float)
    if x.isna().any().any():
        raise ValueError("Sensor data contains missing values")
    model = make_pipeline(StandardScaler(), IsolationForest(contamination=contamination, random_state=seed, n_estimators=120))
    out["ml_anomaly"] = model.fit_predict(x) == -1
    out["threshold_anomaly"] = False
    for col, limit in LIMITS.items():
        out["threshold_anomaly"] |= out[col] > limit
    out["is_anomaly"] = out["ml_anomaly"] | out["threshold_anomaly"]
    out["anomaly_score"] = (-model.decision_function(x)).clip(0, 1)
    out["severity"] = "Normal"
    out.loc[out["is_anomaly"] & ~out["threshold_anomaly"], "severity"] = "Warning"
    out.loc[out["threshold_anomaly"], "severity"] = "Critical"
    return out
