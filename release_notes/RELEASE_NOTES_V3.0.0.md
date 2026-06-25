# Release Notes V3.0.0

## Basis

- `V3.0.0` bringt den lokalen Entwicklungsstand und den bereits manuell veröffentlichten GitHub-Stand wieder sauber zusammen.
- Die Version bündelt die veröffentlichten `2.2.3`-Änderungen mit den noch lokal fehlenden Fixes in einem konsistenten neuen Ausgangspunkt.

## Lernlogik

- Der persönliche Chlor-Dosierfaktor nutzt jetzt nur noch zeitnahe Messpaare.
- Die Vorher-Messung darf höchstens `12 h` vor der Zugabe liegen.
- Die Nachmessung darf höchstens `12 h` nach der Zugabe liegen.
- Späte Nachmessungen ziehen den gelernten Wirkstoff damit nicht mehr unplausibel nach unten.

## Diagnose / Support

- Die Chlor-Breakdown-Ansicht zeigt Volumen, gelernten Dosierfaktor und effektiven Wirkstoff direkt im Empfehlungsblock.
- Neue `FAQ.md` sammelt typische Fälle wie `20 g trotz 0,916 m³`, Lernphase, Volumenabweichungen und späte Nachmessungen.

## Versionierung / Dokumentation

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `FAQ.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `3.0.0` aktualisiert.
