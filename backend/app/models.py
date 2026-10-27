from sqlalchemy import Boolean, Column, Float, Integer, String

from .database import Base


class DelayRecord(Base):
    __tablename__ = "delay_records"

    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String, nullable=False, index=True)
    train_name = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    start_date = Column(String, nullable=True)
    status = Column(String, nullable=True)
    station_code = Column(String, nullable=True, index=True)
    arrival_delay_min = Column(Float, nullable=True)
    departure_delay_min = Column(Float, nullable=True)
    arrival_reported = Column(Boolean, nullable=True)
    departure_reported = Column(Boolean, nullable=True)
    run_quality = Column(Float, nullable=True)


class DelaySummary(Base):
    __tablename__ = "delay_summaries"

    id = Column(Integer, primary_key=True, index=True)
    metric = Column(String, nullable=False, index=True)
    dimension = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    label = Column(String, nullable=False)
