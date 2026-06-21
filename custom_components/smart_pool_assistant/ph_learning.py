"""pH drift learning helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Callable

from .const import CONF_PH_DOWN_DOSAGE, CONF_PH_UP_DOSAGE, CONF_POOL_VOLUME


MEASUREMENTS_KEY = "ph_learning_measurements"
CORRECTIONS_KEY = "ph_learning_corrections"
MAX_STORED_ITEMS = 80
MIN_INTERVAL_HOURS = 3.0
MAX_INTERVAL_DAYS = 7.0
STABLE_DRIFT_THRESHOLD = 0.03


def record_ph_measurement(
    history: dict,
    measured_at: str | None,
    ph: float | int | None,
) -> None:
    """Store a deduplicated pH measurement for future learning."""
    if measured_at is None or ph is None:
        return

    try:
        value = round(float(ph), 3)
    except (TypeError, ValueError):
        return

    if value < 0 or value > 14:
        return

    measurements = history.get(MEASUREMENTS_KEY, [])
    measurements = measurements if isinstance(measurements, list) else []
    if any(item.get("raw_ts") == measured_at for item in measurements if isinstance(item, dict)):
        return

    measurements.append({"raw_ts": measured_at, "ph": value})
    history[MEASUREMENTS_KEY] = measurements[-MAX_STORED_ITEMS:]


def record_ph_correction(
    history: dict,
    corrected_at: str | None,
    correction_type: str,
    amount: float | int | None,
) -> None:
    """Store a deduplicated pH correction action for future learning."""
    if corrected_at is None or correction_type not in ("ph_plus", "ph_minus") or amount is None:
        return

    try:
        value = round(float(amount), 3)
    except (TypeError, ValueError):
        return

    if value <= 0:
        return

    corrections = history.get(CORRECTIONS_KEY, [])
    corrections = corrections if isinstance(corrections, list) else []
    if any(item.get("raw_ts") == corrected_at for item in corrections if isinstance(item, dict)):
        return

    corrections.append({"raw_ts": corrected_at, "type": correction_type, "amount": value})
    history[CORRECTIONS_KEY] = corrections[-MAX_STORED_ITEMS:]


def calculate_ph_learning(
    history: dict,
    conf: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> dict:
    """Calculate learned pH drift and stability statistics."""
    volume = _positive_float(conf.get(CONF_POOL_VOLUME), 0.0)
    ph_down_dosage = _positive_float(conf.get(CONF_PH_DOWN_DOSAGE), 0.0)
    ph_up_dosage = _positive_float(conf.get(CONF_PH_UP_DOSAGE), 0.0)

    measurements = _load_measurements(history, parse_ts, now)
    corrections = _load_corrections(history, parse_ts, now)
    intervals = _build_intervals(measurements, corrections, volume, ph_down_dosage, ph_up_dosage)

    last_24h = _period_stats(intervals, now, timedelta(hours=24))
    last_7d = _period_stats(intervals, now, timedelta(days=7))
    last_14d = _period_stats(intervals, now, timedelta(days=14))

    avg_drift = last_14d["average_daily_drift"]
    prediction_quality = _prediction_quality(intervals)
    sample_count = last_14d["samples"]
    trend = _trend(avg_drift, sample_count)

    if sample_count < 3:
        stability = "learning"
    elif prediction_quality >= 4 and trend == "stable":
        stability = "stable"
    elif prediction_quality >= 3:
        stability = "variable"
    else:
        stability = "unstable"

    return {
        "ph_drift_24h": last_24h["average_daily_drift"],
        "ph_drift_7d": last_7d["average_daily_drift"],
        "ph_drift_14d": avg_drift,
        "ph_prediction_quality": prediction_quality,
        "ph_stability": stability,
        "ph_trend": trend,
        "ph_stability_attributes": {
            "period": "14d",
            "average_daily_drift": avg_drift,
            "min_daily_drift": last_14d["min_daily_drift"],
            "max_daily_drift": last_14d["max_daily_drift"],
            "samples": sample_count,
            "prediction_quality": prediction_quality,
            "prediction_quality_stars": _quality_stars(prediction_quality),
            "trend": trend,
            "learning_phase": sample_count < 3,
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
            value = float(item.get("ph"))
        except (TypeError, ValueError):
            value = -1.0
        if dt and dt >= cutoff and 0 <= value <= 14:
            result.append({"dt": dt, "ph": value})
    result.sort(key=lambda item: item["dt"])
    return result


def _load_corrections(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=21)
    result = []
    for item in history.get(CORRECTIONS_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        amount = _positive_float(item.get("amount"), 0.0)
        correction_type = item.get("type")
        if dt and dt >= cutoff and amount > 0 and correction_type in ("ph_plus", "ph_minus"):
            result.append({"dt": dt, "type": correction_type, "amount": amount})
    result.sort(key=lambda item: item["dt"])
    return result


def _build_intervals(
    measurements: list[dict],
    corrections: list[dict],
    volume: float,
    ph_down_dosage: float,
    ph_up_dosage: float,
) -> list[dict]:
    intervals = []
    if volume <= 0:
        return intervals

    for previous, current in zip(measurements, measurements[1:]):
        hours = (current["dt"] - previous["dt"]).total_seconds() / 3600.0
        if hours < MIN_INTERVAL_HOURS or hours > MAX_INTERVAL_DAYS * 24:
            continue

        correction_effect = sum(
            _correction_effect(correction, volume, ph_down_dosage, ph_up_dosage)
            for correction in corrections
            if previous["dt"] < correction["dt"] <= current["dt"]
        )
        observed_change = current["ph"] - previous["ph"]
        natural_drift = observed_change - correction_effect
        daily_drift = natural_drift / (hours / 24.0)

        if abs(daily_drift) > 1.0:
            continue

        intervals.append({
            "end": current["dt"],
            "daily_drift": round(daily_drift, 3),
        })

    return intervals


def _correction_effect(correction: dict, volume: float, ph_down_dosage: float, ph_up_dosage: float) -> float:
    amount = correction["amount"]
    if correction["type"] == "ph_minus" and ph_down_dosage > 0:
        factor = ph_down_dosage / 10.0 / 0.2
        return -(amount / (factor * volume))
    if correction["type"] == "ph_plus" and ph_up_dosage > 0:
        factor = ph_up_dosage / 10.0 / 0.1
        return amount / (factor * volume)
    return 0.0


def _period_stats(intervals: list[dict], now: datetime, period: timedelta) -> dict:
    cutoff = now - period
    values = [item["daily_drift"] for item in intervals if item["end"] >= cutoff]
    if not values:
        return {
            "average_daily_drift": None,
            "min_daily_drift": None,
            "max_daily_drift": None,
            "samples": 0,
        }

    return {
        "average_daily_drift": round(mean(values), 3),
        "min_daily_drift": round(min(values), 3),
        "max_daily_drift": round(max(values), 3),
        "samples": len(values),
    }


def _prediction_quality(intervals: list[dict]) -> int:
    recent = [item["daily_drift"] for item in intervals[-8:]]
    if len(recent) < 3:
        return 0

    avg = mean(recent)
    mean_absolute_error = mean(abs(value - avg) for value in recent)
    if mean_absolute_error < 0.03:
        return 5
    if mean_absolute_error < 0.06:
        return 4
    if mean_absolute_error < 0.1:
        return 3
    if mean_absolute_error < 0.15:
        return 2
    return 1


def _trend(avg_drift: float | None, sample_count: int) -> str:
    if sample_count < 3 or avg_drift is None:
        return "learning"
    if avg_drift > STABLE_DRIFT_THRESHOLD:
        return "rising"
    if avg_drift < -STABLE_DRIFT_THRESHOLD:
        return "falling"
    return "stable"


def _quality_stars(quality: int) -> str:
    quality = max(0, min(5, int(quality or 0)))
    return "*" * quality + "-" * (5 - quality)
