from typing import Optional

from pydantic import BaseModel, Field


class DelayRecordPayload(BaseModel):
    train_number: str = Field(..., description="Train number as stored in raw data, preserving leading zeros.")
    train_name: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[str] = None
    status: Optional[str] = None
    station_code: Optional[str] = None
    arrival_delay_min: Optional[float] = None
    departure_delay_min: Optional[float] = None
    arrival_reported: Optional[bool] = None
    departure_reported: Optional[bool] = None
    run_quality: Optional[float] = None


class SummaryRow(BaseModel):
    label: str
    value: float
    count: Optional[int] = None


class AnalyticsResponse(BaseModel):
    trains: list[SummaryRow]
    stations: list[SummaryRow]
    categories: list[SummaryRow]
    coverage: dict[str, float]
