import duckdb

from app.services.dataset_analytics import load_dataset_analytics


def test_dataset_analytics_aggregates_all_parquet_rows(tmp_path):
    parquet_file = tmp_path / "records.parquet"
    connection = duckdb.connect()
    try:
        connection.execute("""
            CREATE TABLE test_records (
                train_number VARCHAR,
                start_date DATE,
                status VARCHAR,
                seq INTEGER,
                station_code VARCHAR,
                category VARCHAR,
                arrival_delay_min DOUBLE,
                departure_delay_min DOUBLE,
                arrival_reported BOOLEAN,
                departure_reported BOOLEAN,
                run_quality DOUBLE
            )
        """)
        connection.execute("""
            INSERT INTO test_records VALUES
                ('100', '2026-10-01', 'completed', 1, 'AAA', 'EXP', 0, 5, true, true, 0.8),
                ('100', '2026-10-01', 'completed', 2, 'BBB', 'EXP', 10, 15, false, true, 0.8),
                ('100', '2026-10-02', 'cancelled', 1, 'AAA', 'EXP', 60, 65, true, false, 0.6)
        """)
        connection.execute(f"COPY test_records TO '{parquet_file}' (FORMAT PARQUET)")
    finally:
        connection.close()

    payload = load_dataset_analytics(str(tmp_path))

    assert payload["totals"] == {
        "records": 3,
        "trains": 1,
        "stations": 2,
        "journeys": 2,
    }
    assert payload["trains"] == [{"label": "100", "value": 32.5, "count": 2}]
    assert payload["monthly_trends"][0]["value"] == 23.33
    assert {row["label"]: row["count"] for row in payload["statuses"]} == {
        "completed": 1,
        "cancelled": 1,
    }
    assert payload["sequence"] == [
        {"label": "1", "value": 30.0, "count": 2},
        {"label": "2", "value": 10.0, "count": 1},
    ]
