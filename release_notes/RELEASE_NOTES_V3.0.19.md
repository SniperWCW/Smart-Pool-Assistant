# Release Notes V3.0.19

## Anorganisches Chlor

- Bei `anorganisch` trennt die Integration jetzt fachlich zwischen einer minimalen Vor-Baden-Korrektur und der eigentlichen Chlorzugabe nach der Nutzung.
- `chlor_pre` hebt bei Bedarf nur bis in den sicheren Mindestbereich an.
- `chlor_dose` bleibt die Hauptdosierung fuer die aktive Desinfektion nach dem Baden.

## Empfehlung und Karte

- Die Empfehlungstexte fuer niedrige Chlorwerte wurden fuer anorganisches Chlor angepasst.
- Die Lovelace-Karte zeigt jetzt getrennt an, was vor dem Baden nur minimal korrigiert werden sollte und was nach der Nutzung aktiv dosiert werden soll.

## Benennung

- Die UI benennt die beiden Werte jetzt klarer als `Chlor Hauptdosierung` und `Chlor vor Baden Minimum`.
- Die bestehenden Entity-IDs bleiben dabei aus Kompatibilitaetsgruenden unveraendert.

## Release-Artefakte

- `manifest.json`, `README.md`, `Changelog.md`, `TECHNISCHE_DOKUMENTATION.md`, `pool-chemistry-card.js` und diese Release Notes wurden auf `3.0.19` aktualisiert.
