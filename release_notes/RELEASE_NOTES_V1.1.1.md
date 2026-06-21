# Release Notes V1.1.1

## Highlights

- PoolLab-Cloud-Abruf wurde aus `coordinator.py` nach `poollab_cloud.py` verschoben.
- Notification- und Filterwarnungslogik wurde aus `coordinator.py` nach `notifications.py` verschoben.
- Optional kann ein zweiter Notify-Dienst konfiguriert werden, damit Meldungen an zwei Ziele gehen.
- Alle Release-Notes liegen nun gesammelt im Ordner `release_notes/`.
- Die Refactoring-Linie `1.1.x` bleibt damit klar nachvollziehbar.

## Details

### PoolLab Cloud

- `poollab_cloud.py` kapselt den GraphQL-Request zur LabCom-Cloud.
- Cloud-Messwerte werden dort sortiert, normalisiert und als strukturiertes Ergebnis an den Coordinator zurückgegeben.
- Der Coordinator entscheidet weiterhin über Quellenpriorität, Cache-Fallbacks und UI-Daten.

### Benachrichtigungen

- `notifications.py` kapselt Persistent Notifications, konfigurierte Notify-Services, Follow-up-Hinweise und Filterwarnungen.
- Neben `notify_service` kann optional `notify_service_2` gesetzt werden.
- Beide Notify-Dienste erhalten dieselben Meldungen; doppelte Ziele werden nur einmal versendet.
- Die Filterwarnungen aktualisieren weiterhin die bestehenden `last_notified_*` History-Felder.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.1.1` angehoben.
