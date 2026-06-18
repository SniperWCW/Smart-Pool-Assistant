# Release Notes V1.0.19

## Highlights

- Chlorberechnung fachlich neu aufgebaut: Alle Zuschlaege werden jetzt zuerst als zusaetzliche Zielkonzentration in `mg/l` modelliert und erst danach ueber das konfigurierte Poolvolumen in Gramm Produkt umgerechnet.
- Kleine Becken werden nicht mehr durch feste Grammzuschlaege ueberdosiert, gleichzeitig bleibt die Stoßchlorung fuer reale Whirlpool-Faelle im plausiblen Bereich.
- Die Breakdown-Anzeige in der Karte verwendet jetzt die neue Semantik mit Stoßchlor-Ziel und Zuschlaegen statt alter Faktor-Begriffe.

## Details

### Chlorlogik

- Basisbedarf weiter aus `Ziel - Ist`, Volumen und Wirkstoffanteil.
- Temperatur, offenes Becken und Nutzung werden als zusaetzlicher Konzentrationsbedarf in `mg/l` behandelt.
- Stoßchlorung arbeitet jetzt mit volumenbezogenen Stoß-Zielwerten statt mit einem multiplikativen Shock-Faktor.
- Mindestdosis und Vor-Baden-Empfehlung bleiben volumenbezogen.
- Die obere Begrenzung orientiert sich jetzt an einer maximalen Zielkonzentration statt an einem pauschalen Grammlimit.

### Frontend

- Breakdown-Texte an die neue Berechnungslogik angepasst.
- "Schock-Faktor" wurde in der Karte durch "Stoßchlor-Ziel" ersetzt.
- Weitere Zuschlaege werden klarer als Temperatur-, Offenes-Becken- und Nutzungszuschlag ausgewiesen.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md` und `manifest.json` auf `1.0.19` angehoben.
- Eigene Markdown-Release-Note fuer den Stand `V1.0.19` hinzugefuegt.
