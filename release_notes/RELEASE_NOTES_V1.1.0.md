# Release Notes V1.1.0

## Highlights

- Start der nachvollziehbaren Refactoring-Linie `1.1.x`.
- Wartungs- und History-Logik wurde aus `coordinator.py` nach `maintenance.py` verschoben.
- Chemische Dosier-, Nachmess- und Empfehlungslogik wurde nach `calculation.py` ausgelagert.

## Details

### Architektur

- `coordinator.py` bleibt die Home-Assistant-Schaltstelle fuer Refresh, Services, Storage, PoolLab-Abruf und Ergebniszusammenfuehrung.
- `maintenance.py` kapselt Activity-Texte, History-Normalisierung, Wartungsprotokollierung, Zeitberechnung und Filterstatus.
- `calculation.py` kapselt Chlor-/pH-Dosierung, Breakdown-Werte, Nachmessstatus und Empfehlungstext.

### Wartbarkeit

- Fachlogik kann kuenftig gezielter geaendert und getestet werden.
- Aenderungen an Dosierlogik oder Wartungshistorie beruehren weniger Home-Assistant-spezifischen Coordinator-Code.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.1.0` angehoben.
