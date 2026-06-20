"""Chlorine consumption learning helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Callable

from .const import CONF_CHLOR_CONTENT, CONF_POOL_VOLUME


MEASUREMENTS_KEY = "chlor_learning_measurements"
DOSES_KEY = "chlor_learning_doses"
MAX_STORED_ITEMS = 80
MIN_INTERVAL_HOURS = 3.0
MAX_INTERVAL_DAYS = 7.0
DEFAULT_DAILY_LOSS = 0.8


def record_chlor_measurement(
    history: dict,
    measured_at: str | None,
    chlorine: float | int | None,
) -> None:
    """Store a deduplicated chlorine measurement for future learning."""
    if measured_at is None or chlorine is None:
        return

    try:
        value = round(float(chlorine), 3)
    except (TypeError, ValueError):
        return

    if value < 0 or value > 20:
        return

    measurements = history.get(MEASUREMENTS_KEY, [])
    measurements = measurements if isinstance(measurements, list) else []
    if any(item.get("raw_ts") == measured_at for item in measurements if isinstance(item, dict)):
        return

    measurements.append({"raw_ts": measured_at, "chlor": value})
    history[MEASUREMENTS_KEY] = measurements[-MAX_STORED_ITEMS:]


def record_chlor_dose(
    history: dict,
    dosed_at: str | None,
    amount: float | int | None,
) -> None:
    """Store a deduplicated chlorine dose for future learning."""
    if dosed_at is None or amount is None:
        return

    try:
        value = round(float(amount), 3)
    except (TypeError, ValueError):
        return

    if value <= 0:
        return

    doses = history.get(DOSES_KEY, [])
    doses = doses if isinstance(doses, list) else []
    if any(item.get("raw_ts") == dosed_at for item in doses if isinstance(item, dict)):
        return

    doses.append({"raw_ts": dosed_at, "amount": value})
    history[DOSES_KEY] = doses[-MAX_STORED_ITEMS:]


def calculate_chlorine_learning(
    history: dict,
    conf: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> dict:
    """Calculate learned chlorine consumption and stability statistics."""
    volume = _positive_float(conf.get(CONF_POOL_VOLUME), 0.0)
    chlor_content = _positive_float(conf.get(CONF_CHLOR_CONTENT), 0.56) or 0.56

    measurements = _load_measurements(history, parse_ts, now)
    doses = _load_doses(history, parse_ts, now)
    intervals = _build_intervals(measurements, doses, volume, chlor_content)

    last_24h = _period_stats(intervals, now, timedelta(hours=24))
    last_7d = _period_stats(intervals, now, timedelta(days=7))
    last_14d = _period_stats(intervals, now, timedelta(days=14))

    avg_loss = last_14d["average_daily_loss"]
    factor = round(avg_loss / DEFAULT_DAILY_LOSS, 2) if avg_loss is not None else None
    prediction_quality = _prediction_quality(intervals)
    quality_stars = _quality_stars(prediction_quality)
    sample_count = last_14d["samples"]

    if sample_count < 3:
        stability = "learning"
    elif prediction_quality >= 4:
        stability = "stable"
    elif prediction_quality >= 3:
        stability = "variable"
    else:
        stability = "unstable"

    return {
        "chlor_consumption_24h": last_24h["average_daily_loss"],
        "chlor_consumption_7d": last_7d["average_daily_loss"],
        "chlor_consumption_14d": avg_loss,
        "personal_chlor_factor": factor,
        "chlor_prediction_quality": prediction_quality,
        "chlor_stability": stability,
        "chlor_stability_attributes": {
            "period": "14d",
            "average_daily_loss": avg_loss,
            "min_daily_loss": last_14d["min_daily_loss"],
            "max_daily_loss": last_14d["max_daily_loss"],
            "samples": sample_count,
            "prediction_quality": prediction_quality,
            "prediction_quality_stars": quality_stars,
            "personal_chlor_factor": factor,
            "learning_phase": sample_count < 3,
            "baseline_daily_loss": DEFAULT_DAILY_LOSS,
        },
    }


def _positive_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _load_measurements(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=21)
    result = []
    for item in history.get(MEASUREMENTS_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        try:
            value = float(item.get("chlor"))
        except (TypeError, ValueError):
            value = -1.0
        if dt and dt >= cutoff and 0 <= value <= 20:
            result.append({"dt": dt, "chlor": value})
    result.sort(key=lambda item: item["dt"])
    return result


def _load_doses(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=21)
    result = []
    for item in history.get(DOSES_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        amount = _positive_float(item.get("amount"), 0.0)
        if dt and dt >= cutoff and amount > 0:
            result.append({"dt": dt, "amount": amount})
    result.sort(key=lambda item: item["dt"])
    return result


def _build_intervals(
    measurements: list[dict],
    doses: list[dict],
    volume: float,
    chlor_content: float,
) -> list[dict]:
    intervals = []
    if volume <= 0:
        return intervals

    for previous, current in zip(measurements, measurements[1:]):
        hours = (current["dt"] - previous["dt"]).total_seconds() / 3600.0
        if hours < MIN_INTERVAL_HOURS or hours > MAX_INTERVAL_DAYS * 24:
            continue

        added = sum(
            dose["amount"] * chlor_content / volume
            for dose in doses
            if previous["dt"] < dose["dt"] <= current["dt"]
        )
        loss = previous["chlor"] + added - current["chlor"]
        daily_loss = loss / (hours / 24.0)

        if daily_loss < 0 or daily_loss > 5.0:
            continue

        intervals.append({
            "end": current["dt"],
            "daily_loss": round(daily_loss, 3),
        })

    return intervals


def _period_stats(intervals: list[dict], now: datetime, period: timedelta) -> dict:
    cutoff = now - period
    values = [item["daily_loss"] for item in intervals if item["end"] >= cutoff]
    if not values:
        return {
            "average_daily_loss": None,
            "min_daily_loss": None,
            "max_daily_loss": None,
            "samples": 0,
        }

    return {
        "average_daily_loss": round(mean(values), 2),
        "min_daily_loss": round(min(values), 2),
        "max_daily_loss": round(max(values), 2),
        "samples": len(values),
    }


def _prediction_quality(intervals: list[dict]) -> int:
    recent = [item["daily_loss"] for item in intervals[-8:]]
    if len(recent) < 3:
        return 0

    avg = mean(recent)
    if avg <= 0:
        return 0

    mean_absolute_error = mean(abs(value - avg) for value in recent)
    relative_error = mean_absolute_error / avg
    if relative_error < 0.1:
        return 5
    if relative_error < 0.2:
        return 4
    if relative_error < 0.35:
        return 3
    if relative_error < 0.5:
        return 2
    return 1


def _quality_stars(quality: int) -> str:
    quality = max(0, min(5, int(quality or 0)))
    return "*" * quality + "-" * (5 - quality)
