# Release Notes V1.1.4

## Highlights

- Optionaler separater UV-Sensor ist jetzt konfigurierbar.
- Tomorrow.io-Setups koennen den UV-Index damit sauber aus `sensor.tomorrow_io_home_uv_index` beziehen.
- Die bestehende Wetterkarte und die Chlor-Logik nutzen diesen Wert automatisch.

## Details

### UV-Sensor

- Im Config Flow und im Options Flow gibt es jetzt ein optionales Feld `uv_sensor`.
- Wenn gesetzt, verwendet die Integration diesen Sensor bevorzugt für `weather_uv_today`.
- Forecast-Daten bleiben als Fallback bestehen, falls kein separater UV-Sensor konfiguriert ist.

### Wirkung

- `Sonne/UV` in der Wetterkarte kann nun auch dann gefüllt werden, wenn der Daily-Forecast selbst keinen `uv_index` liefert.
- Die bestehende UV-basierte Chlor-Anpassung arbeitet damit robuster mit Providern wie Tomorrow.io.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.1.4` angehoben.
