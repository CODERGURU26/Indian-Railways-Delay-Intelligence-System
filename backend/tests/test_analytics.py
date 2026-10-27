from app.services.analytics import build_analytics_payload


def test_build_analytics_payload_shapes():
    records = [
        {"train_number": "12952", "arrival_delay_min": 45, "station_code": "NDLS", "category": "MEX", "arrival_reported": False, "run_quality": 0.5},
        {"train_number": "12952", "arrival_delay_min": 25, "station_code": "BCT", "category": "MEX", "arrival_reported": True, "run_quality": 0.8},
        {"train_number": "22901", "arrival_delay_min": 20, "station_code": "NDLS", "category": "RAJ", "arrival_reported": True, "run_quality": 0.9},
        {"train_number": "22901", "arrival_delay_min": 40, "station_code": "AGC", "category": "RAJ", "arrival_reported": False, "run_quality": 0.8},
        {"train_number": "12010", "arrival_delay_min": 15, "station_code": "BPL", "category": "EXP", "arrival_reported": True, "run_quality": 0.7},
    ]

    payload = build_analytics_payload(records)

    assert "trains" in payload
    assert "stations" in payload
    assert "categories" in payload
    assert "coverage" in payload
    assert payload["trains"][0]["label"] == "12952"
    assert payload["coverage"]["reported"] > 0
    assert payload["coverage"]["estimated"] > 0


def test_missing_delay_is_ignored():
    records = [
        {"train_number": "123", "arrival_delay_min": None, "station_code": "NDLS", "category": "EXP"},
        {"train_number": "123", "arrival_delay_min": 10, "station_code": "NDLS", "category": "EXP", "arrival_reported": True},
    ]

    payload = build_analytics_payload(records)
    assert payload["trains"][0]["value"] == 10.0
