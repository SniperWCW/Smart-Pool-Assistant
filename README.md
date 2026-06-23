# Smart Pool Assistant

Der **Smart Pool Assistant** ist eine Home Assistant Integration für Pool- und Whirlpool-Pflege. Die Integration kombiniert PoolLab BLE, PoolLab Cloud, manuelle Sensoren, Dosierlogik, Wartungshistorie und eine eigene Lovelace-Karte in einer zentralen Empfehlung.

**Aktueller Release-Stand: V2.2.1**

## Hauptfunktionen

- Präzise Chlor-Berechnung über volumenbezogene Zielbereiche mit Stoßchlor-Ziel, Temperatur-, Abdeckungs- und Nutzungszuschlag.
- Transparente Dosierlogik mit Breakdown direkt in der Lovelace-Karte.
- Konservative Dosierempfehlungen passend zu Messlöffeln mit `1`, `2,5`, `5`, `7,5` und `15 g/ml`.
- Lernende Chloranalyse mit persönlichem Chlorfaktor, persönlichem Dosierfaktor, Verbrauch über 24h/7d/14d und kontextbereinigter Stabilitätsbewertung.
- Neue Chlor-Prognose mit geschätzter Zeit bis zur Zieluntergrenze oder bis `0,6 mg/l`, inklusive Konfidenz, Kontextgewichtung und zeitanteiliger Bewertung von Abdeckung und Nutzung.
- pH-Stabilitätsanalyse mit bereinigter Drift über 24h/7d/14d, Trend und Vorhersagequalität.
- Optionale Wetterintegration über eine Home-Assistant-`weather`-Entität mit Vorhersage für heute und morgen, inklusive Backend-Forecast-Fallback für Provider wie Tomorrow.io.
- Optionaler separater `UV`-Sensor für Provider, die den UV-Index nicht im Daily-Forecast liefern.
- Die Wetterkarte nutzt bevorzugt vom Backend vorbereitete Forecast-Tagesdaten und fällt erst danach auf heutige Coordinator-Wetterwerte zurück.
- Die Wettersektion ist jetzt einklappbar und zeigt in der Kopfzeile eine kompakte Heute-Zusammenfassung.
- Optimierte Lovelace-Karte: rendert nur noch bei relevanten Entity-Änderungen neu.
- Badeampel in der Lovelace-Karte: `Baden empfohlen`, `Baden möglich` oder `Nicht empfohlen` anhand von Chemie-, Nachmess-, Temperatur- und Wetterdaten.
- Übersichtlichere Messwertetabelle mit getrennten Spalten für `Messwert`, `Ist`, `Ziel` und `Quelle`.
- Verbesserte mobile Darstellung für Wetter-Kopfzeile und aktuelle Messwerte.
- Konservativer Wetter-Einfluss auf Chlor: hoher UV-Index kann den Zielbedarf leicht erhöhen, Regen erzeugt einen Nachmess-Hinweis.
- Direkte Bluetooth-Anbindung für **PoolLab 1.0** inklusive Batteriestatus und Nutzung über ESP Bluetooth Proxy.
- Manueller PoolLab-Abruf über `button.poollab_messwerte_abrufen` statt zyklischem BLE-Polling.
- Weiterhin zyklischer Cloud-Abruf über das konfigurierbare Cloud-Update-Intervall.
- Abrufbutton direkt in der Messwertetabelle der Karte, inklusive Status-, Fehler- und Cooldown-Anzeige.
- Live-BLE-Status: **BT Verbindung** ist nur während eines aktiven BLE-Abrufs grün und springt nach dem Disconnect wieder auf rot.
- Fachlich sauberer Nachmess-Workflow: Nach jeder bestätigten Chlor- oder pH-Zugabe zeigt die Integration **Warten auf erneute Messung**, bis neue Werte vorliegen.
- Getrennte Quellenlogik für Bluetooth, Cloud, manuelle Sensoren und Speicher-Fallback.
- Persistente Historie für letzte Werte, letzte Aktionen, letzte Cloud-Messwerte und Filterwartung.
- LayZSpa-Panel mit Anzeige von Verbindung, RSSI, Pumpe, Heizung, Luftblasen, Ist-/Zieltemperatur, optionaler Zieltemperatur-Steuerung per `+` / `-` und Heizzeit-Prognose `Auf Wunschtemperatur`.
- Benachrichtigungen für Chemie-Follow-up, Filterwartung und optional verlorene Pool-Verbindung, optional an zwei Notify-Ziele.
- Re-Konfiguration über Config Flow / Options Flow.

## Installation

### Über HACS

1. Öffne **HACS** in Home Assistant.
2. Gehe auf **Benutzerdefinierte Repositories**.
3. Füge dieses Repository als Typ `Integration` hinzu.
4. Installiere **Smart Pool Assistant**.
5. Starte Home Assistant neu.

### Manuell

1. Kopiere `custom_components/smart_pool_assistant` in deinen `custom_components` Ordner.
2. Starte Home Assistant neu.

## Konfiguration

Die Einrichtung erfolgt über **Einstellungen > Geräte & Dienste > Integration hinzufuegen**.

Wichtige Konfigurationspunkte:

- **BLE-Adresse**: PoolLab 1.0 für manuellen BLE-Abruf.
- **PoolLab API-Key**: Aktiviert die zyklische Cloud-Aktualisierung und dient ohne BLE optional auch als manuelle Abrufquelle.
- **Cloud-Update-Intervall**: Zyklischer Cloud-Abruf in Minuten, Standard `5`, Bereich `1-60`.
- **Manuelle Sensoren**: Chlor, pH und optional Temperatur.
- **Pumpe**: Optionaler `switch.*` oder `binary_sensor.*` für Pumpenlaufzeit in der Chlor-Prognose.
- **Pool-Verbindung**: Optionaler Binary Sensor, der nach konfigurierbarer Offline-Wartezeit eine Benachrichtigung ausloest.
- **Poolvolumen**: Wassermenge in m3.
- **Zielbereiche**: Chlor Minimum/Maximum und pH Minimum/Maximum.
- **Wirkstoffanteil**: Wirkstoffanteil des Chlorprodukts.
- **pH-Dosierungen**: pH-Minus in ml und pH-Plus in g.
- **Benachrichtigungsdienst(e)** und **Follow-up-Zeit**.
- **Filter-Intervalle** und Warnschwellen.

## PoolLab-Abruf

- Die Integration verbindet sich nicht mehr zyklisch mit dem PoolLab.
- Für einen BLE-Abruf: PoolLab einschalten, Messung oder Zero durchführen, kurz warten und dann `button.poollab_messwerte_abrufen` druecken.
- Der gleiche Abruf ist direkt in der Lovelace-Karte unter **Aktuelle Messwerte** integriert.
- Nach Erfolg gilt ein Cooldown von 20 Sekunden, nach Fehlern 30 Sekunden.
- Cloud-Daten laufen weiterhin zyklisch über das konfigurierte Intervall weiter, ohne dass BLE automatisch verbunden wird.
- **BT Verbindung** zeigt nur den aktuell laufenden BLE-Connect an. Nach dem Lesen trennt die Integration bewusst wieder.
- Diagnose-Logs werden in `smart_pool_assistant_logs/smart_pool_assistant.log` im Home-Assistant-Konfigurationsverzeichnis geschrieben und automatisch rotiert.

## Nachmess-Workflow nach Chemiezugabe

- Wenn du Chlor, pH-Minus oder pH-Plus in der Karte bestaetigst, gilt die bisherige Messung fachlich als verbraucht.
- Solange noch keine neue Messung eingelesen wurde, zeigt die Integration **Warten auf erneute Messung** statt denselben Dosiervorschlag erneut an.
- Die betroffenen Eingabefelder bleiben bis zur nächsten Messung gesperrt.
- Die Follow-up-Erinnerung bleibt aktiv und passt weiterhin zum Nachmess-Ablauf.

## Berechnungslogik

### Chlor

Die Chlorempfehlung berücksichtigt:

1. Basisbedarf aus `untere Zielgrenze - Ist` in `mg/l`, wenn Chlor unter dem Zielbereich liegt.
2. Temperatur-Zuschlag ab 28 C bzw. 32 C.
3. Zuschlag für offene Abdeckung.
4. Nutzungsmodus (`none`, `normal`, `party`) als zusätzlicher Konzentrationsbedarf, der auch bei aktivem Stoßchlor-Ziel zusätzlich auf die Endmenge wirkt.
5. Stoßchlor-Ziele bei sehr niedrigen Chlorwerten.
6. Umrechnung der benötigten Gesamtkonzentration über das konfigurierte `Poolvolumen (m³)` und den Wirkstoffanteil in Gramm Produkt.
7. Zielbereich-Check, damit innerhalb des Bereichs oder bei Überdosierung `0 g` empfohlen wird.

### pH

Die pH-Berechnung ermittelt anhand Zielbereich, Poolvolumen und Produktdosierung die benötigte Menge an:

- **PH-Minus** in ml
- **PH-Plus** in g

### Lernende Chloranalyse

Die Integration speichert neue Chlor-Messpunkte und bestätigte Chlorzugaben in der lokalen Home-Assistant-Storage-Historie. Dabei werden zusätzliche Kontextdaten wie Temperatur, Abdeckung, Nutzungsmodus, Wetter/UV und optional Pumpenlaufzeit mitgespeichert. Statuswechsel von Abdeckung und Nutzung laufen jetzt zusätzlich als eigener Verlauf mit, sodass ein Intervall zeitanteilig ausgewertet werden kann, z. B. `5 h offen / 19 h abgedeckt` oder `2 h normal genutzt`.

Berechnet werden:

- Chlorverbrauch über 24 Stunden, 7 Tage und 14 Tage in `mg/l/d`
- persönlicher Chlorfaktor gegen einen konservativen Basisverlust von `0,8 mg/l/d`
- persönlicher Chlor-Dosierfaktor aus bestätigten Zugabe-/Nachmess-Paaren
- effektiver Wirkstoffanteil auf Basis der real beobachteten Dosierwirkung
- Chlor-Prognose für den erwarteten Abfall unter die Zieluntergrenze bzw. unter `0,6 mg/l`
- Chlor-Stabilität mit Durchschnitt, Minimum, Maximum, Stichprobenzahl, roher Vorhersagequalität und kontextbereinigter Stabilitätsqualität

Bis mindestens drei verwertbare Intervalle vorhanden sind, bleibt die Auswertung in der Lernphase.

Für die Stabilität bleibt der angezeigte 24h/7d/14d-Verbrauch roh beobachtet. Die Stabilitätsbewertung selbst nutzt zusätzlich eine heuristisch kontextbereinigte Reihe, damit Intervalle mit viel offener Abdeckung oder intensiver Nutzung die Stabilitätsampel nicht mehr unnötig verschlechtern.

### pH-Stabilitätsanalyse

Die Integration speichert neue pH-Messpunkte sowie bestätigte pH-Plus- und pH-Minus-Zugaben. Daraus entstehen bereinigte Drift-Intervalle, bei denen die erwartete Korrekturwirkung der Zugaben herausgerechnet wird.

Berechnet werden:

- pH-Drift über 24 Stunden, 7 Tage und 14 Tage in `pH/d`
- pH-Trend als `rising`, `falling`, `stable` oder `learning`
- pH-Stabilität mit Durchschnitt, Minimum, Maximum, Stichprobenzahl und Vorhersagequalität

Bis mindestens drei verwertbare Intervalle vorhanden sind, bleibt die Auswertung in der Lernphase.

## Frontend: Pool Chemistry Card

Die Integration registriert automatisch eine Custom Card:

```yaml
type: custom:pool-chemistry-card
recommendation_entity: sensor.pool_empfehlung
grid_options:
  columns: full
  rows: auto
layzspa:
  enabled: true
  connection: binary_sensor.layzspa_connection
  ip: sensor.layzspa_ip
  rssi: sensor.layzspa_rssi
  pump: switch.layzspa_pump
  heater: switch.layzspa_heat_regulation
  airbubbles: switch.layzspa_airbubbles
  temp_current: sensor.layzspa_temp_c
  temp_target: sensor.layzspa_target_temp_c
  temp_target_control: number.layzspa_target_temp_c
  heat_eta:
    enabled: true
    history_hours: 48
    fallback_rate_c_per_hour: 3
```

`temp_target_control` ist optional und kann auf eine `number.*`- oder `climate.*`-Entität zeigen. Wenn gesetzt, blendet die Karte unterhalb der Temperaturanzeige eine direkte Zieltemperatur-Steuerung ein.

`heat_eta` ist optional. Die Karte lädt dafür im Frontend die Home-Assistant-Historie von Ist-Temperatur und Heizung, berechnet daraus die reale Heizrate während Heizphasen und zeigt die geschätzte Restdauer bis zur Zieltemperatur. Wenn noch nicht genug Verlauf vorhanden ist, wird `fallback_rate_c_per_hour` verwendet und als Fallback gekennzeichnet.

Die Karte zeigt oben neben der Empfehlung eine Badeampel. Rot bedeutet, dass Baden aktuell nicht empfohlen wird, z. B. wegen fehlender aktueller Kernmessung, Nachmess-Zustand, gemessenem Chlor im Stoßchlorbereich, deutlicher Chlor-/pH-Abweichung oder sehr hoher Wassertemperatur ab 41 °C. Gelb bedeutet, dass Baden möglich ist, aber Werte oder Wetter nicht ideal sind, z. B. bei warmem Wasser über 36 °C. Grün bedeutet, dass keine Warn- oder Sperrgründe vorliegen.

Die Karte zeigt zusätzlich eine einklappbare Sektion **Stabilität**. Die Kopfzeile fasst Chlor- und pH-Status inklusive Lernfortschritt oder Vorhersagequalität zusammen; aufgeklappt erscheinen 24h-/7d-/14d-Werte, Min/Max, persönlicher Chlorfaktor, persönlicher Dosierfaktor, effektiver Wirkstoffanteil, Chlor-Prognose, Konfidenz und pH-Trend.

Direkt im Chlor-Empfehlungsblock blendet die Karte außerdem die aktuelle Chlor-Prognose mit Konfidenz ein, sobald genügend Lernhistorie vorhanden ist.

Im visuellen Karten-Editor bleiben nur die LayZSpa-Optionen editierbar. Wetter-Entität und UV-Sensor werden in der Integration konfiguriert; Empfehlungssensor und PoolLab-Abruf-Button werden von der Karte fest bzw. automatisch verwendet.

## Entitäten

Die Integration stellt unter anderem bereit:

- `sensor.pool_chlor_nachdosierung`
- `sensor.pool_chlor_vor_baden`
- `sensor.pool_ph_minus`
- `sensor.pool_ph_plus`
- `sensor.pool_chlor_istwert`
- `sensor.pool_ph_istwert`
- `sensor.pool_temperatur_istwert`
- `sensor.pool_datenquelle`
- `sensor.pool_chlorverbrauch_24h`
- `sensor.pool_chlorverbrauch_7d`
- `sensor.pool_chlorverbrauch_14d`
- `sensor.pool_persoenlicher_chlorfaktor`
- `sensor.pool_persoenlicher_chlor_dosierfaktor`
- `sensor.pool_chlor_vorhersagequalitaet`
- `sensor.pool_chlor_dosierqualitaet`
- `sensor.pool_chlor_prognose_tagesverlust`
- `sensor.pool_chlor_bis_minimum`
- `sensor.pool_chlor_bis_0_6`
- `sensor.pool_chlor_prognose`
- `sensor.pool_chlor_stabilitaet`
- `sensor.pool_ph_drift_24h`
- `sensor.pool_ph_drift_7d`
- `sensor.pool_ph_drift_14d`
- `sensor.pool_ph_vorhersagequalitaet`
- `sensor.pool_ph_trend`
- `sensor.pool_ph_stabilitaet`
- `sensor.pool_empfehlung`
- `sensor.poollab_batterie`
- `sensor.pool_filter_reinigung_fallig`
- `sensor.pool_filter_wechsel_fallig`
- `button.poollab_messwerte_abrufen`

## Dokumentation

- Technische Doku: [TECHNISCHE_DOKUMENTATION.md](TECHNISCHE_DOKUMENTATION.md)
- Changelog: [Changelog.md](Changelog.md)
