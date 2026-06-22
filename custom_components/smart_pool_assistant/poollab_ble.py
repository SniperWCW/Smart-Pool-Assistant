import asyncio
import logging
import math
import struct
from dataclasses import dataclass

from bleak import BleakClient, BleakError, BleakGATTCharacteristic
from bleak_retry_connector import establish_connection

_LOGGER = logging.getLogger(__name__)

# BLE UUIDs for PoolLab 1.0
SERVICE_UUID = "a7ee04a9-507b-4910-a528-b619d5501924"
MOSI_UUID = "91bfa536-3036-4901-8813-3635fced7b90"  # Write (Commands)
MISO_UUID = "2ff18b59-195d-4ee1-b78c-0cbde3eff9c2"  # Read (Responses)
SIGNAL_UUID = "c2296c06-c7e0-4657-b42e-c8330826454c"  # Notify (Signal)

PREAMBLE = 0xAB
STATUS_OK = 0


@dataclass
class PoolLabMeasurement:
    measure_id: int
    measure_type: int
    status: int
    timestamp: int
    value: float


@dataclass
class PoolLabData:
    battery: int
    measurements: dict[int, PoolLabMeasurement]


class PoolLabBLEClient:
    """Handles BLE communication with a PoolLab 1.0 device."""

    def __init__(self, device) -> None:
        self._device = device
        self._notify_event = asyncio.Event()

    def _on_notify(self, _sender: BleakGATTCharacteristic, _data: bytearray) -> None:
        self._notify_event.set()

    async def _start_notify_with_retry(
        self,
        client: BleakClient,
        attempts: int = 2,
        delay: float = 2.0,
    ) -> None:
        """Start notifications, retrying transient ESPHome GATT errors."""
        for attempt in range(1, attempts + 1):
            try:
                _LOGGER.debug(
                    "Starting MISO signal notifications on %s attempt=%s/%s",
                    SIGNAL_UUID,
                    attempt,
                    attempts,
                )
                await client.start_notify(SIGNAL_UUID, self._on_notify)
                _LOGGER.debug("MISO signal notifications started on %s", SIGNAL_UUID)
                return
            except BleakError as err:
                _LOGGER.warning(
                    "PoolLab start_notify failed: address=%s attempt=%s/%s error=%s",
                    self._device.address,
                    attempt,
                    attempts,
                    err,
                )
                if attempt == attempts:
                    raise
                await asyncio.sleep(delay * attempt)

    @staticmethod
    def _hex_preview(data: bytes, limit: int = 32) -> str:
        """Return a short hex preview for debug logging."""
        return data[:limit].hex(" ")

    async def _send_command(self, client: BleakClient, cmd: bytes, timeout: float = 5.0) -> bytes:
        """Send a command and wait until the PoolLab signals that a response is ready."""
        self._notify_event.clear()
        await asyncio.sleep(0.4)  # Slightly more conservative for BLE proxy stability
        _LOGGER.debug(
            "PoolLab BLE write: char=%s timeout=%s payload_len=%s payload=%s",
            MOSI_UUID,
            timeout,
            len(cmd),
            self._hex_preview(cmd),
        )
        await client.write_gatt_char(MOSI_UUID, cmd, response=True)
        try:
            await asyncio.wait_for(self._notify_event.wait(), timeout=timeout)
        except asyncio.TimeoutError as err:
            raise BleakError("Timeout waiting for PoolLab response") from err

        # The signal only means "response ready"; give proxied links a moment to settle.
        await asyncio.sleep(0.4)
        response = bytes(await client.read_gatt_char(MISO_UUID))
        _LOGGER.debug(
            "PoolLab BLE read: char=%s response_len=%s response=%s",
            MISO_UUID,
            len(response),
            self._hex_preview(response, 64),
        )
        return response

    @staticmethod
    def _build_command(cmd_type: int, payload: bytes = b"") -> bytes:
        return bytes((PREAMBLE, cmd_type & 0xFF, (cmd_type >> 8) & 0xFF)) + payload

    @staticmethod
    def _parse_measurements(data: bytes) -> list[PoolLabMeasurement]:
        """Parse up to 8 measurement records from one GET_MEASURES response."""
        if not data or len(data) < 17 or data[0] != PREAMBLE:
            return []

        measurements: list[PoolLabMeasurement] = []
        # Response layout: preamble + 8 x 16-byte measurement records
        for offset in range(1, min(len(data), 1 + 16 * 8), 16):
            chunk = data[offset : offset + 16]
            if len(chunk) < 16 or not any(chunk):
                continue

            m_id, m_type, status, ts = struct.unpack_from("<HBBI", chunk, 0)
            (val,) = struct.unpack_from("<f", chunk, 8)
            measurements.append(PoolLabMeasurement(m_id, m_type, status, ts, val))

        return measurements

    async def async_read_data(self) -> PoolLabData:
        """Connect to PoolLab, read measurements, and disconnect."""
        _LOGGER.debug(
            "Connecting to PoolLab via BLE: name=%s address=%s rssi=%s details=%s",
            getattr(self._device, "name", None),
            self._device.address,
            getattr(self._device, "rssi", None),
            getattr(self._device, "details", None),
        )
        client: BleakClient | None = None
        notifications_started = False
        try:
            client = await establish_connection(BleakClient, self._device, self._device.address)
            _LOGGER.debug("BLE connection established to PoolLab: %s", self._device.address)
        except Exception:
            _LOGGER.exception(
                "BLE connection failed before GATT setup: address=%s service=%s",
                self._device.address,
                SERVICE_UUID,
            )
            raise

        try:
            await self._start_notify_with_retry(client)
            notifications_started = True
            await asyncio.sleep(1.0)  # Let proxies settle before the first command

            # Step 1: GET_INFO (battery @ byte 21, count @ byte 3-4)
            _LOGGER.debug("Sending PoolLab GET_INFO command")
            info_resp: bytes | None = None
            for attempt in range(2):
                try:
                    info_resp = await self._send_command(client, self._build_command(0x01))
                    break
                except BleakError as err:
                    _LOGGER.debug(
                        "PoolLab GET_INFO failed: attempt=%s/2 error=%s",
                        attempt + 1,
                        err,
                    )
                    if attempt == 1:
                        raise
                    await asyncio.sleep(1.0)

            if info_resp is None:
                raise BleakError("PoolLab GET_INFO returned no response")

            result_count = struct.unpack_from("<H", info_resp, 5)[0] if len(info_resp) > 7 else 0
            battery = struct.unpack_from("<H", info_resp, 21)[0]
            _LOGGER.debug(
                "PoolLab Info: %s total measurements, battery: %s%%, raw=%s",
                result_count,
                battery,
                info_resp[:32].hex(" "),
            )

            # Step 2: GET_MEASURES
            # Read the saved results in 8-result blocks as documented by the API.
            all_measurements = []
            command_count = math.ceil(result_count / 8) if result_count else 0
            _LOGGER.debug(
                "Preparing PoolLab GET_MEASURES reads: result_count=%s command_count=%s",
                result_count,
                command_count,
            )
            for chunk_idx in range(command_count):
                cell_id = chunk_idx // 2
                cell_half = chunk_idx % 2  # 0 = lower half, 1 = upper half
                payload = bytes([(cell_id >> 8) & 0xFF, cell_id & 0xFF, cell_half, 0x00])
                _LOGGER.debug(
                    "Requesting measurement chunk=%s cell_id=%s half=%s payload=%s",
                    chunk_idx,
                    cell_id,
                    "lower" if cell_half == 0 else "upper",
                    payload.hex(" "),
                )

                resp: bytes | None = None
                for attempt in range(2):
                    try:
                        resp = await self._send_command(
                            client,
                            self._build_command(0x05, payload),
                            timeout=7.5,
                        )
                        break
                    except BleakError as err:
                        _LOGGER.debug(
                            "PoolLab chunk read failed: chunk=%s attempt=%s/2 error=%s",
                            chunk_idx,
                            attempt + 1,
                            err,
                        )
                        if attempt == 1:
                            raise
                        _LOGGER.debug("Retrying PoolLab measurement read for chunk %s after BLE error: %s", chunk_idx, err)
                        await asyncio.sleep(1.0)

                if resp:
                    _LOGGER.debug(
                        "PoolLab GET_MEASURES chunk=%s cell=%s half=%s len=%s raw=%s",
                        chunk_idx,
                        cell_id,
                        cell_half,
                        len(resp),
                        resp[:40].hex(" "),
                    )
                    parsed = self._parse_measurements(resp)
                    all_measurements.extend(parsed)
                    for measurement in parsed:
                        _LOGGER.debug(
                            "PoolLab measurement parsed: chunk=%s id=%s type=%s status=%s ts=%s value=%s",
                            chunk_idx,
                            measurement.measure_id,
                            measurement.measure_type,
                            measurement.status,
                            measurement.timestamp,
                            measurement.value,
                        )
                    if not parsed:
                        _LOGGER.debug(
                            "Ignoring unexpected measurement response for chunk %s: %s",
                            chunk_idx,
                            resp[:40].hex(" "),
                        )
                else:
                    _LOGGER.debug(
                        "No response payload received for measurement chunk %s",
                        chunk_idx,
                    )
        except Exception as err:
            _LOGGER.warning(
                "BLE read failed during command flow for %s: %s: %s",
                self._device.address,
                type(err).__name__,
                err,
            )
            raise
        finally:
            if client is not None and notifications_started:
                try:
                    await client.stop_notify(SIGNAL_UUID)
                    _LOGGER.debug("Stopped MISO signal notifications on %s", SIGNAL_UUID)
                except Exception as err:
                    _LOGGER.debug(
                        "Ignoring PoolLab stop_notify cleanup failure for %s: %s",
                        self._device.address,
                        err,
                    )
            if client is not None:
                try:
                    if getattr(client, "is_connected", False):
                        await client.disconnect()
                        _LOGGER.debug("Disconnected from PoolLab BLE device: %s", self._device.address)
                except Exception as err:
                    _LOGGER.debug(
                        "Ignoring PoolLab disconnect cleanup failure for %s: %s",
                        self._device.address,
                        err,
                    )

        latest: dict[int, PoolLabMeasurement] = {}
        for m in all_measurements:
            if m.status != STATUS_OK:
                continue
            existing = latest.get(m.measure_type)
            if existing is None or m.timestamp > existing.timestamp:
                latest[m.measure_type] = m

        _LOGGER.debug(
            "PoolLab BLE read complete: battery=%s parsed_measurements=%s latest_types=%s",
            battery,
            len(all_measurements),
            sorted(latest.keys()),
        )
        return PoolLabData(battery=battery, measurements=latest)
