# Release Notes V2.1.10

## Bugfix

- Der zusätzliche 15-Sekunden-Timeout um `establish_connection(...)` wurde entfernt.
- Damit kann `bleak-retry-connector` beim PoolLab-BLE-Verbindungsaufbau wieder seine eigene Retry- und Safety-Timeout-Logik vollständig ausführen.
- Das robuste Cleanup aus `2.1.9` bleibt erhalten: Notifications werden best-effort gestoppt und die BLE-Verbindung wird explizit getrennt.

## Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.10` aktualisiert.
