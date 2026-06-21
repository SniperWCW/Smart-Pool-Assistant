# Release Notes V1.0.23

## Highlights

- Forecast-Logspam in Home Assistant behoben.
- Robusteres Nachladen von Tagesvorhersagen in der Pool-Karte.
- Kein fehlerhafter Service-Aufruf für Wetter-Forecasts mehr aus dem Frontend.

## Details

### Forecast-Fix

- Die Lovelace-Karte verwendet für das Nachladen von Tagesvorhersagen im Frontend nicht mehr den problematischen Service-Pfad `weather.get_forecasts`.
- Damit entfallen WebSocket-Fehler wie `The action requires responses and must be called with return_response=True`, die bei wiederholten Nachladeversuchen das Log fluten konnten.

### Stabilität

- Wenn die Wetter-Entity kein direktes `forecast`-Attribut besitzt, nutzt die Karte nur noch den Forecast-Endpunkt.
- Bei leerem Ergebnis greift zusätzlich ein Retry-Cooldown, damit keine sofortige Endlosschleife aus erneuten Forecast-Anfragen entsteht.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.0.23` angehoben.
