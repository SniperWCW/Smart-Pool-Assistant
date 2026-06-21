# Release Notes V2.1.7

## Neu

- Optionaler Pool-/LayZSpa-Verbindungsmonitor im Config Flow und Options Flow.
- Konfigurierbarer Binary Sensor fuer die Verbindung, z. B. `binary_sensor.layzspa_connection`.
- Konfigurierbare Offline-Wartezeit in Minuten, Standard `5`.

## Benachrichtigungen

- Wenn die Verbindung nach der Wartezeit weiterhin `off` oder `unavailable` ist, wird eine Meldung an die hinterlegten Notify-Ziele gesendet.
- Optional wird zusaetzlich eine Home-Assistant-Persistent-Notification erstellt.
- Pro Offline-Phase wird nur einmal benachrichtigt; sobald der Sensor wieder `on` ist, wird der Alarmstatus zurueckgesetzt.
- Mobile-App-Daten wie Tag, Gruppe, Icon, Farbe und Dashboard-Link werden fuer kompatible Notify-Dienste mitgegeben.

## Verbesserungen

- Persistente Chemie-Follow-up-Erinnerungen wurden robuster gemacht, damit sie nach Neustarts korrekt nachgeholt und nicht doppelt versendet werden.
- Die bereits vorbereitete LayZSpa-Heizzeit-Prognose ist in diesem Release enthalten.

## Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.7` aktualisiert.
