# Release Notes V1.0.22

## Highlights

- Wettervorhersage in der Pool-Karte funktioniert jetzt robuster mit Providern wie Tomorrow.io.
- Die Karte kann Tages-Forecasts aktiv nachladen, wenn die Wetter-Entity kein direktes `forecast`-Attribut bereitstellt.
- Windwerte werden mit der tatsächlichen Einheit der Wetter-Entity angezeigt.

## Details

### Wetteranzeige

- Die Lovelace-Karte prüft weiterhin zuerst `attributes.forecast` der konfigurierten `weather`-Entität.
- Wenn dort keine Tagesvorhersage vorhanden ist, versucht die Karte die Daten zusätzlich über Home Assistants Forecast-Endpunkt nachzuladen.
- Dadurch funktionieren Entitäten wie `weather.tomorrow_io_home_daily` auch dann, wenn die Forecast-Daten nicht direkt als Attribut an der Entity hängen.

### Einheiten

- Die Windanzeige orientiert sich jetzt an `wind_speed_unit` der Wetter-Entity.
- Tomorrow.io-Werte wie `17.28` werden damit korrekt als `km/h` statt irrtümlich als `m/s` dargestellt.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.0.22` angehoben.
