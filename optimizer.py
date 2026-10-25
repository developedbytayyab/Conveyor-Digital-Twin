"""Simple bounded simulation optimizer; suggestions are not PLC commands."""
from __future__ import annotations

def recommend_speed(current_speed: float, temperature_c: float, vibration_mm_s: float,
                    min_speed: float = 0.5, max_speed: float = 1.8) -> dict:
    if not (0 < min_speed <= max_speed):
        raise ValueError("Speed bounds must satisfy 0 < min_speed <= max_speed")
    if not min_speed <= current_speed <= max_speed:
        current_speed = min(max(current_speed, min_speed), max_speed)
    reason = "Operating within simulated safe limits"
    target = current_speed
    if temperature_c >= 75 or vibration_mm_s >= 7:
        target = max(min_speed, current_speed * 0.65)
        reason = "Reduce speed because temperature/vibration is critical"
    elif temperature_c <= 62 and vibration_mm_s <= 3.5:
        target = min(max_speed, current_speed * 1.08)
        reason = "Small throughput increase; sensor readings are within limits"
    target = round(min(max(target, min_speed), max_speed), 3)
    return {"current_speed_m_s": round(current_speed, 3), "recommended_speed_m_s": target,
            "speed_change_pct": round((target-current_speed)/current_speed*100, 1), "reason": reason,
            "simulated_only": True}
