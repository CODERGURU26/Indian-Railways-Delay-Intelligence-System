from fastapi import APIRouter, HTTPException

from ..services.dataset_analytics import load_dataset_analytics
from ..services.stations import load_station_directory

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "railway-delay-api"}


@router.get("/summary")
def get_summary():
    try:
        return load_dataset_analytics()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/stations")
def get_stations():
    try:
        return load_station_directory()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
