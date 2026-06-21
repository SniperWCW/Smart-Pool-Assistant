# Release Notes V2.1.6

## Bugfix

- Die Stoßchlor-Semantik wurde korrigiert.
- `is_shock` wird jetzt nur gesetzt, wenn der gemessene Chlorwert im Stoßchlorbereich von `3,0 bis 5,0 mg/l` liegt.
- Zu niedrige Chlorwerte lösen weiterhin eine Stoßchlor-Empfehlung aus, gelten aber nicht mehr als aktive Stoßchlorung.

## Lovelace-Karte

- Die Badeampel zeigt nicht mehr `Stoßchlor aktiv`.
- Bei passendem Messwert erscheint stattdessen `Chlor im Stoßchlorbereich`.

## Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.6` aktualisiert.
