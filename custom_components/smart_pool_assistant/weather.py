"""Weather helpers for Smart Pool Assistant."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_WEATHER_ENTITY


def get_weather_forecast_today(hass: HomeAssistant, conf: dict) -> dict | None:
    """Return normalized weather data for today's daily forecast."""
    entity_id = conf.get(CONF_WEATHER_ENTITY)
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return {"entity_id": entity_id, "available": False}

    base = {
        "entity_id": entity_id,
        "available": True,
        "condition": _valid_state_value(state.state),
        "temperature": _to_float(state.attributes.get("temperature")),
        "wind_speed": _to_float(state.attributes.get("wind_speed")),
    }

    forecast = state.attributes.get("forecast")
    if not isinstance(forecast, list) or not forecast:
        return {**base, "has_forecast": False}

    today = dt_util.now().date()
    selected = None
    for item in forecast:
        if not isinstance(item, dict):
            continue
        dt_raw = item.get("datetime")
        if dt_raw:
            parsed = dt_util.parse_datetime(dt_raw)
            if parsed is not None and dt_util.as_local(parsed).date() == today:
                selected = item
                break
        if selected is None:
            selected = item

    if selected is None:
        return {**base, "has_forecast": False}

    precipitation_probability = selected.get("precipitation_probability")
    precipitation_amount = selected.get("precipitation")
    uv_index = selected.get("uv_index")

    return {
        **base,
        "has_forecast": True,
        "condition": selected.get("condition") or base["condition"],
        "uv_index": _to_float(uv_index),
        "precipitation_probability": _to_float(precipitation_probability),
        "precipitation_amount": _to_float(precipitation_amount),
        "wind_speed": _to_float(selected.get("wind_speed")) or base["wind_speed"],
        "temperature": _to_float(selected.get("temperature")) or base["temperature"],
    }


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _valid_state_value(value: str | None) -> str | None:
    if value in (None, "unknown", "unavailable", "none", "null"):
        return None
    return value
