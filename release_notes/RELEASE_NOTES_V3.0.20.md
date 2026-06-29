# Release Notes V3.0.20

## Wetteranzeige

- Daily-Forecasts mit `precipitation` bzw. `precipitation_amount` werden in der Lovelace-Karte jetzt wieder sichtbar dargestellt.
- Die Wetterkarte unterscheidet dabei sauber zwischen Regenwahrscheinlichkeit in `%` und Niederschlagsmenge in `mm`.

## UV-Konfiguration

- Ein separater `uv_sensor` bleibt weiterhin optional.
- Wenn die Wetter-Entitaet bereits `uv_index` im Forecast liefert, kann der zuvor gesetzte UV-Sensor im Reconfigure-/Options-Flow jetzt wieder sauber entfernt werden.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `config_flow.py`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.20` aktualisiert.
