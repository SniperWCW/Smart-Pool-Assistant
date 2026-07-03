"""CYA history and forecast helpers for Smart Pool Assistant."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from .chlorine_products import normalize_chlor_product_type, resolve_chlor_content
from .chlorine_learning import DOSES_KEY
from .const import CONF_CHLOR_CONTENT, CONF_CHLOR_PRODUCT_TYPE, CONF_POOL_VOLUME


MEASUREMENTS_KEY = "cya_learning_measurements"
WATER_EXCHANGES_KEY = "cya_water_exchanges"
MAX_STORED_ITEMS = 180
FORECAST_WINDOW_DAYS = 30
FORECAST_HORIZON_DAYS = 180
TARGET_THRESHOLD = 80.0
CRITICAL_THRESHOLD = 100.0
CYA_IDEAL_MAX = 50.0


def record_cya_measurement(
    history: dict,
    measured_at: str | None,
    cya: float | int | None,
) -> None:
    """Store a deduplicated CYA measurement for history and forecasting."""
    if measured_at is None or cya is None:
        return

    try:
        value = round(float(cya), 2)
    except (TypeError, ValueError):
        return

    if value < 0 or value > 500:
        return

    measurements = history.get(MEASUREMENTS_KEY, [])
    measurements = measurements if isinstance(measurements, list) else []
    if any(item.get("raw_ts") == measured_at for item in measurements if isinstance(item, dict)):
        return

    measurements.append({"raw_ts": measured_at, "cya": value})
    history[MEASUREMENTS_KEY] = measurements[-MAX_STORED_ITEMS:]


def normalize_water_exchange(
    liters: float | int | None,
    percent: float | int | None,
    pool_volume_liters: float | int | None,
) -> dict | None:
    """Normalize water exchange input to liters and percent."""
    volume_liters = _positive_float(pool_volume_liters, 0.0)
    liters_value = _positive_float(liters, 0.0)
    percent_value = _non_negative_float(percent)

    if percent_value is not None and percent_value > 100:
        percent_value = 100.0

    if liters_value <= 0 and (percent_value is None or percent_value <= 0):
        return None

    if liters_value <= 0 and percent_value is not None and volume_liters > 0:
        liters_value = volume_liters * (percent_value / 100.0)
    if (percent_value is None or percent_value <= 0) and liters_value > 0 and volume_liters > 0:
        percent_value = liters_value / volume_liters * 100.0

    if liters_value <= 0 or percent_value is None or percent_value <= 0:
        return None

    return {
        "liters": round(liters_value, 1),
        "percent": round(min(percent_value, 100.0), 2),
    }


def record_water_exchange(
    history: dict,
    exchanged_at: str | None,
    liters: float | int | None,
    percent: float | int | None,
    pool_volume_liters: float | int | None,
) -> None:
    """Store a deduplicated water exchange action."""
    normalized = normalize_water_exchange(liters, percent, pool_volume_liters)
    if exchanged_at is None or normalized is None:
        return

    exchanges = history.get(WATER_EXCHANGES_KEY, [])
    exchanges = exchanges if isinstance(exchanges, list) else []
    if any(item.get("raw_ts") == exchanged_at for item in exchanges if isinstance(item, dict)):
        return

    exchanges.append(
        {
            "raw_ts": exchanged_at,
            "liters": normalized["liters"],
            "percent": normalized["percent"],
        }
    )
    history[WATER_EXCHANGES_KEY] = exchanges[-MAX_STORED_ITEMS:]


def calculate_cya_learning(
    history: dict,
    conf: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
    *,
    current_cya: float | None = None,
) -> dict:
    """Calculate modeled current CYA and a simple forward forecast."""
    product_type = normalize_chlor_product_type(conf.get(CONF_CHLOR_PRODUCT_TYPE, "organic"))
    chlor_content = resolve_chlor_content(product_type, conf.get(CONF_CHLOR_CONTENT))
    volume_m3 = _positive_float(conf.get(CONF_POOL_VOLUME), 0.0)
    cya_ratio = _cya_ratio_for_product(product_type, chlor_content)

    measurements = _load_measurements(history, parse_ts, now)
    water_exchanges = _load_water_exchanges(history, parse_ts, now)
    chlor_doses = _load_chlor_doses(history, parse_ts, now)

    estimated_current, basis = _estimate_current_cya(
        measurements,
        water_exchanges,
        chlor_doses,
        current_cya=current_cya,
        volume_m3=volume_m3,
        chlor_content=chlor_content,
        cya_ratio=cya_ratio,
    )

    daily_exchange_fraction = _average_daily_exchange_fraction(water_exchanges, now, FORECAST_WINDOW_DAYS)
    daily_cya_input = _average_daily_cya_input(
        chlor_doses,
        now,
        FORECAST_WINDOW_DAYS,
        volume_m3,
        chlor_content,
        cya_ratio,
    )
    forecast = _simulate_forecast(
        now=now,
        current_cya=estimated_current,
        daily_exchange_fraction=daily_exchange_fraction,
        daily_cya_input=daily_cya_input,
        has_measurement=bool(measurements),
    )

    trend = _trend_label(forecast["estimated_daily_change"])
    latest_measurement = measurements[-1] if measurements else None
    latest_exchange = water_exchanges[-1] if water_exchanges else None
    recommended_exchange_percent, recommended_exchange_liters = _recommended_water_exchange(
        estimated_current,
        volume_m3,
        CYA_IDEAL_MAX,
    )
    message = _build_cya_status_message(
        estimated_current=estimated_current,
        latest_measurement=latest_measurement,
        recommended_exchange_percent=recommended_exchange_percent,
        recommended_exchange_liters=recommended_exchange_liters,
    )

    return {
        "cya_estimated_current": round(estimated_current, 2) if estimated_current is not None else current_cya,
        "cya_estimated_daily_change": forecast["estimated_daily_change"],
        "cya_days_to_80": forecast["days_to_80"],
        "cya_days_to_100": forecast["days_to_100"],
        "cya_forecast_confidence": forecast["confidence"],
        "cya_trend": trend,
        "cya_forecast_message": message,
        "cya_forecast_attributes": {
            "basis": basis,
            "trend": trend,
            "confidence": forecast["confidence"],
            "estimated_daily_change": forecast["estimated_daily_change"],
            "daily_exchange_percent": round(daily_exchange_fraction * 100.0, 3),
            "daily_stabilized_cya_input": round(daily_cya_input, 3),
            "cya_ratio_per_free_chlorine": round(cya_ratio, 3),
            "product_type": product_type,
            "latest_measured_cya": latest_measurement["cya"] if latest_measurement else None,
            "latest_measured_at": latest_measurement["raw_ts"] if latest_measurement else None,
            "latest_water_exchange_liters": latest_exchange["liters"] if latest_exchange else None,
            "latest_water_exchange_percent": latest_exchange["percent"] if latest_exchange else None,
            "recommended_exchange_liters": recommended_exchange_liters,
            "recommended_exchange_percent": recommended_exchange_percent,
            "recommended_target_cya": CYA_IDEAL_MAX,
            "recent_measurements": [
                {"raw_ts": item["raw_ts"], "cya": item["cya"]}
                for item in measurements[-6:]
            ],
        },
    }


def _estimate_current_cya(
    measurements: list[dict],
    water_exchanges: list[dict],
    chlor_doses: list[dict],
    *,
    current_cya: float | None,
    volume_m3: float,
    chlor_content: float,
    cya_ratio: float,
) -> tuple[float | None, str]:
    if measurements:
        latest_measurement = measurements[-1]
        modeled = float(latest_measurement["cya"])
        since_dt = latest_measurement["dt"]
        basis = "last_measurement_plus_history"
    elif current_cya is not None:
        modeled = float(current_cya)
        since_dt = None
        basis = "current_measurement_only"
    else:
        return None, "no_measurement"

    events: list[dict] = []
    for item in chlor_doses:
        if since_dt is None or item["dt"] > since_dt:
            events.append({"dt": item["dt"], "type": "dose", **item})
    for item in water_exchanges:
        if since_dt is None or item["dt"] > since_dt:
            events.append({"dt": item["dt"], "type": "exchange", **item})
    events.sort(key=lambda item: item["dt"])

    for item in events:
        if item["type"] == "dose":
            modeled += _dose_to_cya_ppm(item["amount"], volume_m3, chlor_content, cya_ratio)
        elif item["type"] == "exchange":
            modeled *= max(0.0, 1.0 - (item["percent"] / 100.0))

    return round(max(modeled, 0.0), 2), basis


def _average_daily_exchange_fraction(
    exchanges: list[dict],
    now: datetime,
    window_days: int,
) -> float:
    cutoff = now - timedelta(days=window_days)
    fractions = [item["percent"] / 100.0 for item in exchanges if item["dt"] >= cutoff]
    return sum(fractions) / window_days if fractions else 0.0


def _average_daily_cya_input(
    doses: list[dict],
    now: datetime,
    window_days: int,
    volume_m3: float,
    chlor_content: float,
    cya_ratio: float,
) -> float:
    if volume_m3 <= 0 or cya_ratio <= 0:
        return 0.0

    cutoff = now - timedelta(days=window_days)
    total = sum(
        _dose_to_cya_ppm(item["amount"], volume_m3, chlor_content, cya_ratio)
        for item in doses
        if item["dt"] >= cutoff
    )
    return total / window_days if total > 0 else 0.0


def _simulate_forecast(
    *,
    now: datetime,
    current_cya: float | None,
    daily_exchange_fraction: float,
    daily_cya_input: float,
    has_measurement: bool,
) -> dict:
    if current_cya is None:
        return {
            "estimated_daily_change": None,
            "days_to_80": None,
            "days_to_100": None,
            "confidence": "learning",
            "message": "Keine CYA-Prognose verf\u00fcgbar.",
        }

    modeled = float(current_cya)
    next_day = modeled * (1.0 - daily_exchange_fraction) + daily_cya_input
    estimated_daily_change = round(next_day - modeled, 3)

    if not has_measurement:
        return {
            "estimated_daily_change": estimated_daily_change,
            "days_to_80": None,
            "days_to_100": None,
            "confidence": "learning",
            "message": "CYA-Prognose lernt noch: erster Messwert vorhanden, mehr Verlauf n\u00f6tig.",
        }

    if daily_exchange_fraction <= 0 and daily_cya_input <= 0:
        return {
            "estimated_daily_change": estimated_daily_change,
            "days_to_80": None,
            "days_to_100": None,
            "confidence": "low",
            "message": "Ohne dokumentierten Wasserwechsel oder stabilisierte Chlorzugaben bleibt CYA voraussichtlich weitgehend stabil.",
        }

    days_to_80 = None
    days_to_100 = None
    value = modeled
    crossed_above_100 = value < CRITICAL_THRESHOLD
    crossed_below_80 = value > TARGET_THRESHOLD

    for day in range(1, FORECAST_HORIZON_DAYS + 1):
        value = value * (1.0 - daily_exchange_fraction) + daily_cya_input
        if days_to_80 is None and crossed_below_80 and value <= TARGET_THRESHOLD:
            days_to_80 = day
        if days_to_100 is None and crossed_above_100 and value >= CRITICAL_THRESHOLD:
            days_to_100 = day

    confidence = "high" if daily_exchange_fraction > 0 else "medium" if daily_cya_input > 0 else "low"
    return {
        "estimated_daily_change": estimated_daily_change,
        "days_to_80": days_to_80,
        "days_to_100": days_to_100,
        "confidence": confidence,
        "message": _build_forecast_message(now, modeled, estimated_daily_change, days_to_80, days_to_100),
    }


def _build_forecast_message(
    now: datetime,
    current_cya: float,
    estimated_daily_change: float | None,
    days_to_80: int | None,
    days_to_100: int | None,
) -> str:
    if days_to_80 is not None:
        target_date = (now + timedelta(days=days_to_80)).strftime("%d.%m.")
        return f"Bei aktuellem Verlauf voraussichtlich unter 80 ppm ab {target_date}."
    if days_to_100 is not None:
        target_date = (now + timedelta(days=days_to_100)).strftime("%d.%m.")
        return f"Bei aktuellem Verlauf voraussichtlich \u00fcber 100 ppm ab {target_date}."
    if estimated_daily_change is None:
        return "Keine CYA-Prognose verf\u00fcgbar."
    if abs(estimated_daily_change) < 0.1:
        return (
            f"CYA bleibt bei aktuellem Verlauf voraussichtlich nahe {current_cya:.0f} ppm "
            "und aendert sich im Modell aktuell kaum."
        )
    if estimated_daily_change < 0:
        return (
            f"Das Modell erwartet aktuell netto etwa {abs(estimated_daily_change):.2f} ppm/Tag weniger CYA, "
            "typischerweise durch dokumentierten Wasserwechsel."
        )
    return (
        f"Das Modell erwartet aktuell netto etwa {estimated_daily_change:.2f} ppm/Tag mehr CYA, "
        "typischerweise durch stabilisierte Chlorzugaben."
    )


def _build_cya_status_message(
    *,
    estimated_current: float | None,
    latest_measurement: dict | None,
    recommended_exchange_percent: float | None,
    recommended_exchange_liters: float | None,
) -> str:
    if latest_measurement is not None:
        measured_value = latest_measurement["cya"]
        measured_date = latest_measurement["dt"].strftime("%d.%m.%Y")
        measurement_text = f"Letzter CYA-Messwert: {measured_value:.1f} ppm am {measured_date}."
    elif estimated_current is not None:
        measurement_text = f"Aktueller CYA-Wert: {estimated_current:.1f} ppm."
    else:
        return "Kein CYA-Messwert vorhanden."

    if estimated_current is None or estimated_current <= CYA_IDEAL_MAX:
        return measurement_text

    if recommended_exchange_percent is None or recommended_exchange_liters is None:
        return f"CYA zu hoch. Teilwasserwechsel einplanen. {measurement_text}"

    return (
        f"CYA zu hoch: f\u00fcr etwa {CYA_IDEAL_MAX:.0f} ppm ca. {recommended_exchange_liters:.0f} l "
        f"({recommended_exchange_percent:.1f} %) Wasser wechseln. {measurement_text}"
    )


def _recommended_water_exchange(
    current_cya: float | None,
    volume_m3: float,
    target_cya: float,
) -> tuple[float | None, float | None]:
    if current_cya is None or current_cya <= target_cya or volume_m3 <= 0:
        return None, None

    exchange_fraction = 1.0 - (target_cya / current_cya)
    exchange_fraction = max(0.0, min(exchange_fraction, 1.0))
    percent = round(exchange_fraction * 100.0, 1)
    liters = round(volume_m3 * 1000.0 * exchange_fraction, 0)
    return percent, liters


def _dose_to_cya_ppm(amount: float, volume_m3: float, chlor_content: float, cya_ratio: float) -> float:
    if amount <= 0 or volume_m3 <= 0 or chlor_content <= 0 or cya_ratio <= 0:
        return 0.0
    return amount * chlor_content / volume_m3 * cya_ratio


def _trend_label(daily_change: float | None) -> str:
    if daily_change is None:
        return "learning"
    if abs(daily_change) < 0.1:
        return "stable"
    return "falling" if daily_change < 0 else "rising"


def _cya_ratio_for_product(product_type: object, chlor_content: float) -> float:
    if product_type != "organic":
        return 0.0
    return 0.6 if chlor_content >= 0.75 else 0.9


def _load_measurements(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=365)
    result = []
    for item in history.get(MEASUREMENTS_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        value = _non_negative_float(item.get("cya"))
        if dt and dt >= cutoff and value is not None:
            result.append({"dt": dt, "raw_ts": item.get("raw_ts"), "cya": round(value, 2)})
    result.sort(key=lambda item: item["dt"])
    return result


def _load_water_exchanges(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=365)
    result = []
    for item in history.get(WATER_EXCHANGES_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        liters = _positive_float(item.get("liters"), 0.0)
        percent = _positive_float(item.get("percent"), 0.0)
        if dt and dt >= cutoff and liters > 0 and percent > 0:
            result.append(
                {
                    "dt": dt,
                    "raw_ts": item.get("raw_ts"),
                    "liters": round(liters, 1),
                    "percent": round(min(percent, 100.0), 2),
                }
            )
    result.sort(key=lambda item: item["dt"])
    return result


def _load_chlor_doses(
    history: dict,
    parse_ts: Callable[[str | None], datetime | None],
    now: datetime,
) -> list[dict]:
    cutoff = now - timedelta(days=365)
    result = []
    for item in history.get(DOSES_KEY, []):
        if not isinstance(item, dict):
            continue
        dt = parse_ts(item.get("raw_ts"))
        amount = _positive_float(item.get("amount"), 0.0)
        if dt and dt >= cutoff and amount > 0:
            result.append({"dt": dt, "raw_ts": item.get("raw_ts"), "amount": round(amount, 3)})
    result.sort(key=lambda item: item["dt"])
    return result


def _positive_float(value: object, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _non_negative_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None

