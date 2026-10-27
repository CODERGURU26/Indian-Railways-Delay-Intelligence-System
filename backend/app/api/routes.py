from fastapi import APIRouter

from ..services.analytics import build_analytics_payload

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "railway-delay-api"}


@router.get("/summary")
def get_summary():
    sample_records = [
        {"train_number": "22901", "train_name": "RAJ EXPRESS", "start_date": "2026-10-08", "status": "completed", "seq": 1, "arrival_delay_min": 20, "departure_delay_min": 18, "station_code": "NDLS", "category": "RAJ", "arrival_reported": True, "departure_reported": True, "run_quality": 0.9},
        {"train_number": "22901", "train_name": "RAJ EXPRESS", "start_date": "2026-10-08", "status": "completed", "seq": 2, "arrival_delay_min": 40, "departure_delay_min": 42, "station_code": "AGC", "category": "RAJ", "arrival_reported": False, "departure_reported": True, "run_quality": 0.8},
        {"train_number": "12010", "train_name": "EXPRESS", "start_date": "2026-10-08", "status": "completed", "seq": 1, "arrival_delay_min": 15, "departure_delay_min": 12, "station_code": "BPL", "category": "EXP", "arrival_reported": True, "departure_reported": True, "run_quality": 0.7},
        {"train_number": "12010", "train_name": "EXPRESS", "start_date": "2026-10-08", "status": "completed", "seq": 2, "arrival_delay_min": 30, "departure_delay_min": 28, "station_code": "KOTA", "category": "EXP", "arrival_reported": True, "departure_reported": True, "run_quality": 0.6},
        {"train_number": "12952", "train_name": "MAIL EXPRESS", "start_date": "2026-10-09", "status": "cancelled", "seq": 1, "arrival_delay_min": 45, "departure_delay_min": 50, "station_code": "NDLS", "category": "MEX", "arrival_reported": False, "departure_reported": False, "run_quality": 0.5},
        {"train_number": "12952", "train_name": "MAIL EXPRESS", "start_date": "2026-10-09", "status": "cancelled", "seq": 2, "arrival_delay_min": 25, "departure_delay_min": 27, "station_code": "BCT", "category": "MEX", "arrival_reported": True, "departure_reported": True, "run_quality": 0.8},
    ]
    payload = build_analytics_payload(sample_records)
    payload["data_source"] = "demo fixture (replace with processed dataset to analyze real records)"
    return payload
