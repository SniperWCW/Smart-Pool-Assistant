"""PoolLab Cloud API helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import aiohttp
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

_POOLLAB_CLOUD_URL = "https://backend.labcom.cloud/graphql"
_POOLLAB_CLOUD_QUERY = "query { CloudAccount { Accounts { Measurements { parameter value timestamp } } } }"
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

CHLOR_PARAMETERS = ("PL Chlorine Free",)
PH_PARAMETERS = ("PL pH",)
TEMPERATURE_PARAMETERS = ("PL Temperature",)
CYA_PARAMETERS = ("PL Cyanuric Acid", "PL Cyanuric acid", "PL CYA")
_CHEMISTRY_PARAMETERS = (
    *CHLOR_PARAMETERS,
    *PH_PARAMETERS,
    *TEMPERATURE_PARAMETERS,
    *CYA_PARAMETERS,
)
# So viele Messungen werden fuer das Lernen uebernommen (neueste zuerst).
_MAX_HISTORY_ITEMS = 100


class PoolLabCloudError(Exception):
    """The PoolLab Cloud could not deliver usable data."""


class PoolLabCloudAuthError(PoolLabCloudError):
    """The PoolLab Cloud rejected the API key."""


@dataclass(slots=True)
class PoolLabCloudResult:
    """Normalized PoolLab Cloud values."""

    chlor: float | None = None
    ph: float | None = None
    temperature: float | None = None
    cyanuric_acid: float | None = None
    measurement_raw: str | None = None
    chlor_measurement_raw: str | None = None
    ph_measurement_raw: str | None = None
    temperature_measurement_raw: str | None = None
    cyanuric_acid_measurement_raw: str | None = None
    last_measurements: list[dict] = field(default_factory=list)
    # Kompletter Chemie-Verlauf (Chlor, pH, Temperatur, CYA) fuer das Lernen.
    history: list[dict] = field(default_factory=list)

    @property
    def found(self) -> bool:
        """Return whether the cloud response contained usable chemistry values."""
        return (
            self.chlor is not None
            or self.ph is not None
            or self.temperature is not None
            or self.cyanuric_acid is not None
        )


async def async_fetch_poollab_cloud_measurements(session, api_key: str) -> PoolLabCloudResult:
    """Fetch and normalize PoolLab Cloud measurements.

    Raises ``PoolLabCloudAuthError`` for a rejected API key and
    ``PoolLabCloudError`` for any other failure of the cloud request.
    """
    payload = {"query": _POOLLAB_CLOUD_QUERY}
    headers = {"Authorization": api_key}

    async with session.post(
        _POOLLAB_CLOUD_URL,
        json=payload,
        headers=headers,
        timeout=_REQUEST_TIMEOUT,
    ) as resp:
        if resp.status in (401, 403):
            raise PoolLabCloudAuthError("PoolLab Cloud: API-Key ungueltig oder abgelaufen.")
        if resp.status != 200:
            raise PoolLabCloudError(f"PoolLab Cloud antwortet mit HTTP {resp.status}.")

        try:
            result = await resp.json(content_type=None)
        except ValueError as err:
            raise PoolLabCloudError("PoolLab Cloud lieferte keine gueltige JSON-Antwort.") from err

    if not isinstance(result, dict):
        raise PoolLabCloudError("PoolLab Cloud lieferte eine unerwartete Antwort.")

    cloud_data = (result.get("data") or {}).get("CloudAccount")
    if not cloud_data:
        _raise_for_graphql_errors(result.get("errors"))

    if not cloud_data or not cloud_data.get("Accounts"):
        _LOGGER.debug("PoolLab Cloud response did not contain accounts")
        return PoolLabCloudResult()

    measurements = [
        item for item in (cloud_data["Accounts"][0].get("Measurements") or []) if isinstance(item, dict)
    ]
    measurements.sort(key=lambda item: item.get("timestamp") or 0, reverse=True)

    cloud_result = PoolLabCloudResult(
        measurement_raw=_latest_chemistry_timestamp(measurements),
        last_measurements=_last_measurements_for_display(measurements),
        history=_chemistry_history(measurements),
    )

    for obs in measurements:
        p_name = obs.get("parameter")
        p_val_raw = obs.get("value")
        if p_val_raw is None:
            continue

        try:
            p_val = float(p_val_raw)
        except (ValueError, TypeError):
            _LOGGER.debug("Could not parse value for %s: %s", p_name, p_val_raw)
            continue

        if p_name in CHLOR_PARAMETERS and cloud_result.chlor is None:
            cloud_result.chlor = p_val
            cloud_result.chlor_measurement_raw = _measurement_timestamp_iso(obs)
        if p_name in PH_PARAMETERS and cloud_result.ph is None:
            cloud_result.ph = p_val
            cloud_result.ph_measurement_raw = _measurement_timestamp_iso(obs)
        if p_name in TEMPERATURE_PARAMETERS and cloud_result.temperature is None:
            cloud_result.temperature = p_val
            cloud_result.temperature_measurement_raw = _measurement_timestamp_iso(obs)
        if p_name in CYA_PARAMETERS and cloud_result.cyanuric_acid is None:
            cloud_result.cyanuric_acid = p_val
            cloud_result.cyanuric_acid_measurement_raw = _measurement_timestamp_iso(obs)
        if (
            cloud_result.chlor is not None
            and cloud_result.ph is not None
            and cloud_result.temperature is not None
            and cloud_result.cyanuric_acid is not None
        ):
            break

    _LOGGER.debug(
        "PoolLab Cloud values selected: chlor=%s ph=%s temp=%s cya=%s measurement_raw=%s history_items=%s",
        cloud_result.chlor,
        cloud_result.ph,
        cloud_result.temperature,
        cloud_result.cyanuric_acid,
        cloud_result.measurement_raw,
        len(cloud_result.history),
    )
    return cloud_result


def _raise_for_graphql_errors(errors: object) -> None:
    """Raise a descriptive error if the GraphQL response carries errors."""
    if not isinstance(errors, list) or not errors:
        return

    first = errors[0]
    message = str(first.get("message") if isinstance(first, dict) else first)
    lowered = message.lower()
    if any(word in lowered for word in ("unauthor", "unauthent", "forbidden", "invalid token", "api key", "api-key")):
        raise PoolLabCloudAuthError("PoolLab Cloud: API-Key ungueltig oder abgelaufen.")
    raise PoolLabCloudError(f"PoolLab Cloud meldet einen Fehler: {message}")


def _latest_chemistry_timestamp(measurements: list[dict]) -> str | None:
    chemistry_measurements = [
        obs for obs in measurements
        if obs.get("parameter") in _CHEMISTRY_PARAMETERS
    ]

    if chemistry_measurements:
        return _measurement_timestamp_iso(chemistry_measurements[0])

    return None


def _measurement_timestamp_iso(measurement: dict) -> str | None:
    timestamp = measurement.get("timestamp")
    if timestamp is None:
        return None
    try:
        return dt_util.utc_from_timestamp(timestamp).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _last_measurements_for_display(measurements: list[dict]) -> list[dict]:
    last_measurements = []
    for obs in measurements[:4]:
        last_measurements.append({
            "parameter": obs.get("parameter"),
            "value": obs.get("value"),
            "timestamp": _measurement_timestamp_iso(obs),
        })
    return last_measurements


def _chemistry_history(measurements: list[dict]) -> list[dict]:
    """Return the newest chemistry measurements with ISO timestamps."""
    history: list[dict] = []
    for obs in measurements:
        if obs.get("parameter") not in _CHEMISTRY_PARAMETERS or obs.get("value") is None:
            continue
        timestamp = _measurement_timestamp_iso(obs)
        if timestamp is None:
            continue
        history.append({
            "parameter": obs.get("parameter"),
            "value": obs.get("value"),
            "timestamp": timestamp,
        })
        if len(history) >= _MAX_HISTORY_ITEMS:
            break
    return history
