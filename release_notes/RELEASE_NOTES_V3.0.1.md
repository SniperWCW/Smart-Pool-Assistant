# Release Notes V3.0.1

## Dokumentation

- Die bisher sehr lange `README.md` wurde in eine klare Startseite mit Banner, Vorschau und Linkstruktur umgebaut.
- Neue Unterseiten fuer `Setup`, `Chemielogik`, `Karte und Demos` sowie `Entitaeten` teilen die Inhalte sinnvoll auf.
- README, FAQ und die neuen `docs/`-Seiten besitzen jetzt eine konsistente Navigation.

## Dosierlogik

- Der persoenliche Chlor-Dosierfaktor wird jetzt erst ab mindestens `5` verwertbaren Samples aktiv in die Chlorempfehlung eingerechnet.
- Ein Sample ist ein verwertbares Vorher-Messung/Zugabe/Nachmessung-Paar innerhalb des erlaubten Zeitfensters.
- Das reduziert Ueberreaktionen in kleinen Becken bei noch duenner Historie.

## UI

- Die Chlor-Prognose formuliert den Zustand jetzt sauberer, wenn der aktuelle Wert bereits unter `0,6 mg/l` liegt.

## Versionierung

- `manifest.json`, Frontend-Versionsanzeige, `README.md`, `FAQ.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md` und diese Release Notes wurden auf `3.0.1` aktualisiert.
