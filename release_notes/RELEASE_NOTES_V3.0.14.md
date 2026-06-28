# Release Notes V3.0.14

## Chlorprodukt und Wirkstoff

- Der Wirkstoff-Fallback fuer `anorganisch` nutzt jetzt `0.65` statt eines fachlich zu hohen `1.00`-Defaults.
- Die Logik fuer Chlorprodukt-Typ und Wirkstoffanteil ist jetzt zwischen Config Flow, Berechnung, Lernsystem und CYA-Modell zentral vereinheitlicht.
- Die Empfehlung meldet `CYA hoch` ab ueber `80 ppm` jetzt auch dann konsistent, wenn kuenftig anorganisch gechlort wird.

## Dokumentation

- Die Doku beschreibt den Wirkstoffanteil jetzt durchgaengig als produktabhaengigen Realwert laut Etikett.
- Beispiele fuer typische Bereiche wurden auf `0.56` organisch, `0.65-0.70` Calciumhypochlorit und `0.12-0.15` Natriumhypochlorit aktualisiert.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.14` aktualisiert.
