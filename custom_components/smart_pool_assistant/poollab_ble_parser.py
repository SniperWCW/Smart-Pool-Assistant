import struct
import logging
from dataclasses import dataclass
from typing import Optional

_LOGGER = logging.getLogger(__name__)

# Parameter IDs laut PoolLab 1.0 BLE API
PARAM_PH = 1
PARAM_CHLORINE_FREE = 2
PARAM_CHLORINE_TOTAL = 3
PARAM_ALKALINITY = 4
PARAM_CYANURIC_ACID = 5
PARAM_WATER_TEMP = 12

@dataclass
class PoolLabMeasurement:
    parameter_id: int
    value: float
    unit: int
    timestamp: int

class PoolLabBLEParser:
    """Parser für binäre PoolLab 1.0 BLE Datenpakete."""

    def parse_response_packet(self, data: bytes) -> list[PoolLabMeasurement]:
        """
        Parsed ein vollständiges Kommunikationspaket von FF02.
        Struktur: [STX:0x02] [LEN_L] [LEN_H] [CMD] [DATA...] [CRC_L] [CRC_H] [ETX:0x03]
        """
        measurements = []
        
        if len(data) < 8:
            return measurements
        
        if data[0] != 0x02 or data[-1] != 0x03:
            _LOGGER.debug("Ungültiges STX/ETX im BLE Paket")
            return measurements

        # CMD 0x10 ist 'Get Measurements'
        cmd = data[3]
        
        if cmd == 0x10:
            payload = data[4:-3] # Daten zwischen CMD und CRC extrahieren
            # Jeder Messdatensatz ist exakt 16 Bytes lang
            for i in range(0, len(payload), 16):
                record = payload[i : i + 16]
                if len(record) == 16:
                    parsed = self._parse_record(record)
                    if parsed:
                        measurements.append(parsed)
                        
        return measurements

    def _parse_record(self, data: bytes) -> Optional[PoolLabMeasurement]:
        """
        Parsed einen einzelnen 16-Byte Datensatz.
        [4-7]  Timestamp (uint32)
        [8]    Parameter ID (uint8)
        [9-12] Value (float32)
        """
        try:
            # Checksumme prüfen (Summe der Bytes 0-14 modulo 256)
            if sum(data[:15]) % 256 != data[15]:
                _LOGGER.debug("Prüfsummenfehler im Datensatz")
                return None

            timestamp = struct.unpack_from("<I", data, 4)[0]
            param_id = data[8]
            value = struct.unpack_from("<f", data, 9)[0]
            unit = data[13]

            return PoolLabMeasurement(
                parameter_id=param_id,
                value=round(value, 2),
                unit=unit,
                timestamp=timestamp
            )
        except Exception as err:
            _LOGGER.error("Fehler beim Dekodieren des PoolLab Datensatzes: %s", err)
            return None