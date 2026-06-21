# Release Notes V2.1.2

## Highlights

- Die Lovelace-Karte zeigt jetzt eine eigene einklappbare Sektion **Stabilität**.
- Chlor- und pH-Lernfortschritt sind direkt im Frontend sichtbar.
- Fehlende Lernwerte werden lesbar angezeigt, statt als rohe `unknown`-Werte zu erscheinen.

## Details

### Stabilitätssektion

- Die Kopfzeile fasst Chlor und pH kompakt zusammen.
- Während der Lernphase zeigt die Karte den Fortschritt als `0/3`, `1/3` oder `2/3` verwertbare Intervalle.
- Sobald genügend Daten vorhanden sind, zeigt die Kopfzeile Status und Vorhersagequalität.

### Detailansicht

Aufgeklappt zeigt die Karte:

- Chlorverbrauch über 24h, 7d und 14d
- Chlor-Minimum und -Maximum
- persönlichen Chlorfaktor
- pH-Drift über 24h, 7d und 14d
- pH-Minimum und -Maximum
- pH-Trend

### Fallbacks

- Fehlende Zahlen werden als `Nicht genügend Daten` dargestellt.
- Fehlende Qualitätsbewertung wird als `Noch keine Bewertung` dargestellt.
- Die Anzeige füllt sich automatisch, sobald genügend Messintervalle gesammelt wurden.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.1.2` aktualisiert.
