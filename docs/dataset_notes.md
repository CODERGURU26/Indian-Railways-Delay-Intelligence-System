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

- The dashboard uses `2025-02-08_2026-02-07`, a historical config with 17,522,150 rows and source dates spanning 2025-02-08 through 2026-02-07. Hugging Face also provides `2026-10-10_` (2,805,574 rows) as a separate current-data config.
- Missing actual times are not treated as zero delay.
- Estimated timestamps are stored separately from reported values.
- Station-level delay is distinct from destination punctuality, and the analytics service keeps those concepts separate.

Run `python bigdata/ingestion/download_dataset.py --config 2025-02-08_2026-02-07` from the project root to fetch every historical Parquet shard. The downloader checks each shard's byte size and row count, validates the total against Hugging Face metadata, and records SHA-256 checksums. Then run `python bigdata/scripts/clean_dataset.py --config 2025-02-08_2026-02-07` to normalize values, derive analysis features, and create a data-quality report while retaining all input rows.

## Included analyses

The one-year analytics pipeline summarizes:

- Train performance using per-journey arrival-delay averages, then averaging journeys equally per train.
- Arrival and departure delays by station and train category.
- Arrival and departure delay trends by journey start date.
- Reported versus estimated arrival and departure coverage, excluding missing reporting flags from the denominator.
- Completed, cancelled, and other service statuses by distinct train journey.
- Route-level average delay and arrival delay by stop sequence (`seq`).
- Delay distribution across early/on-time, 1-15, 16-60, and over-60-minute bands.

Missing delay values are excluded from averages. The `/summary` API and dashboard use DuckDB to aggregate the cleaned full-year Parquet dataset, including top train and station delays, monthly delay trends, category averages, status counts, recurring route averages, reporting coverage, delay bands, and delay by stop sequence. The exact 365-day date range spans 13 calendar-month groups because its endpoints fall in partial February months. Train delays are first averaged by journey to prevent long routes from dominating; rare train/station/route results are excluded from rankings using minimum observation thresholds. The API returns HTTP 503 rather than showing demo records if the full dataset is not ready.
