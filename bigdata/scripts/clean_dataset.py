from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = "2025-02-08_2026-02-07"
RAW_ROOT = ROOT / "data" / "raw"
CLEAN_ROOT = ROOT / "data" / "cleaned"
REPORT_ROOT = ROOT / "data" / "reports"


def clean_dataset(config: str) -> dict:
    source_dir = RAW_ROOT / config
    source_files = list(source_dir.glob("*.parquet"))
    if not source_files:
        raise FileNotFoundError(f"No downloaded Parquet shards found under {source_dir}")

    output_dir = CLEAN_ROOT / config
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "records.parquet"
    report_path = REPORT_ROOT / f"cleaning_{config}.json"
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    source_pattern = str(source_dir / "*.parquet").replace("\\", "/").replace("'", "''")
    target_path = str(target).replace("\\", "/").replace("'", "''")
    connection = duckdb.connect()
    try:
        connection.execute(f"""
            CREATE TEMP VIEW source_records AS
            SELECT * FROM read_parquet('{source_pattern}')
        """)
        connection.execute(f"""
            COPY (
                SELECT
                    NULLIF(trim(train_number), '') AS train_number,
                    NULLIF(trim(train_name), '') AS train_name,
                    NULLIF(trim(category), '') AS category,
                    try_cast(start_date AS DATE) AS start_date,
                    NULLIF(trim(status), '') AS status,
                    try_cast(seq AS INTEGER) AS seq,
                    NULLIF(trim(station_code), '') AS station_code,
                    try_cast(scheduled_arrival AS TIMESTAMP) AS scheduled_arrival,
                    try_cast(scheduled_departure AS TIMESTAMP) AS scheduled_departure,
                    try_cast(actual_arrival AS TIMESTAMP) AS actual_arrival,
                    try_cast(actual_departure AS TIMESTAMP) AS actual_departure,
                    arrival_reported,
                    departure_reported,
                    try_cast(arrival_delay_min AS DOUBLE) AS arrival_delay_min,
                    try_cast(departure_delay_min AS DOUBLE) AS departure_delay_min,
                    try_cast(run_quality AS DOUBLE) AS run_quality,
                    strftime(try_cast(start_date AS DATE), '%Y-%m') AS start_month,
                    CASE
                        WHEN arrival_delay_min IS NULL THEN 'Unknown'
                        WHEN arrival_delay_min <= 0 THEN 'Early or on time'
                        WHEN arrival_delay_min <= 15 THEN '1-15 min'
                        WHEN arrival_delay_min <= 60 THEN '16-60 min'
                        ELSE 'Over 60 min'
                    END AS arrival_delay_band,
                    CASE
                        WHEN departure_delay_min IS NULL THEN 'Unknown'
                        WHEN departure_delay_min <= 0 THEN 'Early or on time'
                        WHEN departure_delay_min <= 15 THEN '1-15 min'
                        WHEN departure_delay_min <= 60 THEN '16-60 min'
                        ELSE 'Over 60 min'
                    END AS departure_delay_band
                FROM source_records
            ) TO '{target_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        row = connection.execute(f"""
            SELECT
                count(*) AS retained_rows,
                min(start_date) AS min_start_date,
                max(start_date) AS max_start_date,
                count(*) FILTER (WHERE train_number IS NULL) AS missing_train_number,
                count(*) FILTER (WHERE station_code IS NULL) AS missing_station_code,
                count(*) FILTER (WHERE start_date IS NULL) AS invalid_start_date,
                count(*) FILTER (WHERE arrival_delay_min < 0) AS negative_arrival_delays,
                count(*) FILTER (WHERE arrival_delay_min > 1440) AS arrival_delays_over_24h,
                count(*) - count(DISTINCT (train_number, start_date, seq)) AS duplicate_journey_stops
            FROM read_parquet('{target_path}')
        """).fetchone()
        source_rows = connection.execute(
            "SELECT count(*) FROM source_records"
        ).fetchone()[0]
    finally:
        connection.close()

    report = {
        "dataset": "pjay-in/indian-railways-delays",
        "config": config,
        "cleaned_at": datetime.now(timezone.utc).isoformat(),
        "source_rows": source_rows,
        "retained_rows": row[0],
        "min_start_date": str(row[1]) if row[1] else None,
        "max_start_date": str(row[2]) if row[2] else None,
        "missing_train_number": row[3],
        "missing_station_code": row[4],
        "invalid_start_date": row[5],
        "negative_arrival_delays": row[6],
        "arrival_delays_over_24h": row[7],
        "duplicate_journey_stops": row[8],
        "cleaned_file": str(target),
        "policy": "Normalize blank text and types, retain all source rows, and flag anomalies without clipping delays.",
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean and enrich downloaded railway Parquet data.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Downloaded dataset config to clean.")
    args = parser.parse_args()
    print(json.dumps(clean_dataset(args.config), indent=2))


if __name__ == "__main__":
    main()
