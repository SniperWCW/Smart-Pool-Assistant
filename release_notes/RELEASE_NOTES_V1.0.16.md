# Release Notes V1.0.16

## Highlights

- Live-BLE-Status in der Karte: **BT Verbindung** ist nur während eines aktiven PoolLab-Abrufs grün und springt nach dem Disconnect wieder auf rot.
- Fachlich sauberer Nachmess-Workflow: Nach bestätigter Chlor- oder pH-Zugabe zeigt die Integration **Warten auf erneute Messung**, bis neue Messwerte vorliegen.
- LayZSpa-Komfortfunktion: Die Zieltemperatur kann jetzt direkt in der Karte per `+` / `-` angepasst werden.

## Details

### BLE / PoolLab

- `bluetooth_connected` wird nicht mehr sticky gespeichert.
- Die Karte nutzt den echten Abrufzustand und den laufenden Client-Status für die Live-Anzeige.
- Der manuelle PoolLab-Abruf per Button bleibt BLE-first, Cloud bleibt weiterhin separat zyklisch aktualisiert.

### Chemie-Workflow

- Nach protokollierter Chlor-, pH-Minus- oder pH-Plus-Zugabe werden bestehende Empfehlungen nicht mehr erneut als frisch angezeigt.
- Stattdessen wechselt die Statusbox auf **Warten auf erneute Messung**.
- Die betroffenen Eingabefelder bleiben bis zur nächsten Messung deaktiviert.

### LayZSpa

- Neue optionale Steuerung über `layzspa.temp_target_control`.
- Unterstützt `number.*` und `climate.*` als Zieltemperatur-Entität.
- Die Karte respektiert Schrittweite sowie Min-/Max-Grenzen der Zielentität.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md` und `manifest.json` auf `1.0.16` angehoben.
- Eigene Markdown-Release-Note für den Stand `V1.0.16` hinzugefügt.
