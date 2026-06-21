# Release Notes V1.1.3

## Highlights

- Daily-Forecasts für die Wetterkarte werden jetzt im Backend geladen und normalisiert.
- Tomorrow.io und ähnliche Provider funktionieren damit robuster für `Heute` und `Morgen`.
- Die Karte nutzt bevorzugt die vorbereiteten Forecast-Tagesdaten aus dem Empfehlungssensor.

## Details

### Wetter

- `weather.py` lädt Daily-Forecasts nun bei Bedarf über Home Assistants Wetter-Service mit `return_response=True`.
- Die Integration normalisiert daraus `weather_forecast_days` sowie die heutigen Wetterwerte für die Chemie-Logik.
- `coordinator.py` reicht diese Daten an den Empfehlungssensor weiter, inklusive `weather_wind_speed_unit`.
- Die Lovelace-Karte nutzt zuerst diese Backend-Daten und fällt nur noch danach auf direkte Weather-Entity-Attribute zurück.

### Wirkung

- Wetterkarten mit Entitäten wie `weather.tomorrow_io_home_daily` zeigen wieder belastbar `Heute` und `Morgen`.
- Der Frontend-Pfad muss die Forecast-Daten nicht mehr selbst zusammensuchen.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.1.3` angehoben.
