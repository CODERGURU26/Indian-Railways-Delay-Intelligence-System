USE railway_delay;

-- Average delay by train
SELECT train_number, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay
FROM railway_stops
WHERE arrival_delay_min IS NOT NULL
GROUP BY train_number
ORDER BY avg_arrival_delay DESC
LIMIT 20;

-- Average delay by station
SELECT station_code, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       AVG(CAST(departure_delay_min AS DOUBLE)) AS avg_departure_delay
FROM railway_stops
GROUP BY station_code
ORDER BY avg_arrival_delay DESC
LIMIT 20;

-- Delay distribution by category
SELECT category, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       COUNT(*) AS observation_count
FROM railway_stops
WHERE arrival_delay_min IS NOT NULL
GROUP BY category
ORDER BY avg_arrival_delay DESC;

-- Reported versus estimated counts
SELECT
  SUM(CASE WHEN arrival_reported = TRUE THEN 1 ELSE 0 END) AS reported_arrivals,
  SUM(CASE WHEN arrival_reported = FALSE THEN 1 ELSE 0 END) AS estimated_arrivals,
  SUM(CASE WHEN departure_reported = TRUE THEN 1 ELSE 0 END) AS reported_departures,
  SUM(CASE WHEN departure_reported = FALSE THEN 1 ELSE 0 END) AS estimated_departures
FROM railway_stops;

-- Status summary
SELECT status, COUNT(*) AS route_count
FROM railway_stops
GROUP BY status;
