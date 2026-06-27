# Release Notes V3.0.4

## CYA-Anzeige

- Der PoolLab-Abruf selbst funktionierte bereits korrekt, inklusive eingelesenem CYA-Wert.
- Der fehlende Messwert in der Lovelace-Karte lag an einem geschlossenen Attributpfad: `sensor.pool_empfehlung` reicht jetzt `cyanuric_acid` und `cyanuric_acid_source` sauber an das Frontend weiter.

## Ergebnis

- CYA/Cyanursaeure kann nach erfolgreichem PoolLab-Abruf jetzt auch in **Aktuelle Messwerte** erscheinen.

## FAQ

- Die FAQ erklaert jetzt klarer die Trennung zwischen Verbrauchslernen (`Messung -> Messung`) und Dosierwirkungslernen (`Messung -> Zugabe -> Nachmessung`).

## Release-Artefakte

- `sensor.py`, `FAQ.md`, `manifest.json`, `README.md`, `Changelog.md` und diese Release Notes wurden auf `3.0.4` aktualisiert.
