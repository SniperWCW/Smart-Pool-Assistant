# Release Notes V3.0.15

## Schockchlorung

- Neuer Config-Wert `chlor_shock_max` fuer die maximale automatische Schockchlorung in `mg/l`.
- Die Chlorempfehlung respektiert diese Obergrenze jetzt auch dann sauber, wenn Temperatur, offene Abdeckung oder Nutzung weitere Zuschlaege ausloesen.
- Damit lassen sich Whirlpool-Setups jetzt direkt auf Werte wie `3.0 mg/l` begrenzen.

## Benennung und UI

- Frontend, Empfehlung, Config-Texte und Doku verwenden jetzt durchgaengig `Schockchlorung` statt `Stoßchlor`.
- Die Breakdown-Anzeige in der Karte nennt das Ziel jetzt `Schockchlorungsziel`.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.15` aktualisiert.
