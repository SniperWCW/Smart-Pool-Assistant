# Release Notes V2.0.0

## Highlights

- Abschluss der großen Architektur- und Frontend-Umbauten als Major Release.
- Die Lovelace-Karte rendert deutlich gezielter und reagiert nur noch auf relevante Entity-Änderungen.
- PoolLab-, Wetter-, Chemie-, Wartungs- und Benachrichtigungslogik sind jetzt sauberer getrennt und leichter wartbar.

## Details

### Frontend Performance

- Der `hass`-Setter der Karte nutzt nun eine Render-Signatur für die relevanten Entitäten.
- Unbeteiligte Home-Assistant-State-Updates lösen keinen kompletten DOM-Neuaufbau der Karte mehr aus.
- Die automatisch erkannte PoolLab-Abruf-Button-Entität wird gecacht.
- Lokale UI-Zustände wie PoolLab-Abrufstatus bleiben weiterhin sofort sichtbar.

### Architekturstand

- Berechnung, Wartung, Benachrichtigungen, PoolLab-Cloud, PoolLab-BLE-Auswertung und Wetter-Normalisierung liegen in eigenen Modulen.
- Die Karte nutzt Backend-Forecast-Daten bevorzugt und zeigt Wetter kompakt einklappbar an.
- LayZSpa-Zieltemperatur-Steuerung, Nachmess-Workflow und manuelle PoolLab-Abrufe bleiben enthalten.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und die Release-Dateien wurden auf `2.0.0` angehoben.
