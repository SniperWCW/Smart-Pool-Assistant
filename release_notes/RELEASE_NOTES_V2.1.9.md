# Release Notes V2.1.9

## Bugfix

- Der PoolLab-BLE-Client raeumt nach Timeout oder Abbruch jetzt robuster auf.
- Notifications werden im Cleanup best-effort gestoppt und die BLE-Verbindung wird explizit getrennt.
- Der von `establish_connection(...)` gelieferte Client wird direkt verwendet; eine doppelte Connect-/Disconnect-Verwaltung ueber `async with client` wurde entfernt.
- Der BLE-Verbindungsaufbau hat jetzt ein eigenes Timeout, damit Home Assistants Bluetooth-Connect-State bei ESP32-Bluetooth-Proxies sauberer bleibt.

## Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.9` aktualisiert.
