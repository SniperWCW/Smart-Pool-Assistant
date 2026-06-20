# Smart Pool Assistant

Der **Smart Pool Assistant** ist eine Home Assistant Integration fuer Pool- und Whirlpool-Pflege. Die Integration kombiniert PoolLab BLE, PoolLab Cloud, manuelle Sensoren, Dosierlogik, Wartungshistorie und eine eigene Lovelace-Karte in einer zentralen Empfehlung.

**Aktueller Release-Stand: V2.0.4**

## Hauptfunktionen

- Praezise Chlor-Berechnung ueber volumenbezogene Zielbereiche mit Stoßchlor-Ziel, Temperatur-, Abdeckungs- und Nutzungszuschlag.
- Transparente Dosierlogik mit Breakdown direkt in der Lovelace-Karte.
- Konservative Dosierempfehlungen passend zu Messloeffeln mit `1`, `2,5`, `5`, `7,5` und `15 g/ml`.
- Optionale Wetterintegration ueber eine Home-Assistant-`weather`-Entitaet mit Vorhersage fuer heute und morgen, inklusive Backend-Forecast-Fallback fuer Provider wie Tomorrow.io.
- Optionaler separater `UV`-Sensor fuer Provider, die den UV-Index nicht im Daily-Forecast liefern.
- Die Wetterkarte nutzt bevorzugt vom Backend vorbereitete Forecast-Tagesdaten und faellt erst danach auf heutige Coordinator-Wetterwerte zurueck.
- Die Wettersektion ist jetzt einklappbar und zeigt in der Kopfzeile eine kompakte Heute-Zusammenfassung.
- Optimierte Lovelace-Karte: rendert nur noch bei relevanten Entity-Aenderungen neu.
- Badeampel in der Lovelace-Karte: `Baden empfohlen`, `Baden möglich` oder `Nicht empfohlen` anhand von Chemie-, Nachmess-, Temperatur- und Wetterdaten.
- Uebersichtlichere Messwertetabelle mit getrennten Spalten fuer `Messwert`, `Ist`, `Ziel` und `Quelle`.
- Verbesserte mobile Darstellung fuer Wetter-Kopfzeile und aktuelle Messwerte.
- Konservativer Wetter-Einfluss auf Chlor: hoher UV-Index kann den Zielbedarf leicht erhoehen, Regen erzeugt einen Nachmess-Hinweis.
- Direkte Bluetooth-Anbindung fuer **PoolLab 1.0** inklusive Batteriestatus und Nutzung ueber ESP Bluetooth Proxy.
- Manueller PoolLab-Abruf ueber `button.poollab_messwerte_abrufen` statt zyklischem BLE-Polling.
- Weiterhin zyklischer Cloud-Abruf ueber das konfigurierbare Cloud-Update-Intervall.
- Abrufbutton direkt in der Messwertetabelle der Karte, inklusive Status-, Fehler- und Cooldown-Anzeige.
- Live-BLE-Status: **BT Verbindung** ist nur waehrend eines aktiven BLE-Abrufs gruen und springt nach dem Disconnect wieder auf rot.
- Fachlich sauberer Nachmess-Workflow: Nach jeder bestaetigten Chlor- oder pH-Zugabe zeigt die Integration **Warten auf erneute Messung**, bis neue Werte vorliegen.
- Getrennte Quellenlogik fuer Bluetooth, Cloud, manuelle Sensoren und Speicher-Fallback.
- Persistente Historie fuer letzte Werte, letzte Aktionen, letzte Cloud-Messwerte und Filterwartung.
- LayZSpa-Panel mit Anzeige von Verbindung, RSSI, Pumpe, Heizung, Luftblasen, Ist-/Zieltemperatur und optionaler Zieltemperatur-Steuerung per `+` / `-`.
- Benachrichtigungen fuer Chemie-Follow-up und Filterwartung, optional an zwei Notify-Ziele.
- Re-Konfiguration ueber Config Flow / Options Flow.

## Installation

### Ueber HACS

1. Oeffne **HACS** in Home Assistant.
2. Gehe auf **Benutzerdefinierte Repositories**.
3. Fuege dieses Repository als Typ `Integration` hinzu.
4. Installiere **Smart Pool Assistant**.
5. Starte Home Assistant neu.

### Manuell

1. Kopiere `custom_components/smart_pool_assistant` in deinen `custom_components` Ordner.
2. Starte Home Assistant neu.

## Konfiguration

Die Einrichtung erfolgt ueber **Einstellungen > Geraete & Dienste > Integration hinzufuegen**.

Wichtige Konfigurationspunkte:

- **BLE-Adresse**: PoolLab 1.0 fuer manuellen BLE-Abruf.
- **PoolLab API-Key**: Aktiviert die zyklische Cloud-Aktualisierung und dient ohne BLE optional auch als manuelle Abrufquelle.
- **Cloud-Update-Intervall**: Zyklischer Cloud-Abruf in Minuten, Standard `5`, Bereich `1-60`.
- **Manuelle Sensoren**: Chlor, pH und optional Temperatur.
- **Poolvolumen**: Wassermenge in m3.
- **Zielbereiche**: Chlor Minimum/Maximum und pH Minimum/Maximum.
- **Wirkstoffanteil**: Wirkstoffanteil des Chlorprodukts.
- **pH-Dosierungen**: pH-Minus in ml und pH-Plus in g.
- **Benachrichtigungsdienst(e)** und **Follow-up-Zeit**.
- **Filter-Intervalle** und Warnschwellen.

## PoolLab-Abruf

- Die Integration verbindet sich nicht mehr zyklisch mit dem PoolLab.
- Fuer einen BLE-Abruf: PoolLab einschalten, Messung oder Zero durchfuehren, kurz warten und dann `button.poollab_messwerte_abrufen` druecken.
- Der gleiche Abruf ist direkt in der Lovelace-Karte unter **Aktuelle Messwerte** integriert.
- Nach Erfolg gilt ein Cooldown von 20 Sekunden, nach Fehlern 30 Sekunden.
- Cloud-Daten laufen weiterhin zyklisch ueber das konfigurierte Intervall weiter, ohne dass BLE automatisch verbunden wird.
- **BT Verbindung** zeigt nur den aktuell laufenden BLE-Connect an. Nach dem Lesen trennt die Integration bewusst wieder.

## Nachmess-Workflow nach Chemiezugabe

- Wenn du Chlor, pH-Minus oder pH-Plus in der Karte bestaetigst, gilt die bisherige Messung fachlich als verbraucht.
- Solange noch keine neue Messung eingelesen wurde, zeigt die Integration **Warten auf erneute Messung** statt denselben Dosiervorschlag erneut an.
- Die betroffenen Eingabefelder bleiben bis zur naechsten Messung gesperrt.
- Die Follow-up-Erinnerung bleibt aktiv und passt weiterhin zum Nachmess-Ablauf.

## Berechnungslogik

### Chlor

Die Chlorempfehlung beruecksichtigt:

1. Basisbedarf aus `untere Zielgrenze - Ist` in `mg/l`, wenn Chlor unter dem Zielbereich liegt.
2. Temperatur-Zuschlag ab 28 C bzw. 32 C.
3. Zuschlag fuer offene Abdeckung.
4. Nutzungsmodus (`none`, `normal`, `party`) als zusaetzlicher Konzentrationsbedarf, der auch bei aktivem Stoßchlor-Ziel zusaetzlich auf die Endmenge wirkt.
5. Stoßchlor-Ziele bei sehr niedrigen Chlorwerten.
6. Umrechnung der benoetigten Gesamtkonzentration ueber das konfigurierte `Poolvolumen (m³)` und den Wirkstoffanteil in Gramm Produkt.
7. Zielbereich-Check, damit innerhalb des Bereichs oder bei Ueberdosierung `0 g` empfohlen wird.

### pH

Die pH-Berechnung ermittelt anhand Zielbereich, Poolvolumen und Produktdosierung die benoetigte Menge an:

- **PH-Minus** in ml
- **PH-Plus** in g

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
```

`temp_target_control` ist optional und kann auf eine `number.*`- oder `climate.*`-Entitaet zeigen. Wenn gesetzt, blendet die Karte unterhalb der Temperaturanzeige eine direkte Zieltemperatur-Steuerung ein.

Die Karte zeigt oben neben der Empfehlung eine Badeampel. Rot bedeutet, dass Baden aktuell nicht empfohlen wird, z. B. wegen fehlender aktueller Kernmessung, Nachmess-Zustand, Stosschlor oder deutlicher Chlor-/pH-Abweichung. Gelb bedeutet, dass Baden moeglich ist, aber Werte oder Wetter nicht ideal sind. Gruen bedeutet, dass keine Warn- oder Sperrgruende vorliegen.

Im visuellen Karten-Editor bleiben nur die LayZSpa-Optionen editierbar. Wetter-Entitaet und UV-Sensor werden in der Integration konfiguriert; Empfehlungssensor und PoolLab-Abruf-Button werden von der Karte fest bzw. automatisch verwendet.

## Entitaeten

Die Integration stellt unter anderem bereit:

- `sensor.pool_chlor_nachdosierung`
- `sensor.pool_chlor_vor_baden`
- `sensor.pool_ph_minus`
- `sensor.pool_ph_plus`
- `sensor.pool_chlor_istwert`
- `sensor.pool_ph_istwert`
- `sensor.pool_temperatur_istwert`
- `sensor.pool_datenquelle`
- `sensor.pool_empfehlung`
- `sensor.poollab_batterie`
- `sensor.pool_filter_reinigung_fallig`
- `sensor.pool_filter_wechsel_fallig`
- `button.poollab_messwerte_abrufen`

## Dokumentation

- Technische Doku: [TECHNISCHE_DOKUMENTATION.md](TECHNISCHE_DOKUMENTATION.md)
- Changelog: [Changelog.md](Changelog.md)
