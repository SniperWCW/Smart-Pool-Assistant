# Release Notes V3.0.9

## Lernhistorie reparieren

- Neuer Service `smart_pool_assistant.repair_learning_history`.
- Der Service kann die Lernhistorie manuell neu abgleichen und optional vorher einen frischen PoolLab-Abruf ausloesen.

## Sample-Diagnose

- Die Reparatur schreibt jetzt direkt ins bestehende Diagnose-Log, welche Chlor-Dosier-Samples akzeptiert oder verworfen wurden.
- Bei verworfenen Samples werden Grund, Vorher-/Nachher-Messung, Zeitfenster und berechneter Faktor mitgeloggt.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `services.yaml`, `strings.json`, `translations/de.json` und diese Release Notes wurden auf `3.0.9` aktualisiert.
