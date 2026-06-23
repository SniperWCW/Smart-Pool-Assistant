"""Chlorine consumption learning helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean
from typing import Callable

from .const import CONF_CHLOR_CONTENT, CONF_CHLOR_MIN, CONF_CHLOR_TARGET, CONF_POOL_VOLUME
from .maintenance import CONTEXT_HISTORY_KEY


MEASUREMENTS_KEY = "chlor_learning_measurements"
DOSES_KEY = "chlor_learning_doses"
MAX_STORED_ITEMS = 120
MIN_INTERVAL_HOURS = 3.0
MAX_INTERVAL_DAYS = 7.0
MIN_DOSE_EFFECT_HOURS = 0.5
MAX_DOSE_EFFECT_HOURS = 48.0
DEFAULT_DAILY_LOSS = 0.8
DEFAULT_DOSE_FACTOR = 1.0
CRITICAL_LOW_CHLOR = 0.6
CONTEXT_OPEN_FACTOR = 0.35
CONTEXT_USAGE_NORMAL_FACTOR = 0.25
CONTEXT_USAGE_PARTY_FACTOR = 0.7


def record_chlor_measurement(
    history: dict,
    measured_at: str | None,
    chlorine: float | int | None,
    *,
    temperature: float | int | None = None,
    pool_covered: bool | None = None,
    usage_mode: str | None = None,
    uv_index: float | int | None = None,
    weather_condition: str | None = None,
    precipitation_probability: float | int | None = None,
    precipitation_amount: float | int | None = None,
    pump_runtime_hours_total: float | int | None = None,
    pump_active: bool | None = None,
) -> None:
    """Store a deduplicated chlorine measurement with context for learning."""
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

    measurements.append({
        "raw_ts": measured_at,
        "chlor": value,
        "temperature": _round_optional(temperature, 2),
        "pool_covered": _bool_optional(pool_covered),
        "usage_mode": _clean_usage_mode(usage_mode),
        "uv_index": _round_optional(uv_index, 2),
        "weather_condition": _clean_text(weather_condition),
        "precipitation_probability": _round_optional(precipitation_probability, 1),
        "precipitation_amount": _round_optional(precipitation_amount, 2),
        "pump_runtime_hours_total": _round_optional(pump_runtime_hours_total, 3),
        "pump_active": _bool_optional(pump_active),
    })
    history[MEASUREMENTS_KEY] = measurements[-MAX_STORED_ITEMS:]


def record_chlor_dose(
    history: dict,
    dosed_at: str | None,
    amount: float | int | None,
    *,
    temperature: float | int | None = None,
    pool_covered: bool | None = None,
    usage_mode: str | None = None,
    uv_index: float | int | None = None,
    weather_condition: str | None = None,
    precipitation_probability: float | int | None = None,
    precipitation_amount: float | int | None = None,
    pump_runtime_hours_total: float | int | None = None,
    pump_active: bool | None = None,
) -> None:
    """Store a deduplicated chlorine dose with context for learning."""
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

    doses.append({
        "raw_ts": dosed_at,
        "amount": value,
        "temperature": _round_optional(temperature, 2),
        "pool_covered": _bool_optional(pool_covered),
        "usage_mode": _clean_usage_mode(usage_mode),
        "uv_index": _round_optional(uv_index, 2),
        "weather_condition": _clean_text(weather_condition),
        "precipitation_probability": _round_optional(precipitation_probability, 1),
        "precipitation_amount": _round_optional(precipitation_amount, 2),
        "pump_runtime_hours_total": _round_optional(pump_runtime_hours_total, 3),
        "pump_active": _bool_optional(pump_active),
    })
    history[DOSES_KEY] = doses[-MAX_STORED_ITEMS:]


def calculate_chlorine_learning(
    history: dict,
    conf: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
    *,
    current_chlorine: float | None = None,
    current_temperature: float | None = None,
    pool_covered: bool | None = None,
    usage_mode: str | None = None,
    weather_today: dict | None = None,
    pump_active: bool | None = None,
) -> dict:
    """Calculate learned chlorine consumption, dose factor and forecast."""
    volume = _positive_float(conf.get(CONF_POOL_VOLUME), 0.0)
    chlor_content = _positive_float(conf.get(CONF_CHLOR_CONTENT), 0.56) or 0.56
    chlor_min = _chlor_min_from_conf(conf)

    measurements = _load_measurements(history, parse_ts, now)
    doses = _load_doses(history, parse_ts, now)
    context_events = _load_context_events(history, parse_ts, now)
    intervals = _build_intervals(measurements, doses, volume, chlor_content, context_events)

    last_24h = _period_stats(intervals, now, timedelta(hours=24))
    last_7d = _period_stats(intervals, now, timedelta(days=7))
    last_14d = _period_stats(intervals, now, timedelta(days=14))
    last_14d_context = _period_stats(intervals, now, timedelta(days=14), value_key="context_adjusted_daily_loss")

    avg_loss = last_14d["average_daily_loss"]
    factor = round(avg_loss / DEFAULT_DAILY_LOSS, 2) if avg_loss is not None else None
    prediction_quality = _prediction_quality(intervals)
    context_prediction_quality = _prediction_quality(intervals, value_key="context_adjusted_daily_loss")
    quality_stars = _quality_stars(prediction_quality)
    context_quality_stars = _quality_stars(context_prediction_quality)
    sample_count = last_14d["samples"]

    if sample_count < 3:
        stability = "learning"
    elif context_prediction_quality >= 4:
        stability = "stable"
    elif context_prediction_quality >= 3:
        stability = "variable"
    else:
        stability = "unstable"

    baseline_daily_loss = avg_loss if avg_loss is not None else DEFAULT_DAILY_LOSS
    dose_effects = _build_dose_effects(measurements, doses, volume, chlor_content, baseline_daily_loss)
    dose_factor_stats = _dose_factor_stats(dose_effects, chlor_content)

    forecast = calculate_chlorine_forecast(
        current_chlorine=current_chlorine,
        chlor_min=chlor_min,
        current_temperature=current_temperature,
        pool_covered=pool_covered,
        usage_mode=usage_mode,
        weather_today=weather_today,
        pump_active=pump_active,
        intervals=intervals,
        avg_daily_loss=avg_loss,
        prediction_quality=prediction_quality,
    )

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
            "context_prediction_quality": context_prediction_quality,
            "context_prediction_quality_stars": context_quality_stars,
            "context_average_daily_loss": last_14d_context["average_daily_loss"],
            "context_min_daily_loss": last_14d_context["min_daily_loss"],
            "context_max_daily_loss": last_14d_context["max_daily_loss"],
            "personal_chlor_factor": factor,
            "learning_phase": sample_count < 3,
            "baseline_daily_loss": DEFAULT_DAILY_LOSS,
            "personal_dose_factor": dose_factor_stats["personal_chlor_dose_factor"],
            "dose_factor_samples": dose_factor_stats["samples"],
            "average_open_ratio": _average_interval_value(intervals, "open_ratio"),
            "average_covered_ratio": _average_interval_value(intervals, "covered_ratio"),
            "average_usage_none_ratio": _average_interval_value(intervals, "usage_none_ratio"),
            "average_usage_normal_ratio": _average_interval_value(intervals, "usage_normal_ratio"),
            "average_usage_party_ratio": _average_interval_value(intervals, "usage_party_ratio"),
        },
        **dose_factor_stats,
        **forecast,
    }


def calculate_chlorine_forecast(
    *,
    current_chlorine: float | None,
    chlor_min: float,
    current_temperature: float | None,
    pool_covered: bool | None,
    usage_mode: str | None,
    weather_today: dict | None,
    pump_active: bool | None,
    intervals: list[dict],
    avg_daily_loss: float | None,
    prediction_quality: int,
) -> dict:
    """Forecast chlorine decay until warning thresholds are reached."""
    if current_chlorine is None:
        return _empty_forecast("no_measurement")

    current_chlorine = float(current_chlorine)
    if current_chlorine <= 0:
        return _empty_forecast("no_measurement")

    usable_intervals = [item for item in intervals if item.get("daily_loss") is not None]
    if len(usable_intervals) < 3:
        return _empty_forecast("learning")

    weighted_loss, basis_count = _weighted_context_daily_loss(
        usable_intervals=usable_intervals,
        current_temperature=current_temperature,
        pool_covered=pool_covered,
        usage_mode=usage_mode,
        uv_index=_weather_float(weather_today, "uv_index"),
        rain_probability=_weather_float(weather_today, "precipitation_probability"),
        rain_amount=_weather_float(weather_today, "precipitation_amount"),
        pump_active=pump_active,
    )
    if weighted_loss is None:
        weighted_loss = avg_daily_loss

    if weighted_loss is None or weighted_loss <= 0:
        return _empty_forecast("insufficient")

    hourly_loss = weighted_loss / 24.0
    hours_to_min = _hours_until_threshold(current_chlorine, chlor_min, hourly_loss)
    hours_to_critical = _hours_until_threshold(current_chlorine, CRITICAL_LOW_CHLOR, hourly_loss)
    basis = "similar_intervals" if basis_count >= 3 else "14d_average"
    confidence = _forecast_confidence_label(prediction_quality, basis_count)
    message = _build_forecast_message(
        current_chlorine=current_chlorine,
        chlor_min=chlor_min,
        hours_to_min=hours_to_min,
        hours_to_critical=hours_to_critical,
        confidence=confidence,
    )

    return {
        "chlor_forecast_daily_loss": round(weighted_loss, 2),
        "chlor_forecast_hourly_loss": round(hourly_loss, 3),
        "chlor_hours_to_min": hours_to_min,
        "chlor_hours_to_critical_low": hours_to_critical,
        "chlor_forecast_threshold_min": round(chlor_min, 2),
        "chlor_forecast_threshold_critical_low": CRITICAL_LOW_CHLOR,
        "chlor_forecast_confidence": confidence,
        "chlor_forecast_basis": basis,
        "chlor_forecast_message": message,
        "chlor_forecast_attributes": {
            "basis": basis,
            "matching_intervals": basis_count,
            "prediction_quality": prediction_quality,
            "predicted_daily_loss": round(weighted_loss, 2),
            "predicted_hourly_loss": round(hourly_loss, 3),
            "current_chlorine": round(current_chlorine, 2),
            "threshold_min": round(chlor_min, 2),
            "threshold_critical_low": CRITICAL_LOW_CHLOR,
        },
    }


def _positive_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _round_optional(value: object, digits: int) -> float | None:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _bool_optional(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _clean_usage_mode(value: object) -> str | None:
    if isinstance(value, str) and value in {"none", "normal", "party"}:
        return value
    return None


def _clean_text(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _chlor_min_from_conf(conf: dict) -> float:
    fallback = _positive_float(conf.get(CONF_CHLOR_TARGET), 1.5)
    return _positive_float(conf.get(CONF_CHLOR_MIN), fallback)


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
            result.append({
                "dt": dt,
                "chlor": value,
                "temperature": _round_optional(item.get("temperature"), 2),
                "pool_covered": _bool_optional(item.get("pool_covered")),
                "usage_mode": _clean_usage_mode(item.get("usage_mode")),
                "uv_index": _round_optional(item.get("uv_index"), 2),
                "weather_condition": _clean_text(item.get("weather_condition")),
                "precipitation_probability": _round_optional(item.get("precipitation_probability"), 1),
                "precipitation_amount": _round_optional(item.get("precipitation_amount"), 2),
                "pump_runtime_hours_total": _round_optional(item.get("pump_runtime_hours_total"), 3),
                "pump_active": _bool_optional(item.get("pump_active")),
            })
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
            result.append({
                "dt": dt,
                "amount": amount,
                "temperature": _round_optional(item.get("temperature"), 2),
                "pool_covered": _bool_optional(item.get("pool_covered")),
                "usage_mode": _clean_usage_mode(item.get("usage_mode")),
                "uv_index": _round_optional(item.get("uv_index"), 2),
                "weather_condition": _clean_text(item.get("weather_condition")),
                "precipitation_probability": _round_optional(item.get("precipitation_probability"), 1),
                "precipitation_amount": _round_optional(item.get("precipitation_amount"), 2),
                "pump_runtime_hours_total": _round_optional(item.get("pump_runtime_hours_total"), 3),
                "pump_active": _bool_optional(item.get("pump_active")),
            })
    result.sort(key=lambda item: item["dt"])
    return result


def _load_context_events(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=21)
    result = []
    for item in history.get(CONTEXT_HISTORY_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        if dt and dt >= cutoff:
            result.append({
                "dt": dt,
                "pool_covered": _bool_optional(item.get("pool_covered")),
                "usage_mode": _clean_usage_mode(item.get("usage_mode")),
            })
    result.sort(key=lambda item: item["dt"])
    return result


def _build_intervals(
    measurements: list[dict],
    doses: list[dict],
    volume: float,
    chlor_content: float,
    context_events: list[dict],
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

        pump_runtime_delta = _pump_runtime_delta(previous, current)
        context_ratios = _context_ratios(previous, current, context_events)
        context_adjusted_loss = _context_adjusted_daily_loss(
            round(daily_loss, 3),
            context_ratios,
        )
        intervals.append({
            "end": current["dt"],
            "daily_loss": round(daily_loss, 3),
            "hours": round(hours, 2),
            "temperature": _average_numeric(previous.get("temperature"), current.get("temperature")),
            "pool_covered": _dominant_covered_state(context_ratios),
            "usage_mode": _dominant_usage_mode(context_ratios),
            "uv_index": _average_numeric(previous.get("uv_index"), current.get("uv_index")),
            "precipitation_probability": _max_numeric(
                previous.get("precipitation_probability"),
                current.get("precipitation_probability"),
            ),
            "precipitation_amount": _max_numeric(
                previous.get("precipitation_amount"),
                current.get("precipitation_amount"),
            ),
            "pump_runtime_hours": pump_runtime_delta,
            "pump_runtime_ratio": round(pump_runtime_delta / hours, 3) if pump_runtime_delta is not None else None,
            "covered_ratio": context_ratios["covered_ratio"],
            "open_ratio": context_ratios["open_ratio"],
            "usage_none_ratio": context_ratios["usage_none_ratio"],
            "usage_normal_ratio": context_ratios["usage_normal_ratio"],
            "usage_party_ratio": context_ratios["usage_party_ratio"],
            "context_adjusted_daily_loss": context_adjusted_loss,
        })

    return intervals


def _build_dose_effects(
    measurements: list[dict],
    doses: list[dict],
    volume: float,
    chlor_content: float,
    baseline_daily_loss: float,
) -> list[dict]:
    if volume <= 0:
        return []

    effects = []
    for index, dose in enumerate(doses):
        previous = _latest_measurement_before(measurements, dose["dt"])
        following = _first_measurement_after(measurements, dose["dt"])
        next_dose = doses[index + 1] if index + 1 < len(doses) else None

        if previous is None or following is None:
            continue
        if next_dose and next_dose["dt"] <= following["dt"]:
            continue

        hours = (following["dt"] - previous["dt"]).total_seconds() / 3600.0
        if hours < MIN_DOSE_EFFECT_HOURS or hours > MAX_DOSE_EFFECT_HOURS:
            continue

        theoretical_increase = dose["amount"] * chlor_content / volume
        if theoretical_increase <= 0:
            continue

        corrected_increase = following["chlor"] - previous["chlor"] + baseline_daily_loss * (hours / 24.0)
        dose_factor = corrected_increase / theoretical_increase
        if dose_factor <= 0.2 or dose_factor > 1.8:
            continue

        effects.append({
            "end": following["dt"],
            "hours": round(hours, 2),
            "dose_amount": round(dose["amount"], 2),
            "theoretical_increase": round(theoretical_increase, 3),
            "corrected_increase": round(corrected_increase, 3),
            "dose_factor": round(dose_factor, 3),
        })

    return effects


def _period_stats(
    intervals: list[dict],
    now: datetime,
    period: timedelta,
    *,
    value_key: str = "daily_loss",
) -> dict:
    cutoff = now - period
    values = [
        item[value_key]
        for item in intervals
        if item["end"] >= cutoff and item.get(value_key) is not None
    ]
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


def _dose_factor_stats(effects: list[dict], chlor_content: float) -> dict:
    values = [item["dose_factor"] for item in effects]
    if not values:
        return {
            "samples": 0,
            "personal_chlor_dose_factor": None,
            "effective_chlor_content": round(chlor_content, 3),
            "chlor_dose_prediction_quality": 0,
            "chlor_dose_factor_attributes": {
                "samples": 0,
                "average_factor": None,
                "min_factor": None,
                "max_factor": None,
                "quality_stars": "-----",
                "learning_phase": True,
            },
        }

    average_factor = round(mean(values), 2)
    min_factor = round(min(values), 2)
    max_factor = round(max(values), 2)
    quality = _prediction_quality_from_values(values)
    return {
        "samples": len(values),
        "personal_chlor_dose_factor": average_factor,
        "effective_chlor_content": round(chlor_content * average_factor, 3),
        "chlor_dose_prediction_quality": quality,
        "chlor_dose_factor_attributes": {
            "samples": len(values),
            "average_factor": average_factor,
            "min_factor": min_factor,
            "max_factor": max_factor,
            "quality_stars": _quality_stars(quality),
            "learning_phase": len(values) < 2,
            "last_confirmed_effect": effects[-1]["corrected_increase"],
            "last_confirmed_dose": effects[-1]["dose_amount"],
        },
    }


def _prediction_quality(intervals: list[dict], *, value_key: str = "daily_loss") -> int:
    recent = [
        item[value_key]
        for item in intervals[-8:]
        if item.get(value_key) is not None
    ]
    return _prediction_quality_from_values(recent)


def _prediction_quality_from_values(values: list[float]) -> int:
    if len(values) < 3:
        return 0

    avg = mean(values)
    if avg <= 0:
        return 0

    mean_absolute_error = mean(abs(value - avg) for value in values)
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


def _average_numeric(first: float | None, second: float | None) -> float | None:
    values = [value for value in (first, second) if value is not None]
    if not values:
        return None
    return round(mean(values), 2)


def _max_numeric(first: float | None, second: float | None) -> float | None:
    values = [value for value in (first, second) if value is not None]
    if not values:
        return None
    return round(max(values), 2)


def _prefer_value(first: object, second: object) -> object:
    return first if first is not None else second


def _pump_runtime_delta(previous: dict, current: dict) -> float | None:
    previous_total = previous.get("pump_runtime_hours_total")
    current_total = current.get("pump_runtime_hours_total")
    if previous_total is None or current_total is None:
        return None
    delta = current_total - previous_total
    if delta < 0:
        return None
    return round(delta, 3)


def _context_ratios(previous: dict, current: dict, context_events: list[dict]) -> dict:
    start_dt = previous["dt"]
    end_dt = current["dt"]
    total_seconds = max((end_dt - start_dt).total_seconds(), 1.0)
    state = _context_state_at(
        start_dt,
        context_events,
        default_covered=_prefer_value(previous.get("pool_covered"), current.get("pool_covered")),
        default_usage=_prefer_value(previous.get("usage_mode"), current.get("usage_mode")) or "none",
    )
    covered_seconds = 0.0
    usage_seconds = {"none": 0.0, "normal": 0.0, "party": 0.0}
    cursor = start_dt

    for event in context_events:
        event_dt = event["dt"]
        if event_dt <= start_dt or event_dt >= end_dt:
            continue
        segment_seconds = (event_dt - cursor).total_seconds()
        if segment_seconds > 0:
            covered_seconds += _covered_seconds(segment_seconds, state["pool_covered"])
            _add_usage_seconds(usage_seconds, state["usage_mode"], segment_seconds)
        state = {
            "pool_covered": _prefer_value(event.get("pool_covered"), state["pool_covered"]),
            "usage_mode": _prefer_value(event.get("usage_mode"), state["usage_mode"]),
        }
        cursor = event_dt

    tail_seconds = (end_dt - cursor).total_seconds()
    if tail_seconds > 0:
        covered_seconds += _covered_seconds(tail_seconds, state["pool_covered"])
        _add_usage_seconds(usage_seconds, state["usage_mode"], tail_seconds)

    covered_ratio = round(covered_seconds / total_seconds, 3)
    open_ratio = round(max(0.0, 1.0 - covered_ratio), 3)
    return {
        "covered_ratio": covered_ratio,
        "open_ratio": open_ratio,
        "usage_none_ratio": round(usage_seconds["none"] / total_seconds, 3),
        "usage_normal_ratio": round(usage_seconds["normal"] / total_seconds, 3),
        "usage_party_ratio": round(usage_seconds["party"] / total_seconds, 3),
    }


def _context_state_at(
    dt: datetime,
    context_events: list[dict],
    *,
    default_covered: bool | None,
    default_usage: str | None,
) -> dict:
    state = {
        "pool_covered": True if default_covered is None else default_covered,
        "usage_mode": default_usage or "none",
    }
    for event in context_events:
        if event["dt"] > dt:
            break
        state = {
            "pool_covered": _prefer_value(event.get("pool_covered"), state["pool_covered"]),
            "usage_mode": _prefer_value(event.get("usage_mode"), state["usage_mode"]),
        }
    return state


def _covered_seconds(segment_seconds: float, pool_covered: bool | None) -> float:
    if pool_covered is True:
        return segment_seconds
    return 0.0


def _add_usage_seconds(target: dict[str, float], usage_mode: str | None, segment_seconds: float) -> None:
    usage_key = usage_mode if usage_mode in target else "none"
    target[usage_key] += segment_seconds


def _dominant_covered_state(context_ratios: dict) -> bool | None:
    covered_ratio = context_ratios.get("covered_ratio")
    open_ratio = context_ratios.get("open_ratio")
    if covered_ratio is None or open_ratio is None:
        return None
    return covered_ratio >= open_ratio


def _dominant_usage_mode(context_ratios: dict) -> str | None:
    usage_ratios = {
        "none": context_ratios.get("usage_none_ratio"),
        "normal": context_ratios.get("usage_normal_ratio"),
        "party": context_ratios.get("usage_party_ratio"),
    }
    valid_ratios = {key: value for key, value in usage_ratios.items() if value is not None}
    if not valid_ratios:
        return None
    return max(valid_ratios, key=valid_ratios.get)


def _context_adjusted_daily_loss(daily_loss: float, context_ratios: dict) -> float:
    context_multiplier = 1.0
    context_multiplier += float(context_ratios.get("open_ratio") or 0.0) * CONTEXT_OPEN_FACTOR
    context_multiplier += float(context_ratios.get("usage_normal_ratio") or 0.0) * CONTEXT_USAGE_NORMAL_FACTOR
    context_multiplier += float(context_ratios.get("usage_party_ratio") or 0.0) * CONTEXT_USAGE_PARTY_FACTOR
    return round(daily_loss / max(context_multiplier, 0.5), 3)


def _average_interval_value(intervals: list[dict], key: str) -> float | None:
    values = [float(item[key]) for item in intervals if item.get(key) is not None]
    if not values:
        return None
    return round(mean(values), 3)


def _latest_measurement_before(measurements: list[dict], dt: datetime) -> dict | None:
    for item in reversed(measurements):
        if item["dt"] <= dt:
            return item
    return None


def _first_measurement_after(measurements: list[dict], dt: datetime) -> dict | None:
    for item in measurements:
        if item["dt"] > dt:
            return item
    return None


def _weighted_context_daily_loss(
    *,
    usable_intervals: list[dict],
    current_temperature: float | None,
    pool_covered: bool | None,
    usage_mode: str | None,
    uv_index: float | None,
    rain_probability: float | None,
    rain_amount: float | None,
    pump_active: bool | None,
) -> tuple[float | None, int]:
    weighted_sum = 0.0
    total_weight = 0.0
    matches = 0

    for interval in usable_intervals[-12:]:
        weight = 1.0
        if current_temperature is not None and interval.get("temperature") is not None:
            weight *= max(0.35, 1.0 - abs(interval["temperature"] - current_temperature) / 12.0)

        interval_covered = interval.get("pool_covered")
        if pool_covered is not None and interval_covered is not None:
            weight *= 1.35 if interval_covered == pool_covered else 0.7

        interval_usage = interval.get("usage_mode")
        if usage_mode and interval_usage:
            weight *= 1.3 if interval_usage == usage_mode else 0.8

        interval_uv = interval.get("uv_index")
        if uv_index is not None and interval_uv is not None:
            weight *= max(0.4, 1.0 - abs(interval_uv - uv_index) / 8.0)

        if rain_probability is not None and interval.get("precipitation_probability") is not None:
            weight *= max(
                0.5,
                1.0 - abs(interval["precipitation_probability"] - rain_probability) / 100.0,
            )

        if rain_amount is not None and interval.get("precipitation_amount") is not None:
            weight *= max(0.6, 1.0 - abs(interval["precipitation_amount"] - rain_amount) / 20.0)

        interval_pump_ratio = interval.get("pump_runtime_ratio")
        if pump_active is not None and interval_pump_ratio is not None:
            expected_ratio = 1.0 if pump_active else 0.0
            weight *= max(0.6, 1.0 - abs(interval_pump_ratio - expected_ratio))

        if weight >= 0.75:
            matches += 1

        weighted_sum += interval["daily_loss"] * weight
        total_weight += weight

    if total_weight <= 0:
        return None, 0
    return weighted_sum / total_weight, matches


def _hours_until_threshold(current_chlorine: float, threshold: float, hourly_loss: float) -> float | None:
    if current_chlorine <= threshold:
        return 0.0
    if hourly_loss <= 0:
        return None
    return round((current_chlorine - threshold) / hourly_loss, 1)


def _forecast_confidence_label(prediction_quality: int, basis_count: int) -> str:
    if prediction_quality >= 4 and basis_count >= 4:
        return "high"
    if prediction_quality >= 3 and basis_count >= 2:
        return "medium"
    return "low"


def _build_forecast_message(
    *,
    current_chlorine: float,
    chlor_min: float,
    hours_to_min: float | None,
    hours_to_critical: float | None,
    confidence: str,
) -> str | None:
    if hours_to_critical is not None and 0 <= hours_to_critical <= 48:
        return f"In ca. {hours_to_critical:g} Stunden faellt Chlor unter {CRITICAL_LOW_CHLOR:.1f} mg/l."
    if hours_to_min is not None and 0 <= hours_to_min <= 48:
        return f"In ca. {hours_to_min:g} Stunden faellt Chlor unter {chlor_min:.1f} mg/l."
    if confidence == "low":
        return "Chlor-Prognose noch unsicher."
    if current_chlorine <= chlor_min:
        return "Chlor liegt bereits am oder unter dem Minimum."
    return None


def _empty_forecast(reason: str) -> dict:
    message = "Chlor-Prognose noch in Lernphase." if reason == "learning" else None
    return {
        "chlor_forecast_daily_loss": None,
        "chlor_forecast_hourly_loss": None,
        "chlor_hours_to_min": None,
        "chlor_hours_to_critical_low": None,
        "chlor_forecast_threshold_min": None,
        "chlor_forecast_threshold_critical_low": CRITICAL_LOW_CHLOR,
        "chlor_forecast_confidence": "learning" if reason == "learning" else "unknown",
        "chlor_forecast_basis": reason,
        "chlor_forecast_message": message,
        "chlor_forecast_attributes": {
            "basis": reason,
        },
    }


def _weather_float(weather_today: dict | None, key: str) -> float | None:
    if not isinstance(weather_today, dict):
        return None
    return _round_optional(weather_today.get(key), 2)
