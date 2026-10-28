import json

import duckdb

from app.services.stations import load_station_directory


def test_station_directory_joins_names_and_keeps_unmapped_codes(tmp_path):
    parquet_file = tmp_path / "records.parquet"
    reference_file = tmp_path / "stations.json"
    reference_file.write_text(json.dumps([
        {"station_code": "AAA", "station_name": "ALPHA STATION", "region_code": "NR"},
    ]), encoding="utf-8")

    connection = duckdb.connect()
    try:
        connection.execute("""
            CREATE TABLE test_records (
                station_code VARCHAR,
                arrival_delay_min DOUBLE,
                departure_delay_min DOUBLE
            )
        """)
        connection.execute("""
            INSERT INTO test_records VALUES
                ('AAA', 10, 4),
                ('AAA', 20, 8),
                ('BBB', 5, NULL)
        """)
        connection.execute(f"COPY test_records TO '{parquet_file}' (FORMAT PARQUET)")
    finally:
        connection.close()

    result = load_station_directory(str(tmp_path), str(reference_file))

    assert result["total"] == 2
    assert result["mapped"] == 1
    assert result["unmapped"] == 1
    assert result["stations"] == [
        {
            "code": "AAA",
            "name": "ALPHA STATION",
            "region": "NR",
            "stop_records": 2,
            "arrival_observations": 2,
            "departure_observations": 2,
            "avg_arrival_delay_min": 15.0,
            "avg_departure_delay_min": 6.0,
        },
        {
            "code": "BBB",
            "name": None,
            "region": None,
            "stop_records": 1,
            "arrival_observations": 1,
            "departure_observations": 0,
            "avg_arrival_delay_min": 5.0,
            "avg_departure_delay_min": None,
        },
    ]
