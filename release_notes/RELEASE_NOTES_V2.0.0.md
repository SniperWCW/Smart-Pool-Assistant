# Release Notes V2.0.0

## Highlights

- Abschluss der grossen Architektur- und Frontend-Umbauten als Major Release.
- Die Lovelace-Karte rendert deutlich gezielter und reagiert nur noch auf relevante Entity-Aenderungen.
- PoolLab-, Wetter-, Chemie-, Wartungs- und Benachrichtigungslogik sind jetzt sauberer getrennt und leichter wartbar.

## Details

### Frontend Performance

- Der `hass`-Setter der Karte nutzt nun eine Render-Signatur fuer die relevanten Entitaeten.
- Unbeteiligte Home-Assistant-State-Updates loesen keinen kompletten DOM-Neuaufbau der Karte mehr aus.
- Die automatisch erkannte PoolLab-Abruf-Button-Entitaet wird gecacht.
- Lokale UI-Zustaende wie PoolLab-Abrufstatus bleiben weiterhin sofort sichtbar.

### Architekturstand

- Berechnung, Wartung, Benachrichtigungen, PoolLab-Cloud, PoolLab-BLE-Auswertung und Wetter-Normalisierung liegen in eigenen Modulen.
- Die Karte nutzt Backend-Forecast-Daten bevorzugt und zeigt Wetter kompakt einklappbar an.
- LayZSpa-Zieltemperatur-Steuerung, Nachmess-Workflow und manuelle PoolLab-Abrufe bleiben enthalten.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und die Release-Dateien wurden auf `2.0.0` angehoben.
