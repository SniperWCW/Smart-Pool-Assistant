# Release Notes V2.1.0

## Highlights

- Die Integration lernt ab jetzt den persoenlichen Chlorverbrauch des Pools.
- Neue Sensoren zeigen Chlorverbrauch ueber 24h, 7d und 14d.
- Ein neuer Stabilitaets-Sensor bewertet Lernphase, Verbrauchsspanne und Vorhersagequalitaet.

## Details

### Lernhistorie

- Neue Chlor-Messpunkte werden lokal in der bestehenden Home-Assistant-Storage-Historie gespeichert.
- Bestaetigte Chlorzugaben werden separat gespeichert.
- Zwischen zwei Messpunkten wird die rechnerische Wirkung der dazwischenliegenden Chlorzugaben beruecksichtigt.
- Die Analyse bleibt lokal und nutzt keine externe API.

### Neue Sensoren

- `sensor.pool_chlorverbrauch_24h`
- `sensor.pool_chlorverbrauch_7d`
- `sensor.pool_chlorverbrauch_14d`
- `sensor.pool_persoenlicher_chlorfaktor`
- `sensor.pool_chlor_vorhersagequalitaet`
- `sensor.pool_chlor_stabilitaet`

### Stabilitaetsattribute

`sensor.pool_chlor_stabilitaet` liefert unter anderem:

- `average_daily_loss`
- `min_daily_loss`
- `max_daily_loss`
- `samples`
- `prediction_quality`
- `prediction_quality_stars`
- `personal_chlor_factor`
- `learning_phase`

### Ausreisserfilter

- Intervalle unter 3 Stunden oder ueber 7 Tagen werden ignoriert.
- Negative Verbrauchswerte werden ignoriert.
- Extreme Verbrauchswerte ueber `5 mg/l/d` werden ignoriert.
- Bis mindestens drei verwertbare Intervalle vorhanden sind, bleibt die Auswertung in der Lernphase.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.1.0` aktualisiert.
