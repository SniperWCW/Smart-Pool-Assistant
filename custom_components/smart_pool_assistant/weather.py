"""Weather helpers for Smart Pool Assistant."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_UV_SENSOR, CONF_WEATHER_ENTITY

_LOGGER = logging.getLogger(__name__)


async def async_get_weather_data(hass: HomeAssistant, conf: dict, limit: int = 2) -> dict | None:
    """Return normalized weather data for daily forecast and today's chemistry."""
    entity_id = conf.get(CONF_WEATHER_ENTITY)
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return {"entity_id": entity_id, "available": False, "forecast_days": [], "today": None}

    base = {
        "entity_id": entity_id,
        "available": True,
        "condition": _valid_state_value(state.state),
        "temperature": _to_float(state.attributes.get("temperature")),
        "wind_speed": _to_float(state.attributes.get("wind_speed")),
        "wind_speed_unit": state.attributes.get("wind_speed_unit"),
    }

    forecast = state.attributes.get("forecast")
    if not isinstance(forecast, list) or not forecast:
        forecast = await _async_fetch_daily_forecast(hass, entity_id)

    normalized_days = _normalize_forecast_days(forecast, base["wind_speed_unit"], limit=limit)
    today = _select_today_forecast(normalized_days)

    if today is None:
        today = {
            "condition": base["condition"],
            "temperature": base["temperature"],
            "wind_speed": base["wind_speed"],
            "wind_speed_unit": base["wind_speed_unit"],
        }

    return {
        **base,
        "has_forecast": len(normalized_days) > 0,
        "forecast_days": normalized_days,
        "today": _apply_uv_sensor(hass, conf, today),
    }


async def _async_fetch_daily_forecast(hass: HomeAssistant, entity_id: str) -> list[dict]:
    """Fetch daily weather forecast through the HA weather service."""
    try:
        response = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"type": "daily"},
            blocking=True,
            target={"entity_id": entity_id},
            return_response=True,
        )
    except Exception as err:  # pragma: no cover - defensive logging only
        _LOGGER.debug("Weather forecast service failed for %s: %s", entity_id, err)
        return []

    if isinstance(response, dict):
        entity_response = response.get(entity_id)
        if isinstance(entity_response, dict) and isinstance(entity_response.get("forecast"), list):
            return entity_response["forecast"]
        if isinstance(response.get("forecast"), list):
            return response["forecast"]

    return []


def _normalize_forecast_days(forecast: list | None, wind_speed_unit: str | None, limit: int = 2) -> list[dict]:
    """Normalize forecast entries to a stable card/backend format."""
    if not isinstance(forecast, list):
        return []

    days: list[dict] = []
    for item in forecast:
        if not isinstance(item, dict):
            continue
        days.append(
            {
                "datetime": item.get("datetime"),
                "condition": item.get("condition"),
                "temperature": _to_float(item.get("temperature") or item.get("native_temperature")),
                "templow": _to_float(
                    item.get("templow") or item.get("native_templow") or item.get("low_temperature")
                ),
                "precipitation_probability": _to_float(item.get("precipitation_probability")),
                "precipitation_amount": _to_float(item.get("precipitation") or item.get("native_precipitation")),
                "uv_index": _to_float(item.get("uv_index") or item.get("uv")),
                "wind_speed": _to_float(item.get("wind_speed") or item.get("native_wind_speed")),
                "wind_speed_unit": wind_speed_unit,
            }
        )
        if len(days) >= limit:
            break

    return days


def _select_today_forecast(days: list[dict]) -> dict | None:
    """Pick today's forecast entry or the first available day."""
    if not days:
        return None

    today = dt_util.now().date()
    selected = None
    for item in days:
        dt_raw = item.get("datetime")
        if dt_raw:
            parsed = dt_util.parse_datetime(dt_raw)
            if parsed is not None and dt_util.as_local(parsed).date() == today:
                return item
        if selected is None:
            selected = item

    return selected


def _apply_uv_sensor(hass: HomeAssistant, conf: dict, today: dict | None) -> dict | None:
    """Override UV index from an optional dedicated sensor when configured."""
    if today is None:
        return None

    uv_sensor = conf.get(CONF_UV_SENSOR)
    if not uv_sensor:
        return today

    state = hass.states.get(uv_sensor)
    if state is None:
        return today

    uv_value = _to_float(state.state)
    if uv_value is None:
        uv_value = _to_float(state.attributes.get("state"))
    if uv_value is None:
        return today

    return {**today, "uv_index": uv_value}


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
