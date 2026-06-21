# Release Notes V1.0.19

## Highlights

- Chlorberechnung fachlich neu aufgebaut: Alle Zuschläge werden jetzt zuerst als zusätzliche Zielkonzentration in `mg/l` modelliert und erst danach über das konfigurierte Poolvolumen in Gramm Produkt umgerechnet.
- Kleine Becken werden nicht mehr durch feste Grammzuschläge überdosiert, gleichzeitig bleibt die Stoßchlorung für reale Whirlpool-Fälle im plausiblen Bereich.
- Die Breakdown-Anzeige in der Karte verwendet jetzt die neue Semantik mit Stoßchlor-Ziel und Zuschlägen statt alter Faktor-Begriffe.

## Details

### Chlorlogik

- Basisbedarf weiter aus `Ziel - Ist`, Volumen und Wirkstoffanteil.
- Temperatur, offenes Becken und Nutzung werden als zusätzlicher Konzentrationsbedarf in `mg/l` behandelt.
- Stoßchlorung arbeitet jetzt mit volumenbezogenen Stoß-Zielwerten statt mit einem multiplikativen Shock-Faktor.
- Mindestdosis und Vor-Baden-Empfehlung bleiben volumenbezogen.
- Die obere Begrenzung orientiert sich jetzt an einer maximalen Zielkonzentration statt an einem pauschalen Grammlimit.

### Frontend

- Breakdown-Texte an die neue Berechnungslogik angepasst.
- "Schock-Faktor" wurde in der Karte durch "Stoßchlor-Ziel" ersetzt.
- Weitere Zuschläge werden klarer als Temperatur-, Offenes-Becken- und Nutzungszuschlag ausgewiesen.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md` und `manifest.json` auf `1.0.19` angehoben.
- Eigene Markdown-Release-Note für den Stand `V1.0.19` hinzugefügt.
