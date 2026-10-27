from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_train_delays(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in records:
        delay = _safe_float(item.get("arrival_delay_min"))
        if delay is not None:
            grouped[str(item.get("train_number", "unknown"))].append(delay)

    results = []
    for train_number, delays in grouped.items():
        avg_delay = sum(delays) / len(delays)
        results.append({
            "label": train_number,
            "value": round(avg_delay, 2),
            "count": len(delays),
        })
    return sorted(results, key=lambda row: row["value"], reverse=True)[:10]


def summarize_station_delays(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in records:
        delay = _safe_float(item.get("arrival_delay_min"))
        if delay is not None:
            grouped[str(item.get("station_code", "unknown"))].append(delay)

    results = []
    for station, delays in grouped.items():
        avg_delay = sum(delays) / len(delays)
        results.append({
            "label": station,
            "value": round(avg_delay, 2),
            "count": len(delays),
        })
    return sorted(results, key=lambda row: row["value"], reverse=True)[:10]


def summarize_categories(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in records:
        delay = _safe_float(item.get("arrival_delay_min"))
        if delay is not None:
            grouped[str(item.get("category", "unknown"))].append(delay)

    results = []
    for category, delays in grouped.items():
        avg_delay = sum(delays) / len(delays)
        results.append({
            "label": category,
            "value": round(avg_delay, 2),
            "count": len(delays),
        })
    return sorted(results, key=lambda row: row["value"], reverse=True)


def summarize_coverage(records: Sequence[dict]) -> dict[str, float]:
    total = len(records)
    if total == 0:
        return {"reported": 0.0, "estimated": 0.0, "run_quality_avg": 0.0}

    reported = 0
    estimated = 0
    quality_values = []
    for item in records:
        if item.get("arrival_reported") is True:
            reported += 1
        if item.get("arrival_reported") is False:
            estimated += 1
        q = _safe_float(item.get("run_quality"))
        if q is not None:
            quality_values.append(q)

    return {
        "reported": round(reported / total * 100, 2),
        "estimated": round(estimated / total * 100, 2),
        "run_quality_avg": round(sum(quality_values) / len(quality_values), 4) if quality_values else 0.0,
    }


def build_analytics_payload(records: Iterable[dict]) -> dict:
    rows = list(records)
    return {
        "trains": summarize_train_delays(rows),
        "stations": summarize_station_delays(rows),
        "categories": summarize_categories(rows),
        "coverage": summarize_coverage(rows),
    }
