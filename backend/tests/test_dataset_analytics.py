import duckdb

from app.services.dataset_analytics import load_dataset_analytics


def test_dataset_analytics_aggregates_all_parquet_rows(tmp_path):
    parquet_file = tmp_path / "records.parquet"
    connection = duckdb.connect()
    try:
        connection.execute("""
            CREATE TABLE test_records (
                train_number VARCHAR,
                train_name VARCHAR,
                start_date DATE,
                status VARCHAR,
                seq INTEGER,
                station_code VARCHAR,
                category VARCHAR,
                arrival_delay_min DOUBLE,
                departure_delay_min DOUBLE,
                arrival_reported BOOLEAN,
                departure_reported BOOLEAN,
                run_quality DOUBLE,
                start_month VARCHAR,
                arrival_delay_band VARCHAR,
                departure_delay_band VARCHAR
            )
        """)
        connection.execute("""
            INSERT INTO test_records VALUES
                ('100', 'EXPRESS ONE', '2025-03-01', 'completed', 1, 'AAA', 'EXP', 0, 5, true, true, 0.8, '2025-03', 'Early or on time', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-01', 'completed', 2, 'BBB', 'EXP', 10, 15, false, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-04-02', 'cancelled', 1, 'AAA', 'EXP', 60, 65, true, false, 0.6, '2025-04', '16-60 min', 'Over 60 min'),
                ('100', 'EXPRESS ONE', '2025-03-02', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-03', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-04', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-05', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-06', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-07', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-08', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('100', 'EXPRESS ONE', '2025-03-09', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min')
        """)
        connection.execute(f"COPY test_records TO '{parquet_file}' (FORMAT PARQUET)")
    finally:
        connection.close()

    payload = load_dataset_analytics(str(tmp_path))

    assert payload["totals"] == {
        "records": 11,
        "trains": 1,
        "stations": 2,
        "journeys": 10,
        "start_date": "2025-03-01",
        "end_date": "2025-04-02",
    }
    assert payload["trains"] == [{
        "label": "100",
        "name": "EXPRESS ONE",
        "display_label": "100 · EXPRESS ONE",
        "value": 14.5,
        "count": 10,
    }]
    assert payload["monthly_trends"] == [
        {"label": "2025-03", "value": 9.44, "departure_value": 14.44, "count": 9, "departure_count": 9},
        {"label": "2025-04", "value": 60.0, "departure_value": 65.0, "count": 1, "departure_count": 1},
    ]
    assert {row["label"]: row["count"] for row in payload["statuses"]} == {
        "completed": 9,
        "cancelled": 1,
    }
    assert payload["sequence"] == [
        {"label": "1", "value": 14.0, "count": 10},
        {"label": "2", "value": 10.0, "count": 1},
    ]
