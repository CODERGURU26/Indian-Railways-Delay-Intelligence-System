from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import duckdb


DATASET_NAME = "pjay-in/indian-railways-delays"
DATASET_CONFIG = "2026-10-10_"
DATA_PATH = (
    Path(__file__).resolve().parents[3]
    / "bigdata"
    / "data"
    / "raw"
    / DATASET_CONFIG
)


def _records(connection: duckdb.DuckDBPyConnection, query: str) -> list[dict]:
    result = connection.execute(query)
    columns = [description[0] for description in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def _round_metrics(rows: list[dict]) -> list[dict]:
    for row in rows:
        for key in ("value", "departure_value"):
            if row.get(key) is not None:
                row[key] = round(float(row[key]), 2)
    return rows


@lru_cache(maxsize=1)
def load_dataset_analytics(data_path: str = str(DATA_PATH)) -> dict:
    parquet_pattern = str(Path(data_path) / "*.parquet").replace("\\", "/")
    if not list(Path(data_path).glob("*.parquet")):
        raise FileNotFoundError(f"No downloaded dataset Parquet shards found under {data_path}")

    connection = duckdb.connect(":memory:")
    try:
        escaped_pattern = parquet_pattern.replace("'", "''")
        connection.execute(
            f"CREATE VIEW records AS SELECT * FROM read_parquet('{escaped_pattern}')"
        )
        totals = connection.execute(
            """
            SELECT
                count(*) AS records,
                count(DISTINCT train_number) AS trains,
                count(DISTINCT station_code) AS stations,
                count(DISTINCT (train_number, start_date)) AS journeys
            FROM records
            """
        ).fetchone()

        trains = _records(connection, """
            WITH journey AS (
                SELECT train_number, start_date, avg(arrival_delay_min) AS journey_delay
                FROM records
                WHERE arrival_delay_min IS NOT NULL AND train_number IS NOT NULL
                GROUP BY train_number, start_date
            )
            SELECT train_number AS label, round(avg(journey_delay), 2) AS value,
                   count(*) AS count
            FROM journey
            GROUP BY train_number
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
            GROUP BY station_code
            ORDER BY value DESC NULLS LAST
            LIMIT 10
        """)
        categories = _records(connection, """
            SELECT category AS label,
                   round(avg(arrival_delay_min), 2) AS value,
                   round(avg(departure_delay_min), 2) AS departure_value,
                   count(arrival_delay_min) AS count,
                   count(departure_delay_min) AS departure_count
            FROM records
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY value DESC NULLS LAST
        """)
        monthly_trends = _records(connection, """
            SELECT strftime(start_date, '%Y-%m') AS label,
                   round(avg(arrival_delay_min), 2) AS value,
                   round(avg(departure_delay_min), 2) AS departure_value,
                   count(arrival_delay_min) AS count,
                   count(departure_delay_min) AS departure_count
            FROM records
            WHERE start_date IS NOT NULL
            GROUP BY label
            ORDER BY label
        """)
        statuses = _records(connection, """
            SELECT status AS label,
                   count(DISTINCT (train_number, start_date)) AS value,
                   count(DISTINCT (train_number, start_date)) AS count
            FROM records
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        """)
        sequence = _records(connection, """
            SELECT CAST(seq AS VARCHAR) AS label,
                   round(avg(arrival_delay_min), 2) AS value,
                   count(arrival_delay_min) AS count
            FROM records
            WHERE seq IS NOT NULL
            GROUP BY seq
            ORDER BY seq
        """)
        routes = _records(connection, """
            WITH journey AS (
                SELECT train_number, start_date,
                       string_agg(station_code, ' -> ' ORDER BY seq) AS route,
                       avg(arrival_delay_min) AS journey_delay,
                       count(DISTINCT station_code) AS stop_count
                FROM records
                WHERE station_code IS NOT NULL
                GROUP BY train_number, start_date
            )
            SELECT route AS label, round(avg(journey_delay), 2) AS value,
                   count(*) AS count
            FROM journey
            WHERE stop_count > 1 AND journey_delay IS NOT NULL
            GROUP BY route
            ORDER BY value DESC
            LIMIT 10
        """)
        coverage_row = connection.execute("""
            SELECT
                count(*) FILTER (WHERE arrival_reported IS NOT NULL) AS arrival_known,
                count(*) FILTER (WHERE arrival_reported IS TRUE) AS arrival_reported,
                count(*) FILTER (WHERE departure_reported IS NOT NULL) AS departure_known,
                count(*) FILTER (WHERE departure_reported IS TRUE) AS departure_reported,
                avg(run_quality) AS run_quality_avg
            FROM records
        """).fetchone()
    finally:
        connection.close()

    arrival_known, arrival_reported, departure_known, departure_reported, quality = coverage_row
    arrival_pct = arrival_reported / arrival_known * 100 if arrival_known else 0
    departure_pct = departure_reported / departure_known * 100 if departure_known else 0
    return {
        "trains": _round_metrics(trains),
        "stations": _round_metrics(stations),
        "categories": _round_metrics(categories),
        "monthly_trends": _round_metrics(monthly_trends),
        "statuses": statuses,
        "routes": _round_metrics(routes),
        "sequence": _round_metrics(sequence),
        "coverage": {
            "reported": round(arrival_pct, 2),
            "estimated": round(100 - arrival_pct, 2) if arrival_known else 0,
            "arrival_reported_pct": round(arrival_pct, 2),
            "departure_reported_pct": round(departure_pct, 2),
            "run_quality_avg": round(float(quality), 4) if quality is not None else 0,
        },
        "totals": {
            "records": totals[0],
            "trains": totals[1],
            "stations": totals[2],
            "journeys": totals[3],
        },
        "data_source": f"{DATASET_NAME} · {DATASET_CONFIG} · full train split",
    }
