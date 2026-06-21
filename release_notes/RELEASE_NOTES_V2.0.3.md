# Release Notes V2.0.3

## Highlights

- Nachmessstatus springt jetzt schon nach einer einzelnen bestätigten Chemiezugabe auf **Warten auf erneute Messung**.
- Dosierempfehlungen werden konservativ auf vorhandene Messlöffel angepasst.

## Details

### Nachmess-Workflow

- Wenn Chlor, pH-Minus oder pH-Plus nach der letzten Messung protokolliert wurde, gilt die Messung als verbraucht.
- Der Gesamtstatus wechselt dann direkt auf `Warten auf erneute Messung`, auch wenn rechnerisch noch andere Chemie-Empfehlungen offen wären.
- Die Karte sperrt die betroffenen Eingaben weiterhin bis zur nächsten Messung.

### Dosierung

- Chlor, pH-Minus, pH-Plus und die Vor-Baden-Chlormenge werden auf praktische Kombinationen aus `1`, `2,5`, `5`, `7,5` und `15 g/ml` gerundet.
- Die Rundung ist konservativ und bleibt unter der berechneten Menge.
- Beispiel: Aus `8 g` werden `7,5 g`, statt auf eine höhere Menge aufzurunden.
- Die Lovelace-Karte zeigt die passende Messlöffel-Kombination direkt neben der Dosierempfehlung.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.0.3` aktualisiert.
