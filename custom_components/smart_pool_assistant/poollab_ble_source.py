"""PoolLab BLE measurement selection helpers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from .poollab_ble import PoolLabData, PoolLabMeasurement

_LOGGER = logging.getLogger(__name__)

_CHLORINE_TYPE_IDS = (1, 8, 3)
_PH_TYPE_IDS = (9, 27, 28, 29, 30, 31, 32, 33, 34, 36, 48)
_TEMPERATURE_TYPE_ID = 4
_CYANURIC_ACID_TYPE_ID = 11


@dataclass(slots=True)
class PoolLabBLESelection:
    """Selected values from a PoolLab BLE payload."""

    battery: int
    chlor: float | None = None
    ph: float | None = None
    temperature: float | None = None
    cyanuric_acid: float | None = None
    measurement_raw: str | None = None

    @property
    def found(self) -> bool:
        """Return whether the BLE response contained usable chemistry values."""
        return (
            self.chlor is not None
            or self.ph is not None
            or self.temperature is not None
            or self.cyanuric_acid is not None
        )


def select_poollab_ble_measurements(
    ble_data: PoolLabData,
    fetched_at_iso: str | None,
    normalize_measurement_ts: Callable[[int, str | None], str],
) -> PoolLabBLESelection:
    """Select current pool values from raw PoolLab BLE measurements."""
    m_chlor = _get_ble_measurement(ble_data, _CHLORINE_TYPE_IDS)
    m_ph = _get_ble_measurement(ble_data, _PH_TYPE_IDS)
    m_temp = ble_data.measurements.get(_TEMPERATURE_TYPE_ID)
    m_cya = ble_data.measurements.get(_CYANURIC_ACID_TYPE_ID)

    ble_ts_list = []
    if m_chlor:
        ble_ts_list.append(m_chlor.timestamp)
    if m_ph:
        ble_ts_list.append(m_ph.timestamp)

    _LOGGER.debug(
        "BLE selection result: available_types=%s chlor=%s ph=%s temp=%s cya=%s",
        sorted(ble_data.measurements.keys()),
        getattr(m_chlor, "measure_type", None),
        getattr(m_ph, "measure_type", None),
        getattr(m_temp, "measure_type", None),
        getattr(m_cya, "measure_type", None),
    )
    if m_ph is None:
        _LOGGER.debug(
            "No pH measurement selected from BLE response. Available measurement types were: %s",
            sorted(ble_data.measurements.keys()),
        )

    return PoolLabBLESelection(
        battery=ble_data.battery,
        chlor=m_chlor.value if m_chlor else None,
        ph=m_ph.value if m_ph else None,
        temperature=m_temp.value if m_temp else None,
        cyanuric_acid=m_cya.value if m_cya else None,
        measurement_raw=normalize_measurement_ts(max(ble_ts_list), fetched_at_iso) if ble_ts_list else None,
    )


def _get_ble_measurement(
    ble_data: PoolLabData,
    type_ids: tuple[int, ...],
) -> PoolLabMeasurement | None:
    """Return the first BLE measurement matching one of the supported type IDs."""
    for type_id in type_ids:
        if measurement := ble_data.measurements.get(type_id):
            return measurement
    return None
