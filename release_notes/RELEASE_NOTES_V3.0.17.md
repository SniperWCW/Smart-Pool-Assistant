# Release Notes V3.0.17

## CYA-Block

- Bei zu hohem CYA nennt die Karte jetzt eine konkrete Wasserwechsel-Schaetzung in Litern und Prozent, basierend auf dem konfigurierten Beckenvolumen.
- Bei CYA im Zielbereich oder darunter zeigt der Block stattdessen nur noch den letzten Messwert mit Datum.

## Messzeitstempel

- Die Messwertetabelle verwendet jetzt eigene Zeitstempel fuer Chlor, pH, Temperatur und CYA.
- Dadurch fuehrt eine einzelne neue pH-Messung nicht mehr dazu, dass Chlor oder CYA optisch denselben frischen Messzeitpunkt bekommen.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.17` aktualisiert.
