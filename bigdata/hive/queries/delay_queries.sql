USE railway_delay;

-- Average journey delay by train, so longer routes do not dominate the result.
SELECT train_number, AVG(journey_avg_arrival_delay) AS avg_arrival_delay,
       COUNT(*) AS journey_count
FROM (
  SELECT train_number, start_date,
         AVG(CAST(arrival_delay_min AS DOUBLE)) AS journey_avg_arrival_delay
  FROM railway_stops
  WHERE arrival_delay_min IS NOT NULL
  GROUP BY train_number, start_date
) journey_delays
GROUP BY train_number
ORDER BY avg_arrival_delay DESC
LIMIT 20;

-- Average delay by station
SELECT station_code, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       AVG(CAST(departure_delay_min AS DOUBLE)) AS avg_departure_delay,
       COUNT(*) AS stop_record_count
FROM railway_stops
GROUP BY station_code
ORDER BY avg_arrival_delay DESC
LIMIT 20;

-- Delay distribution by category
SELECT category, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       AVG(CAST(departure_delay_min AS DOUBLE)) AS avg_departure_delay,
       COUNT(*) AS observation_count
FROM railway_stops
GROUP BY category
ORDER BY avg_arrival_delay DESC;

-- Delay trends by journey start date
SELECT start_date, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       AVG(CAST(departure_delay_min AS DOUBLE)) AS avg_departure_delay,
       COUNT(*) AS stop_record_count
FROM railway_stops
GROUP BY start_date
ORDER BY start_date;

-- Reported versus estimated counts
SELECT
  SUM(CASE WHEN arrival_reported = TRUE THEN 1 ELSE 0 END) AS reported_arrivals,
  SUM(CASE WHEN arrival_reported = FALSE THEN 1 ELSE 0 END) AS estimated_arrivals,
  SUM(CASE WHEN departure_reported = TRUE THEN 1 ELSE 0 END) AS reported_departures,
  SUM(CASE WHEN departure_reported = FALSE THEN 1 ELSE 0 END) AS estimated_departures,
  AVG(run_quality) AS average_run_quality
FROM railway_stops;

-- Service status by distinct train journey
SELECT status, COUNT(DISTINCT concat(train_number, '|', start_date)) AS journey_count
FROM railway_stops
GROUP BY status;

-- Arrival delay by stop position along the route
SELECT seq, AVG(CAST(arrival_delay_min AS DOUBLE)) AS avg_arrival_delay,
       COUNT(*) AS observation_count
FROM railway_stops
WHERE arrival_delay_min IS NOT NULL
GROUP BY seq
ORDER BY seq;
