# Release Notes V3.0.10

## Dosier-Sample robuster

- Fuer die Chlor-Dosierqualitaet wird nicht mehr blind die erste Nachmessung nach der Zugabe verwendet.
- Stattdessen zaehlt jetzt die erste gueltige Nachmessung im Fenster von `30 Minuten` bis `12 Stunden`.
- Eine zu fruehe Messung blockiert damit kein spaeteres gueltiges Sample mehr.

## Benachrichtigungen

- Nach jeder Chlorzugabe wird jetzt das gueltige Nachmessfenster als Hinweis gesendet.
- Bei erfolgreichem oder verworfenem Dosier-Sample wird eine Rueckmeldung mit Grund verschickt, zum Beispiel `zu frueh`, `zu spaet` oder `Faktor ausserhalb des Bereichs`.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `chlorine_learning.py`, `coordinator.py` und diese Release Notes wurden auf `3.0.10` aktualisiert.
