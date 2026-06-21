# Release Notes V2.1.4

## Highlights

- Die Lovelace-Karte zeigt bei zu hohem Chlor keine doppelte rote Warnbox mehr.
- Die Texte `Chlor zu hoch` und `Chlor deutlich zu hoch` wurden vereinheitlicht.

## Details

### Status und Badeampel

- Wenn der allgemeine Status und die Badeampel denselben kritischen Chlor-Grund melden, wird die Badeampel in die Statusbox integriert.
- Die kombinierte Box zeigt weiterhin klar `Nicht empfohlen`, vermeidet aber die doppelte rote Darstellung.

### Chlor-Warntext

- Die Badeampel nutzt bei stark erhöhtem Chlor jetzt ebenfalls `Chlor zu hoch`.
- Bestehende ältere Texte werden beim Abgleich tolerant normalisiert, damit die Zusammenführung robust bleibt.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.4` aktualisiert.
