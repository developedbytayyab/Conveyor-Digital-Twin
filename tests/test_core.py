import pytest
from simulator import generate_sensor_data
from ml_detector import detect_anomalies
from optimizer import recommend_speed
from reports import csv_bytes, pdf_report


def test_simulator_shape_and_repeatability():
    a = generate_sensor_data(100, seed=5)
    b = generate_sensor_data(100, seed=5)
    assert len(a) == 100
    assert a.equals(b)


def test_simulator_rejects_bad_size():
    with pytest.raises(ValueError):
        generate_sensor_data(5)


def test_detector_returns_expected_columns():
    result = detect_anomalies(generate_sensor_data(120, seed=9))
    assert {"is_anomaly", "anomaly_score", "severity"}.issubset(result.columns)
    assert result.is_anomaly.dtype == bool


def test_detector_rejects_missing_sensor():
    with pytest.raises(ValueError):
        detect_anomalies(generate_sensor_data(30).drop(columns=["temperature_c"]))


def test_optimizer_reduces_speed_for_critical_conditions():
    result = recommend_speed(1.2, 82, 8)
    assert result["recommended_speed_m_s"] < result["current_speed_m_s"]
    assert result["simulated_only"] is True


def test_optimizer_increases_speed_in_normal_conditions():
    result = recommend_speed(1.0, 55, 2.5)
    assert result["recommended_speed_m_s"] > result["current_speed_m_s"]


def test_optimizer_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        recommend_speed(1.0, 55, 2.0, min_speed=2.0, max_speed=1.0)


def test_reports_generate_files():
    data = detect_anomalies(generate_sensor_data(30))
    assert csv_bytes(data).startswith(b"timestamp,")
    assert pdf_report(data).startswith(b"%PDF")
