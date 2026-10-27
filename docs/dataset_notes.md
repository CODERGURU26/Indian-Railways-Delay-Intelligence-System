# Dataset notes

The project uses the Hugging Face dataset `pjay-in/indian-railways-delays`.

Source: https://huggingface.co/datasets/pjay-in/indian-railways-delays
Licence: CC BY 4.0

Key schema fields:

- train_number
- train_name
- category
- start_date
- status
- seq
- station_code
- scheduled_arrival
- scheduled_departure
- actual_arrival
- actual_departure
- arrival_reported
- departure_reported
- arrival_delay_min
- departure_delay_min
- run_quality

Important interpretation notes:

- The `2026-10-10_` config is the preferred working config because it includes the `arrival_reported`, `departure_reported`, and `run_quality` fields.
- Missing actual times are not treated as zero delay.
- Estimated timestamps are stored separately from reported values.
- Station-level delay is distinct from destination punctuality, and the analytics service keeps those concepts separate.

## Included analyses

The analytics pipeline summarizes:

- Train performance using per-journey arrival-delay averages, then averaging journeys equally per train.
- Arrival and departure delays by station and train category.
- Arrival and departure delay trends by journey start date.
- Reported versus estimated arrival and departure coverage, excluding missing reporting flags from the denominator.
- Completed, cancelled, and other service statuses by distinct train journey.
- Route-level average delay and arrival delay by stop sequence (`seq`).

Missing delay values are excluded from averages. The `/summary` API currently uses labeled demo records; run the Spark job against the downloaded Parquet sample or use the Hive queries against cleaned HDFS data for dataset-backed results.
