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


def _label(value) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _journey_key(item: dict) -> tuple[str, str]:
    return (
        _label(item.get("train_number")) or "unknown",
        _label(item.get("start_date")) or "",
    )


def summarize_train_delays(records: Sequence[dict]) -> list[dict]:
    journeys: dict[tuple[str, str], list[float]] = defaultdict(list)
    for item in records:
        delay = _safe_float(item.get("arrival_delay_min"))
        if delay is not None:
            journeys[_journey_key(item)].append(delay)

    grouped: dict[str, list[float]] = defaultdict(list)
    for (train_number, _), delays in journeys.items():
        grouped[train_number].append(sum(delays) / len(delays))

    results = [
        {
            "label": train_number,
            "value": round(sum(journey_averages) / len(journey_averages), 2),
            "count": len(journey_averages),
        }
        for train_number, journey_averages in grouped.items()
    ]
    return sorted(results, key=lambda row: row["value"], reverse=True)[:10]


def summarize_station_delays(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"arrival": [], "departure": []})
    for item in records:
        station = _label(item.get("station_code"))
        if station is None:
            continue
        for field, key in (("arrival_delay_min", "arrival"), ("departure_delay_min", "departure")):
            delay = _safe_float(item.get(field))
            if delay is not None:
                grouped[station][key].append(delay)

    results = []
    for station, delays in grouped.items():
        arrival = delays["arrival"]
        departure = delays["departure"]
        if not arrival and not departure:
            continue
        results.append({
            "label": station,
            "value": round(sum(arrival) / len(arrival), 2) if arrival else None,
            "departure_value": round(sum(departure) / len(departure), 2) if departure else None,
            "count": len(arrival) if arrival else len(departure),
            "departure_count": len(departure),
        })
    return sorted(
        results,
        key=lambda row: row["value"] if row["value"] is not None else float("-inf"),
        reverse=True,
    )[:10]


def summarize_categories(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"arrival": [], "departure": []})
    for item in records:
        category = _label(item.get("category"))
        if category is None:
            continue
        for field, key in (("arrival_delay_min", "arrival"), ("departure_delay_min", "departure")):
            delay = _safe_float(item.get(field))
            if delay is not None:
                grouped[category][key].append(delay)

    results = []
    for category, delays in grouped.items():
        arrival = delays["arrival"]
        departure = delays["departure"]
        results.append({
            "label": category,
            "value": round(sum(arrival) / len(arrival), 2) if arrival else None,
            "departure_value": round(sum(departure) / len(departure), 2) if departure else None,
            "count": len(arrival) if arrival else len(departure),
            "departure_count": len(departure),
        })
    return sorted(results, key=lambda row: row["value"] if row["value"] is not None else float("-inf"), reverse=True)


def summarize_date_trends(records: Sequence[dict]) -> list[dict]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: {"arrival": [], "departure": []})
    for item in records:
        date = _label(item.get("start_date"))
        if date is None:
            continue
        for field, key in (("arrival_delay_min", "arrival"), ("departure_delay_min", "departure")):
            delay = _safe_float(item.get(field))
            if delay is not None:
                grouped[date][key].append(delay)

    return [
        {
            "label": date,
            "value": round(sum(delays["arrival"]) / len(delays["arrival"]), 2) if delays["arrival"] else None,
            "departure_value": round(sum(delays["departure"]) / len(delays["departure"]), 2)
            if delays["departure"] else None,
            "count": len(delays["arrival"]) if delays["arrival"] else len(delays["departure"]),
            "departure_count": len(delays["departure"]),
        }
        for date, delays in sorted(grouped.items())
    ]


def summarize_status(records: Sequence[dict]) -> list[dict]:
    journeys: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for item in records:
        status = _label(item.get("status"))
        if status is not None:
            journeys[status].add(_journey_key(item))
    return [
        {"label": status, "value": len(keys), "count": len(keys)}
        for status, keys in sorted(journeys.items(), key=lambda entry: len(entry[1]), reverse=True)
    ]


def summarize_routes(records: Sequence[dict]) -> tuple[list[dict], list[dict]]:
    journeys: dict[tuple[str, str], list[tuple[int, str, float | None]]] = defaultdict(list)
    sequence_delays: dict[int, list[float]] = defaultdict(list)
    for item in records:
        station = _label(item.get("station_code"))
        sequence = item.get("seq")
        if station is None or sequence is None:
            continue
        try:
            sequence_number = int(sequence)
        except (TypeError, ValueError):
            continue
        delay = _safe_float(item.get("arrival_delay_min"))
        journeys[_journey_key(item)].append((sequence_number, station, delay))
        if delay is not None:
            sequence_delays[sequence_number].append(delay)

    route_groups: dict[str, list[float]] = defaultdict(list)
    route_counts: dict[str, int] = defaultdict(int)
    for stops in journeys.values():
        ordered_stops = sorted(stops, key=lambda stop: stop[0])
        route = " → ".join(station for _, station, _ in ordered_stops)
        if len(ordered_stops) < 2:
            continue
        route_counts[route] += 1
        observed_delays = [delay for _, _, delay in ordered_stops if delay is not None]
        if observed_delays:
            route_groups[route].append(sum(observed_delays) / len(observed_delays))

    routes = [
        {
            "label": route,
            "value": round(sum(delays) / len(delays), 2) if delays else None,
            "count": route_counts[route],
        }
        for route, delays in route_groups.items()
    ]
    routes.sort(key=lambda row: row["value"] if row["value"] is not None else float("-inf"), reverse=True)
    sequence = [
        {
            "label": str(position),
            "value": round(sum(delays) / len(delays), 2),
            "count": len(delays),
        }
        for position, delays in sorted(sequence_delays.items())
    ]
    return routes[:10], sequence


def summarize_coverage(records: Sequence[dict]) -> dict[str, float]:
    arrival_reported = arrival_known = departure_reported = departure_known = 0
    quality_values = []
    for item in records:
        if item.get("arrival_reported") is True:
            arrival_reported += 1
            arrival_known += 1
        elif item.get("arrival_reported") is False:
            arrival_known += 1
        if item.get("departure_reported") is True:
            departure_reported += 1
            departure_known += 1
        elif item.get("departure_reported") is False:
            departure_known += 1
        q = _safe_float(item.get("run_quality"))
        if q is not None:
            quality_values.append(q)

    arrival_pct = arrival_reported / arrival_known * 100 if arrival_known else 0.0
    departure_pct = departure_reported / departure_known * 100 if departure_known else 0.0
    return {
        "reported": round(arrival_pct, 2),
        "estimated": round(100 - arrival_pct, 2) if arrival_known else 0.0,
        "arrival_reported_pct": round(arrival_pct, 2),
        "departure_reported_pct": round(departure_pct, 2),
        "run_quality_avg": round(sum(quality_values) / len(quality_values), 4) if quality_values else 0.0,
    }


def build_analytics_payload(records: Iterable[dict]) -> dict:
    rows = list(records)
    routes, sequence = summarize_routes(rows)
    return {
        "trains": summarize_train_delays(rows),
        "stations": summarize_station_delays(rows),
        "categories": summarize_categories(rows),
        "dates": summarize_date_trends(rows),
        "statuses": summarize_status(rows),
        "routes": routes,
        "sequence": sequence,
        "coverage": summarize_coverage(rows),
        "totals": {
            "records": len(rows),
            "trains": len({_label(row.get("train_number")) for row in rows if _label(row.get("train_number"))}),
            "stations": len({_label(row.get("station_code")) for row in rows if _label(row.get("station_code"))}),
            "journeys": len({_journey_key(row) for row in rows}),
        },
    }
