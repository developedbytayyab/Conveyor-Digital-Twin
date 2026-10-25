"""Deterministic, configurable conveyor sensor simulation."""
from __future__ import annotations
import numpy as np
import pandas as pd

SENSOR_COLUMNS = ["temperature_c", "vibration_mm_s", "motor_current_a", "belt_speed_m_s", "package_rate_min"]


def generate_sensor_data(n: int = 300, seed: int = 7, anomaly_rate: float = 0.06) -> pd.DataFrame:
    if n < 10:
        raise ValueError("n must be at least 10")
    if not 0 <= anomaly_rate <= 0.5:
        raise ValueError("anomaly_rate must be between 0 and 0.5")
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    speed = np.clip(1.2 + 0.08*np.sin(t/18) + rng.normal(0, .025, n), .5, 2.0)
    temp = 48 + 2.5*np.sin(t/35) + 5*(speed-1.2) + rng.normal(0, 1.1, n)
    vibration = np.clip(2.2 + .35*np.sin(t/13) + rng.normal(0, .18, n), .2, None)
    current = 8 + 1.4*speed + rng.normal(0, .35, n)
    rate = np.clip(38*speed + rng.normal(0, 2, n), 0, None)
    df = pd.DataFrame({"timestamp": pd.date_range("2026-01-01", periods=n, freq="s"), "temperature_c": temp,
                       "vibration_mm_s": vibration, "motor_current_a": current, "belt_speed_m_s": speed, "package_rate_min": rate})
    k = int(n * anomaly_rate)
    if k:
        idx = rng.choice(np.arange(n), size=k, replace=False)
        df.loc[idx, "temperature_c"] += rng.uniform(12, 24, k)
        df.loc[idx, "vibration_mm_s"] += rng.uniform(2.5, 6, k)
        df.loc[idx, "motor_current_a"] += rng.uniform(3, 7, k)
    return df
