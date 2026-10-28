from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import duckdb


DATASET_NAME = "pjay-in/indian-railways-delays"
DATASET_CONFIG = "2025-02-08_2026-02-07"
ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "bigdata" / "data" / "cleaned" / DATASET_CONFIG
QUALITY_REPORT = ROOT / "bigdata" / "data" / "reports" / f"cleaning_{DATASET_CONFIG}.json"


def _records(connection: duckdb.DuckDBPyConnection, query: str) -> list[dict]:
    result = connection.execute(query)
    columns = [description[0] for description in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def _round_metrics(rows: list[dict]) -> list[dict]:
    for row in rows:
        for key in ("value", "departure_value", "percentage"):
            if row.get(key) is not None:
                row[key] = round(float(row[key]), 2)
    return rows


@lru_cache(maxsize=1)
def load_dataset_analytics(data_path: str = str(DATA_PATH)) -> dict:
    parquet_file = Path(data_path) / "records.parquet"
    if not parquet_file.is_file():
        raise FileNotFoundError(
            f"Cleaned one-year dataset not found at {parquet_file}. "
            "Download the historical config and run bigdata/scripts/clean_dataset.py."
        )

    quality_report = {}
    if QUALITY_REPORT.is_file() and Path(data_path) == DATA_PATH:
        quality_report = json.loads(QUALITY_REPORT.read_text(encoding="utf-8"))

    quoted_path = str(parquet_file).replace("\\", "/").replace("'", "''")
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            f"CREATE VIEW records AS SELECT * FROM read_parquet('{quoted_path}')"
        )
        totals = connection.execute("""
            SELECT
                count(*) AS records,
                count(DISTINCT train_number) AS trains,
                count(DISTINCT station_code) AS stations,
                count(DISTINCT (train_number, start_date)) AS journeys,
                min(start_date) AS start_date,
                max(start_date) AS end_date
            FROM records
            WHERE start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
        """).fetchone()

        trains = _records(connection, """
            WITH journey AS (
                SELECT train_number, start_date, avg(arrival_delay_min) AS journey_delay
                FROM records
                WHERE arrival_delay_min IS NOT NULL AND train_number IS NOT NULL
                  AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                GROUP BY train_number, start_date
            ),
            train_names AS (
                SELECT train_number, train_name
                FROM (
                    SELECT train_number, NULLIF(trim(train_name), '') AS train_name,
                           row_number() OVER (
                               PARTITION BY train_number
                               ORDER BY count(*) DESC, NULLIF(trim(train_name), '')
                           ) AS name_rank
                    FROM records
                    WHERE train_number IS NOT NULL AND NULLIF(trim(train_name), '') IS NOT NULL
                      AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                    GROUP BY train_number, NULLIF(trim(train_name), '')
                )
                WHERE name_rank = 1
            )
            SELECT train_names.train_name AS label,
                   journey.train_number AS train_number,
                   train_names.train_name AS name,
                   round(avg(journey.journey_delay), 2) AS value,
                   count(*) AS count
            FROM journey
            JOIN train_names ON journey.train_number = train_names.train_number
            GROUP BY journey.train_number, train_names.train_name
            HAVING count(*) >= 10
            ORDER BY value DESC
            LIMIT 10
        """)
        stations = _records(connection, """
            SELECT station_code AS label,
                   round(avg(arrival_delay_min), 2) AS value,
                   round(avg(departure_delay_min), 2) AS departure_value,
                   count(arrival_delay_min) AS count,
                   count(departure_delay_min) AS departure_count
            FROM records
            WHERE station_code IS NOT NULL
              AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
            GROUP BY station_code
            HAVING count(arrival_delay_min) >= 100
            ORDER BY value DESC NULLS LAST
            LIMIT 10
        """)
        categories = _records(connection, """
            WITH journey AS (
                SELECT train_number, start_date, category,
                       avg(arrival_delay_min) AS arrival_delay,
                       avg(departure_delay_min) AS departure_delay
                FROM records
                WHERE category IS NOT NULL
                  AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                GROUP BY train_number, start_date, category
            )
            SELECT category AS label, round(avg(arrival_delay), 2) AS value,
                   round(avg(departure_delay), 2) AS departure_value,
                   count(arrival_delay) AS count,
                   count(departure_delay) AS departure_count
            FROM journey
            GROUP BY category
            ORDER BY value DESC NULLS LAST
        """)
        monthly_trends = _records(connection, """
            WITH journey AS (
                SELECT start_month, train_number, start_date,
                       avg(arrival_delay_min) AS arrival_delay,
                       avg(departure_delay_min) AS departure_delay
                FROM records
                WHERE start_month IS NOT NULL
                  AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                GROUP BY start_month, train_number, start_date
            )
            SELECT start_month AS label,
                   round(avg(arrival_delay), 2) AS value,
                   round(avg(departure_delay), 2) AS departure_value,
                   count(arrival_delay) AS count,
                   count(departure_delay) AS departure_count
            FROM journey
            GROUP BY start_month
            ORDER BY start_month
        """)
        statuses = _records(connection, """
            SELECT status AS label,
                   count(DISTINCT (train_number, start_date)) AS value,
                   count(DISTINCT (train_number, start_date)) AS count
            FROM records
            WHERE status IS NOT NULL
              AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
            GROUP BY status
            ORDER BY count DESC
        """)
        sequence = _records(connection, """
            SELECT CAST(seq AS VARCHAR) AS label,
                   round(avg(arrival_delay_min), 2) AS value,
                   count(arrival_delay_min) AS count
            FROM records
            WHERE seq IS NOT NULL
              AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
            GROUP BY seq
            ORDER BY seq
        """)
        routes = _records(connection, """
            WITH journey AS (
                SELECT train_number, start_date,
                       string_agg(station_code, ' -> ' ORDER BY seq) AS route,
                       avg(arrival_delay_min) AS journey_delay
                FROM records
                WHERE station_code IS NOT NULL
                  AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                GROUP BY train_number, start_date
                HAVING count(DISTINCT station_code) > 1
            )
            SELECT route AS label, round(avg(journey_delay), 2) AS value,
                   count(*) AS count
            FROM journey
            WHERE journey_delay IS NOT NULL
            GROUP BY route
            HAVING count(*) >= 20
            ORDER BY value DESC
            LIMIT 10
        """)
        delay_distribution = _records(connection, """
            SELECT arrival_delay_band AS label, count(*) AS count,
                   round(count(*) * 100.0 / sum(count(*)) OVER (), 2) AS percentage
            FROM records
            WHERE arrival_delay_band != 'Unknown'
              AND start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
            GROUP BY arrival_delay_band
            ORDER BY CASE arrival_delay_band
                WHEN 'Early or on time' THEN 1
                WHEN '1-15 min' THEN 2
                WHEN '16-60 min' THEN 3
                WHEN 'Over 60 min' THEN 4
            END
        """)
        coverage_row = connection.execute("""
            SELECT
                count(*) FILTER (WHERE arrival_reported IS NOT NULL) AS arrival_known,
                count(*) FILTER (WHERE arrival_reported IS TRUE) AS arrival_reported,
                count(*) FILTER (WHERE departure_reported IS NOT NULL) AS departure_known,
                count(*) FILTER (WHERE departure_reported IS TRUE) AS departure_reported,
                avg(run_quality) AS run_quality_avg,
                count(*) FILTER (WHERE arrival_delay_min > 60) AS over_60_count,
                count(arrival_delay_min) AS arrival_count
            FROM records
            WHERE start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
        """).fetchone()
        mean_delays = connection.execute("""
            WITH journey AS (
                SELECT train_number, start_date,
                       avg(arrival_delay_min) AS arrival_delay,
                       avg(departure_delay_min) AS departure_delay
                FROM records
                WHERE start_date BETWEEN DATE '2025-02-08' AND DATE '2026-02-07'
                GROUP BY train_number, start_date
            )
            SELECT avg(arrival_delay), avg(departure_delay)
            FROM journey
        """).fetchone()
    finally:
        connection.close()

    (
        arrival_known, arrival_reported, departure_known, departure_reported,
        quality, over_60_count, arrival_count,
    ) = coverage_row
    mean_arrival, mean_departure = mean_delays
    arrival_pct = arrival_reported / arrival_known * 100 if arrival_known else None
    departure_pct = departure_reported / departure_known * 100 if departure_known else None
    status_counts = {row["label"].lower(): row["count"] for row in statuses}
    cancelled = sum(value for label, value in status_counts.items() if "cancel" in label)
    journey_count = totals[3] or 0
    cancellation_pct = cancelled / journey_count * 100 if journey_count else 0
    severe_pct = over_60_count / arrival_count * 100 if arrival_count else 0

    monthly_with_arrival = [row for row in monthly_trends if row["value"] is not None]
    worst_month = max(monthly_with_arrival, key=lambda row: row["value"], default=None)
    best_month = min(monthly_with_arrival, key=lambda row: row["value"], default=None)
    worst_category = next((row for row in categories if row["value"] is not None), None)

    insights = []
    if worst_month:
        insights.append({
            "title": "Highest-delay month",
            "value": worst_month["label"],
            "detail": f"{worst_month['value']:.2f} min average arrival delay across {worst_month['count']:,} journeys.",
        })
    if best_month:
        insights.append({
            "title": "Lowest-delay month",
            "value": best_month["label"],
            "detail": f"{best_month['value']:.2f} min average arrival delay across {best_month['count']:,} journeys.",
        })
    if worst_category:
        insights.append({
            "title": "Highest-delay category",
            "value": worst_category["label"],
            "detail": f"{worst_category['value']:.2f} min average arrival delay per journey.",
        })
    insights.append({
        "title": "Severe arrival delays",
        "value": f"{severe_pct:.2f}%",
        "detail": f"{over_60_count:,} of {arrival_count:,} observed stop arrivals were over 60 minutes late.",
    })
    insights.append({
        "title": "Cancelled journeys",
        "value": f"{cancellation_pct:.2f}%",
        "detail": f"{cancelled:,} of {journey_count:,} distinct journeys had a cancellation status.",
    })

    return {
        "trains": _round_metrics(trains),
        "stations": _round_metrics(stations),
        "categories": _round_metrics(categories),
        "monthly_trends": _round_metrics(monthly_trends),
        "statuses": statuses,
        "routes": _round_metrics(routes),
        "sequence": _round_metrics(sequence),
        "delay_distribution": _round_metrics(delay_distribution),
        "coverage": {
            "arrival_reported_pct": round(arrival_pct, 2) if arrival_pct is not None else None,
            "departure_reported_pct": round(departure_pct, 2) if departure_pct is not None else None,
            "run_quality_avg": round(float(quality), 4) if quality is not None else None,
        },
        "kpis": {
            "mean_arrival_delay_min": round(float(mean_arrival), 2) if mean_arrival is not None else None,
            "mean_departure_delay_min": round(float(mean_departure), 2) if mean_departure is not None else None,
            "severe_arrival_pct": round(severe_pct, 2),
            "cancelled_journeys_pct": round(cancellation_pct, 2),
        },
        "insights": insights,
        "quality": quality_report,
        "totals": {
            "records": totals[0],
            "trains": totals[1],
            "stations": totals[2],
            "journeys": totals[3],
            "start_date": str(totals[4]) if totals[4] else None,
            "end_date": str(totals[5]) if totals[5] else None,
        },
        "data_source": f"{DATASET_NAME} · {DATASET_CONFIG} · one-year train split",
    }
