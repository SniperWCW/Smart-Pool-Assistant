# Release Notes V2.1.1

## Highlights

- pH-Stabilität ergänzt die Chlor-Stabilität.
- Neue pH-Drift-Sensoren zeigen die bereinigte Entwicklung über 24h, 7d und 14d.
- Die Auswertung berücksichtigt bestätigte pH-Plus- und pH-Minus-Zugaben.

## Details

### pH-Stabilitätsanalyse

- Neue pH-Messpunkte werden lokal in der bestehenden Home-Assistant-Storage-Historie gespeichert.
- Bestätigte pH-Plus- und pH-Minus-Zugaben werden separat gespeichert.
- Zwischen zwei Messpunkten wird die erwartete Korrekturwirkung der pH-Aktionen herausgerechnet.
- Daraus entsteht eine bereinigte pH-Drift in `pH/d`.

### Neue Sensoren

- `sensor.pool_ph_drift_24h`
- `sensor.pool_ph_drift_7d`
- `sensor.pool_ph_drift_14d`
- `sensor.pool_ph_vorhersagequalitaet`
- `sensor.pool_ph_trend`
- `sensor.pool_ph_stabilitaet`

### Stabilitätsattribute

`sensor.pool_ph_stabilitaet` liefert unter anderem:

- `average_daily_drift`
- `min_daily_drift`
- `max_daily_drift`
- `samples`
- `prediction_quality`
- `prediction_quality_stars`
- `trend`
- `learning_phase`

### Ausreißerfilter

- Intervalle unter 3 Stunden oder über 7 Tagen werden ignoriert.
- Extreme Drift-Werte über `1 pH/d` werden ignoriert.
- Bis mindestens drei verwertbare Intervalle vorhanden sind, bleibt die Auswertung in der Lernphase.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.1.1` aktualisiert.
