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
