# Release Notes V3.0.21

## Options-Flow und Validierung

- Leere optionale Entity-Selektoren werden jetzt im Reconfigure-/Options-Flow sauber als nicht gesetzt behandelt.
- Die Validierung prueft beim Speichern nicht mehr nur das aktuelle `user_input`, sondern die effektive Gesamtkonfiguration inklusive bereits vorhandener Werte.

## Gemischte Messhistorie

- Die Lovelace-Karte zeigt die letzten Messungen jetzt gemeinsam aus `API`, `BLE` und `Manuell`.
- Jede Historienzeile enthaelt Quelle, Parameter, Wert und Zeitstempel.
- Das Backend normalisiert Parameternamen, entfernt Duplikate und haelt bis zu 40 aktuelle Eintraege fuer die Anzeige vor.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md` und diese Release Notes wurden auf `3.0.21` aktualisiert.
