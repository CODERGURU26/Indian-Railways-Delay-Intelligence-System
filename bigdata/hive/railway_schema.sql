CREATE DATABASE IF NOT EXISTS railway_delay;
USE railway_delay;

CREATE EXTERNAL TABLE IF NOT EXISTS railway_stops (
    train_number STRING,
    train_name STRING,
    category STRING,
    start_date STRING,
    status STRING,
    seq INT,
    station_code STRING,
    scheduled_arrival TIMESTAMP,
    scheduled_departure TIMESTAMP,
    actual_arrival TIMESTAMP,
    actual_departure TIMESTAMP,
    arrival_reported BOOLEAN,
    departure_reported BOOLEAN,
    arrival_delay_min INT,
    departure_delay_min INT,
    run_quality DOUBLE
)
STORED AS PARQUET
LOCATION '/railway/cleaned';

CREATE TABLE IF NOT EXISTS delay_by_train AS
SELECT
    train_number,
    AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
    MAX(CAST(arrival_delay_min AS DOUBLE)) AS max_arrival_delay,
    COUNT(*) AS records
FROM railway_stops
WHERE arrival_delay_min IS NOT NULL
GROUP BY train_number;

CREATE TABLE IF NOT EXISTS delay_by_station AS
SELECT
    station_code,
    AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
    AVG(CAST(departure_delay_min AS DOUBLE)) AS avg_departure_delay,
    COUNT(*) AS records
FROM railway_stops
GROUP BY station_code;
