# Release Notes V3.0.8

## Lernhistorie und Samples

- Chlor-, pH- und CYA-Messungen werden fuer die Lernlogik jetzt mit dem Zeitstempel ihrer echten Quelle gespeichert.
- Dadurch koennen manuelle, Cloud- und Bluetooth-Werte die Lernhistorie nicht mehr mit einem fremden Anzeige-Zeitstempel verschieben.

## Reparaturpfad

- Beim PoolLab-BLE-Abruf werden die im Geraet gespeicherten historischen Messungen in die Lernhistorie zurueckgespielt.
- Cloud-Messhistorie wird ebenfalls fuer Chlor und pH nachgetragen, soweit sie verfuegbar ist.
- Das hilft insbesondere bei verpassten Dosier-Samples nach einem frueheren Timestamp-Mismatch.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md` und diese Release Notes wurden auf `3.0.8` aktualisiert.
