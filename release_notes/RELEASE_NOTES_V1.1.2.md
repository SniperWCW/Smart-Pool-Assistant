# Release Notes V1.1.2

## Highlights

- Wetter-Normalisierung wurde aus `coordinator.py` nach `weather.py` verschoben.
- PoolLab-BLE-Messwertauswahl wurde nach `poollab_ble_source.py` ausgelagert.
- Die Lovelace-Wetterkarte zeigt nun auch dann Wetterdaten fuer heute, wenn kein Daily-Forecast aus Home Assistant geliefert wird.
- Der Frontend-Cachebuster verwendet nun die Manifest-Version, damit Kartenfixes nach Updates zuverlaessiger geladen werden.

## Details

### Wetter

- `weather.py` kapselt die Backend-Normalisierung der konfigurierten Wetter-Entity.
- Der Coordinator stellt zusaetzlich `weather_condition_today`, `weather_temperature_today` und `weather_wind_speed_today` bereit.
- Die Karte versucht weiterhin zuerst Forecast-Daten zu verwenden.
- Wenn kein Forecast verfuegbar ist, nutzt die Karte die Coordinator-Wetterattribute bzw. aktuelle Attribute der Weather-Entity als Fallback.
- Die Frontend-Ressource wird mit der Manifest-Version versioniert statt mit der Config-Entry-Version.

### PoolLab BLE

- `poollab_ble_source.py` kapselt die Auswahl der relevanten PoolLab-BLE-Messwerte.
- Die Type-ID-Zuordnung fuer Chlor, pH, Temperatur und Cyanursaeure liegt damit nicht mehr direkt im Coordinator.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.1.2` angehoben.
