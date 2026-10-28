from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "bigdata" / "data" / "cleaned" / "2025-02-08_2026-02-07"
REFERENCE_PATH = ROOT / "bigdata" / "data" / "reference" / "indian_railway_stations.json"


@lru_cache(maxsize=1)
def load_station_directory(
    data_path: str = str(DATA_PATH),
    reference_path: str = str(REFERENCE_PATH),
) -> dict:
    parquet_file = Path(data_path) / "records.parquet"
    if not parquet_file.is_file():
        raise FileNotFoundError(f"Cleaned one-year dataset not found at {parquet_file}")
    reference_file = Path(reference_path)
    if not reference_file.is_file():
        raise FileNotFoundError(f"Station code reference not found at {reference_file}")

    reference_rows = json.loads(reference_file.read_text(encoding="utf-8"))
    station_names = {
        row["station_code"]: {
            "name": row["station_name"],
            "region": row.get("region_code"),
        }
        for row in reference_rows
        if row.get("station_code") and row.get("station_name")
    }

    quoted_path = str(parquet_file).replace("\\", "/").replace("'", "''")
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(f"""
            SELECT station_code,
                   count(*) AS stop_records,
                   count(arrival_delay_min) AS arrival_observations,
                   round(avg(arrival_delay_min), 2) AS avg_arrival_delay_min
            FROM read_parquet('{quoted_path}')
            WHERE station_code IS NOT NULL
            GROUP BY station_code
            ORDER BY stop_records DESC, station_code
        """).fetchall()
    finally:
        connection.close()

    stations = []
    for code, stop_records, arrival_observations, avg_delay in rows:
        reference = station_names.get(code)
        stations.append({
            "code": code,
            "name": reference["name"] if reference else None,
            "region": reference["region"] if reference else None,
            "stop_records": stop_records,
            "arrival_observations": arrival_observations,
            "avg_arrival_delay_min": float(avg_delay) if avg_delay is not None else None,
        })

    mapped_count = sum(station["name"] is not None for station in stations)
    return {
        "stations": stations,
        "total": len(stations),
        "mapped": mapped_count,
        "unmapped": len(stations) - mapped_count,
        "mapping_source": "vstflugel/indian-railway-dataset (MIT)",
    }
