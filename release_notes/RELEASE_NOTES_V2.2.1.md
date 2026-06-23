# Release Notes V2.2.1

## Bewertung

- `set_covered` und `set_usage` schreiben jetzt einen eigenen Kontextverlauf, damit die Lernanalyse Zeitanteile wie `5 h offen / 19 h abgedeckt` oder gemischte Nutzung innerhalb eines Intervalls auswerten kann.
- Die Chlor-Stabilitaet bewertet neben dem rohen Verbrauch jetzt auch eine heuristisch kontextbereinigte Reihe. Offene Abdeckung und Nutzung werden zeitanteilig normalisiert, bevor die Stabilitaetsqualitaet bestimmt wird.
- Die Badetemperatur-Schwellen wurden angepasst, damit die Badebewertung besser zu den gewuenschten Zielbereichen passt.

## Filterwartung

- Ein Filterwechsel setzt jetzt automatisch auch den Reinigungszeitpunkt zurueck.
- Dadurch starten Reinigungsintervall, Statusanzeige und Filterwarnungen nach einem Wechsel wieder sauber bei null.

## Versionierung / Dokumentation

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.2.1` aktualisiert.
