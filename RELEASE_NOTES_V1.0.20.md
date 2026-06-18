# Release Notes V1.0.20

## Highlights

- Fehler in der neuen Chlorlogik behoben: Der Nutzungsmodus (`none`, `normal`, `party`) wirkt jetzt auch dann auf die finale Dosiermenge, wenn gleichzeitig ein Stoßchlor-Ziel aktiv ist.
- Die Breakdown-Anzeige war bereits unterschiedlich, die Endmenge blieb aber fälschlich gleich. Das ist korrigiert.

## Details

### Chlorlogik

- Bisher wurde bei sehr niedrigem Chlorwert das Stoßchlor-Ziel per `max(...)` so angewendet, dass der Nutzungszuschlag in der Endmenge wieder neutralisiert wurde.
- Jetzt wird zuerst das Basisziel inklusive Temperatur und Abdeckung mit dem Stoßchlor-Ziel abgeglichen.
- Der Nutzungszuschlag wird danach zusätzlich auf das resultierende Ziel aufgeschlagen.

### Verifiziertes Verhalten

- Für den gezeigten Fall mit `0,916 m³` ergibt die korrigierte Berechnung:
- `keine Nutzung`: ca. `8,1 g`
- `normal`: ca. `8,9 g`
- `party`: ca. `9,7 g`

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und Frontend-Versionsbanner auf `1.0.20` angehoben.
- Eigene Markdown-Release-Note fuer den Stand `V1.0.20` hinzugefuegt.
