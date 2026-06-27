"""PoolLab Cloud API helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

_POOLLAB_CLOUD_URL = "https://backend.labcom.cloud/graphql"
_POOLLAB_CLOUD_QUERY = "query { CloudAccount { Accounts { Measurements { parameter value timestamp } } } }"


@dataclass(slots=True)
class PoolLabCloudResult:
    """Normalized PoolLab Cloud values."""

    chlor: float | None = None
    ph: float | None = None
    temperature: float | None = None
    cyanuric_acid: float | None = None
    measurement_raw: str | None = None
    last_measurements: list[dict] = field(default_factory=list)

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
    """Fetch and normalize PoolLab Cloud measurements."""
    payload = {"query": _POOLLAB_CLOUD_QUERY}
    headers = {"Authorization": api_key}

    async with session.post(
        _POOLLAB_CLOUD_URL,
        json=payload,
        headers=headers,
        timeout=10,
    ) as resp:
        if resp.status != 200:
            _LOGGER.debug("PoolLab Cloud request failed with HTTP status %s", resp.status)
            return PoolLabCloudResult()

        result = await resp.json()

    cloud_data = result.get("data", {}).get("CloudAccount")
    if not cloud_data or not cloud_data.get("Accounts"):
        _LOGGER.debug("PoolLab Cloud response did not contain accounts")
        return PoolLabCloudResult()

    measurements = list(cloud_data["Accounts"][0].get("Measurements", []))
    measurements.sort(key=lambda item: item.get("timestamp") or 0, reverse=True)

    cloud_result = PoolLabCloudResult(
        measurement_raw=_latest_chemistry_timestamp(measurements),
        last_measurements=_last_measurements_for_display(measurements),
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

        if p_name == "PL Chlorine Free" and cloud_result.chlor is None:
            cloud_result.chlor = p_val
        if p_name == "PL pH" and cloud_result.ph is None:
            cloud_result.ph = p_val
        if p_name == "PL Temperature" and cloud_result.temperature is None:
            cloud_result.temperature = p_val
        if p_name in ("PL Cyanuric Acid", "PL Cyanuric acid", "PL CYA") and cloud_result.cyanuric_acid is None:
            cloud_result.cyanuric_acid = p_val
        if (
            cloud_result.chlor is not None
            and cloud_result.ph is not None
            and cloud_result.temperature is not None
            and cloud_result.cyanuric_acid is not None
        ):
            break

    _LOGGER.debug(
        "PoolLab Cloud values selected: chlor=%s ph=%s temp=%s cya=%s measurement_raw=%s last_measurements=%s",
        cloud_result.chlor,
        cloud_result.ph,
        cloud_result.temperature,
        cloud_result.cyanuric_acid,
        cloud_result.measurement_raw,
        cloud_result.last_measurements,
    )
    return cloud_result


def _latest_chemistry_timestamp(measurements: list[dict]) -> str | None:
    chemistry_measurements = [
        obs for obs in measurements
        if obs.get("parameter") in ("PL Chlorine Free", "PL pH")
    ]

    if chemistry_measurements and (latest_ts := chemistry_measurements[0].get("timestamp")):
        return dt_util.utc_from_timestamp(latest_ts).isoformat()

    return None


def _last_measurements_for_display(measurements: list[dict]) -> list[dict]:
    last_measurements = []
    for obs in measurements[:4]:
        p_ts = obs.get("timestamp")
        last_measurements.append({
            "parameter": obs.get("parameter"),
            "value": obs.get("value"),
            "timestamp": dt_util.utc_from_timestamp(p_ts).isoformat() if p_ts else None,
        })
    return last_measurements
