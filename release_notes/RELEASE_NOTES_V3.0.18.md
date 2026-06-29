# Release Notes V3.0.18

## BLE-Messzeiten

- Der neueste BLE-Chemiewert wird weiterhin auf den Abrufzeitpunkt gelegt.
- Aeltere Chlor-, Temperatur- und CYA-Werte behalten jetzt aber ihren relativen Abstand dazu, statt ebenfalls als frisch gemessen zu erscheinen.

## Anzeige pro Parameter

- Ein einzelner neuer pH-Wert kann damit sichtbar neuer sein als aeltere gespeicherte Chlor- oder CYA-Werte aus demselben PoolLab-Abruf.
- Die Messwertetabelle trennt wieder nachvollziehbar, was im aktuellen Messlauf frisch war und was nur aus dem Geraetespeicher stammt.

## Konsistenz

- Die angezeigten BLE-Zeitstempel folgen jetzt demselben relativen Normalisierungsmodell wie das Backfill fuer die Lernhistorie.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.18` aktualisiert.
