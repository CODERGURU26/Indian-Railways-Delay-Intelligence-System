from app.services.analytics import build_analytics_payload


def test_build_analytics_payload_shapes():
    records = [
        {"train_number": "12952", "start_date": "2026-10-08", "status": "completed", "seq": 1, "arrival_delay_min": 45, "departure_delay_min": 46, "station_code": "NDLS", "category": "MEX", "arrival_reported": False, "departure_reported": True, "run_quality": 0.5},
        {"train_number": "12952", "start_date": "2026-10-08", "status": "completed", "seq": 2, "arrival_delay_min": 25, "departure_delay_min": 26, "station_code": "BCT", "category": "MEX", "arrival_reported": True, "departure_reported": True, "run_quality": 0.8},
        {"train_number": "22901", "start_date": "2026-10-08", "status": "completed", "seq": 1, "arrival_delay_min": 20, "departure_delay_min": 21, "station_code": "NDLS", "category": "RAJ", "arrival_reported": True, "departure_reported": True, "run_quality": 0.9},
        {"train_number": "22901", "start_date": "2026-10-08", "status": "completed", "seq": 2, "arrival_delay_min": 40, "departure_delay_min": 41, "station_code": "AGC", "category": "RAJ", "arrival_reported": False, "departure_reported": False, "run_quality": 0.8},
        {"train_number": "12010", "start_date": "2026-10-09", "status": "cancelled", "seq": 1, "arrival_delay_min": 15, "departure_delay_min": 16, "station_code": "BPL", "category": "EXP", "arrival_reported": True, "departure_reported": True, "run_quality": 0.7},
    ]

    payload = build_analytics_payload(records)

    assert "trains" in payload
    assert "stations" in payload
    assert "categories" in payload
    assert "monthly_trends" in payload
    assert "statuses" in payload
    assert "routes" in payload
    assert "sequence" not in payload
    assert "coverage" in payload
    assert payload["trains"][0]["label"] == "12952"
    assert payload["coverage"]["reported"] > 0
    assert payload["coverage"]["estimated"] > 0
    assert payload["totals"]["trains"] == 3
    assert payload["totals"]["stations"] == 4
    assert payload["monthly_trends"][0]["label"] == "2026-10"
    assert payload["routes"][0]["label"] == "NDLS → BCT"
    assert payload["statuses"][0]["label"] == "completed"


def test_missing_delay_is_ignored():
    records = [
        {"train_number": "123", "arrival_delay_min": None, "station_code": "NDLS", "category": "EXP"},
        {"train_number": "123", "arrival_delay_min": 10, "station_code": "NDLS", "category": "EXP", "arrival_reported": True},
    ]

    payload = build_analytics_payload(records)
    assert payload["trains"][0]["value"] == 10.0


def test_train_average_weights_journeys_equally():
    records = [
        {"train_number": "100", "start_date": "2026-10-01", "arrival_delay_min": 0},
        {"train_number": "100", "start_date": "2026-10-01", "arrival_delay_min": 0},
        {"train_number": "100", "start_date": "2026-10-02", "arrival_delay_min": 60},
    ]

    payload = build_analytics_payload(records)
    assert payload["trains"] == [{"label": "100", "value": 30.0, "count": 2}]


def test_missing_reporting_flags_are_excluded_from_coverage_denominator():
    records = [
        {"arrival_reported": True, "departure_reported": False, "run_quality": 0.8},
        {"arrival_reported": None, "departure_reported": None},
    ]

    coverage = build_analytics_payload(records)["coverage"]
    assert coverage["reported"] == 100
    assert coverage["estimated"] == 0
    assert coverage["departure_reported_pct"] == 0


def test_monthly_trends_group_days_in_the_same_month():
    records = [
        {"start_date": "2026-10-01", "arrival_delay_min": 20, "departure_delay_min": 30},
        {"start_date": "2026-10-28", "arrival_delay_min": 40, "departure_delay_min": 50},
        {"start_date": "2026-11-02", "arrival_delay_min": 10, "departure_delay_min": None},
    ]

    trends = build_analytics_payload(records)["monthly_trends"]

    assert trends == [
        {"label": "2026-10", "value": 30.0, "departure_value": 40.0, "count": 2, "departure_count": 2},
        {"label": "2026-11", "value": 10.0, "departure_value": None, "count": 1, "departure_count": 0},
    ]


def test_train_and_station_summaries_include_at_least_eight_when_available():
    records = [
        {
            "train_number": f"{number:05d}",
            "start_date": f"2026-10-{number:02d}",
            "station_code": f"ST{number:02d}",
            "seq": 1,
            "arrival_delay_min": float(number),
            "departure_delay_min": float(number),
        }
        for number in range(1, 9)
    ]

    payload = build_analytics_payload(records)

    assert len(payload["trains"]) == 8
    assert len(payload["stations"]) == 8
