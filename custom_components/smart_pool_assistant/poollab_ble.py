import asyncio
import logging
import struct
from dataclasses import dataclass
from bleak import BleakClient, BleakError, BleakGATTCharacteristic
from bleak_retry_connector import establish_connection

_LOGGER = logging.getLogger(__name__)

# BLE UUIDs für PoolLab 1.0
SERVICE_UUID = "a7ee04a9-507b-4910-a528-b619d5501924"
MOSI_UUID    = "91bfa536-3036-4901-8813-3635fced7b90"  # Write (Commands)
MISO_UUID    = "2ff18b59-195d-4ee1-b78c-0cbde3eff9c2"  # Read (Responses)
SIGNAL_UUID  = "c2296c06-c7e0-4657-b42e-c8330826454c"  # Notify (Signal)

PREAMBLE = 0xAB
STATUS_OK = 0

@dataclass
class PoolLabMeasurement:
    measure_id:   int
    measure_type: int
    status:       int
    timestamp:    int
    value:        float

@dataclass
class PoolLabData:
    battery:      int
    measurements: dict[int, PoolLabMeasurement]

class PoolLabBLEClient:
    """Handles BLE communication with a PoolLab 1.0 device."""

    def __init__(self, device) -> None:
        self._device = device
        self._notify_event = asyncio.Event()

    def _on_notify(self, _sender: BleakGATTCharacteristic, _data: bytearray) -> None:
        self._notify_event.set()

    async def _send_command(self, client: BleakClient, cmd: bytes, timeout: float = 5.0) -> bytes:
        self._notify_event.clear()
        await asyncio.sleep(0.2)  # Kurze Pause vor dem Schreiben für Proxy-Stabilität
        await client.write_gatt_char(MOSI_UUID, cmd, response=True)
        try:
            await asyncio.wait_for(self._notify_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            raise BleakError("Timeout waiting for PoolLab response")
        await asyncio.sleep(0.2)  # Kurze Pause vor dem Lesen der Antwort
        return bytes(await client.read_gatt_char(MISO_UUID))

    @staticmethod
    def _build_command(cmd_type: int, payload: bytes = b"") -> bytes:
        frame = bytearray(128)
        frame[0] = PREAMBLE
        frame[1] = cmd_type
        for i, b in enumerate(payload):
            frame[3 + i] = b
        return bytes(frame)

    @staticmethod
    def _parse_measurement(data: bytes) -> PoolLabMeasurement | None:
        """Parses a single 16-byte measurement record from a 19-byte response."""
        if not data or len(data) < 3 or data[0] != PREAMBLE or data[1] != 0x05:
            return None
        # Das Datenpaket beginnt nach Preamble, CMD und Status (Offset 3)
        chunk = data[3:19]
        if len(chunk) < 12: return None

        m_id, m_type, status, ts = struct.unpack_from("<HBBI", chunk, 0)
        (val,) = struct.unpack_from("<f", chunk, 8)
        return PoolLabMeasurement(m_id, m_type, status, ts, val)

    async def async_read_data(self) -> PoolLabData:
        """Connect to PoolLab, read measurements, and disconnect."""
        _LOGGER.debug("Connecting to PoolLab via BLE: %s", self._device.address)
        client = await establish_connection(BleakClient, self._device, self._device.address)
        async with client:
            await client.start_notify(SIGNAL_UUID, self._on_notify)
            await asyncio.sleep(0.5)  # Warten, bis Benachrichtigungen aktiv sind

            # Step 1: GET_INFO (Battery @ Byte 21, Count @ Byte 3-4)
            info_resp = await self._send_command(client, self._build_command(0x01))
            result_count = struct.unpack_from("<H", info_resp, 3)[0] if len(info_resp) > 5 else 0
            battery = struct.unpack_from("<H", info_resp, 21)[0]
            _LOGGER.debug("PoolLab Info: %s total measurements, battery: %s%%", result_count, battery)

            # Step 2: GET_MEASURES
            # Wir rufen die letzten 20 Messungen einzeln ab, um sicher die neuesten Werte zu erhalten.
            all_measurements = []
            start_idx = max(0, result_count - 20)
            for i in range(start_idx, result_count):
                # Payload für Command 0x05 ist der 16-bit Index (High, Low)
                payload = bytes([(i >> 8) & 0xFF, i & 0xFF])
                resp = await self._send_command(client, self._build_command(0x05, payload))
                if m := self._parse_measurement(resp):
                    all_measurements.append(m)

            await client.stop_notify(SIGNAL_UUID)

        latest: dict[int, PoolLabMeasurement] = {}
        for m in all_measurements:
            if m.status != STATUS_OK: continue
            existing = latest.get(m.measure_type)
            if existing is None or m.timestamp > existing.timestamp:
                latest[m.measure_type] = m

        return PoolLabData(battery=battery, measurements=latest)
