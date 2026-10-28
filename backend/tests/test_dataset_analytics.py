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
                ('100', 'EXPRESS ONE', '2025-03-09', 'completed', 1, 'AAA', 'EXP', 10, 15, true, true, 0.8, '2025-03', '1-15 min', '1-15 min'),
                ('200', '', '2025-03-10', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-11', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-12', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-13', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-14', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-15', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-16', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-17', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-18', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min'),
                ('200', '', '2025-03-19', 'completed', 1, 'AAA', 'EXP', 30, 30, true, true, 0.8, '2025-03', '16-60 min', '16-60 min')
        """)
        connection.execute(f"COPY test_records TO '{parquet_file}' (FORMAT PARQUET)")
    finally:
        connection.close()

    payload = load_dataset_analytics(str(tmp_path))

    assert payload["totals"] == {
        "records": 21,
        "trains": 2,
        "stations": 2,
        "journeys": 20,
        "start_date": "2025-03-01",
        "end_date": "2025-04-02",
    }
    assert payload["trains"] == [{
        "label": "EXPRESS ONE",
        "train_number": "100",
        "name": "EXPRESS ONE",
        "value": 14.5,
        "count": 10,
    }]
    assert payload["monthly_trends"] == [
        {"label": "2025-03", "value": 20.26, "departure_value": 22.63, "count": 19, "departure_count": 19},
        {"label": "2025-04", "value": 60.0, "departure_value": 65.0, "count": 1, "departure_count": 1},
    ]
    assert {row["label"]: row["count"] for row in payload["statuses"]} == {
        "completed": 19,
        "cancelled": 1,
    }
    assert payload["sequence"] == [
        {"label": "1", "value": 22.0, "count": 20},
        {"label": "2", "value": 10.0, "count": 1},
    ]
