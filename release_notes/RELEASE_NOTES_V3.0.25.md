# Release Notes V3.0.25

## Vor-Baden-Planung

- Die Lovelace-Karte hat im Bereich `Status & Nutzung` jetzt ein neues Feld `Baden in`.
- Darueber kann ein Badezeitpunkt in Stunden gesetzt werden, zum Beispiel `3` oder `4.5`.
- Die Vor-Baden-Dosis `chlor_pre` richtet sich dann auf den geplanten Badezeitpunkt statt nur auf den aktuellen Messmoment aus.
- Fuer die Abschaetzung nutzt die Integration bevorzugt die vorhandene Chlor-Prognose und faellt sonst konservativ auf einen Basisverlust zurueck.

## Karte und Bedienung

- Die Nutzungswahl in der Karte wurde auf `Keine` und `Party` reduziert.
- `Normal` bleibt intern und ueber den Service weiter unterstuetzt, ist aber nicht mehr Teil des Standard-Workflows in der Karte.
- Der Badeplan laeuft nach dem gesetzten Zeitpunkt automatisch aus und faellt dann wieder auf normalen Betrieb ohne Zeitvorgabe zurueck.

## Release-Artefakte

- `manifest.json`, `README.md`, `FAQ.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `docs/CHEMISTRY.md`, `docs/CARD_AND_DEMOS.md`, `docs/ENTITIES.md` und diese Release Notes wurden auf `3.0.25` aktualisiert.
