# Release Notes V3.0.7

## CYA-Prognose

- Neue CYA-Historie mit modellierter Fortschreibung aus Messwerten, Chlorprodukt und geloggten Chlorzugaben.
- Die Karte zeigt jetzt einen modellierten aktuellen CYA-Wert, die geschaetzte Nettoveraenderung pro Tag und eine Prognose fuer `80 ppm` bzw. `100 ppm`.

## Wasserwechsel

- Wasserwechsel lassen sich jetzt direkt in der Karte oder ueber `smart_pool_assistant.log_maintenance` in `Litern` oder `Prozent` protokollieren.
- Diese Eintraege fliessen direkt in das CYA-Modell ein.

## Recorder / Attribute

- `sensor.pool_empfehlung` gibt nicht mehr die komplette interne Historie als Attribut aus.
- Stattdessen werden nur noch kompakte, UI-relevante Felder weitergereicht, um die Recorder-Grenze von `16384 bytes` nicht mehr zu reissen.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.7` aktualisiert.
