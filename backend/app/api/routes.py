from fastapi import APIRouter

from ..services.analytics import build_analytics_payload

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "railway-delay-api"}


@router.get("/summary")
def get_summary():
    sample_records = [
        {"train_number": "22901", "arrival_delay_min": 20, "station_code": "NDLS", "category": "RAJ", "arrival_reported": True, "run_quality": 0.9},
        {"train_number": "22901", "arrival_delay_min": 40, "station_code": "AGC", "category": "RAJ", "arrival_reported": False, "run_quality": 0.8},
        {"train_number": "12010", "arrival_delay_min": 15, "station_code": "BPL", "category": "EXP", "arrival_reported": True, "run_quality": 0.7},
        {"train_number": "12010", "arrival_delay_min": 30, "station_code": "KOTA", "category": "EXP", "arrival_reported": True, "run_quality": 0.6},
        {"train_number": "12952", "arrival_delay_min": 45, "station_code": "NDLS", "category": "MEX", "arrival_reported": False, "run_quality": 0.5},
        {"train_number": "12952", "arrival_delay_min": 25, "station_code": "BCT", "category": "MEX", "arrival_reported": True, "run_quality": 0.8},
    ]
    return build_analytics_payload(sample_records)
