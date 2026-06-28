# Einrichtung und Konfiguration

Navigation:

- [Startseite](../README.md)
- [Chemielogik](CHEMISTRY.md)
- [Karte und Demos](CARD_AND_DEMOS.md)
- [Entitaeten](ENTITIES.md)
- [FAQ](../FAQ.md)
- [Technische Dokumentation](../TECHNISCHE_DOKUMENTATION.md)

Diese Seite beschreibt die praktische Einrichtung in Home Assistant. Fuer fachliche Details zur Berechnung siehe [CHEMISTRY.md](CHEMISTRY.md).

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

## Ersteinrichtung

Die Einrichtung erfolgt ueber **Einstellungen > Geraete & Dienste > Integration hinzufuegen**.

Wichtige Konfigurationspunkte:

- **BLE-Adresse**: PoolLab 1.0 fuer manuellen BLE-Abruf.
- **PoolLab API-Key**: Aktiviert die zyklische Cloud-Aktualisierung und dient ohne BLE optional auch als manuelle Abrufquelle.
- **Cloud-Update-Intervall**: Zyklischer Cloud-Abruf in Minuten, Standard `5`, Bereich `1-60`.
- **Manuelle Sensoren**: Chlor, pH und optional Temperatur.
- **Pumpe**: Optionaler `switch.*` oder `binary_sensor.*` fuer Pumpenlaufzeit in der Chlor-Prognose.
- **Pool-Verbindung**: Optionaler Binary Sensor, der nach konfigurierbarer Offline-Wartezeit eine Benachrichtigung ausloest.
- **Poolvolumen**: Wassermenge in `m3`.
- **Zielbereiche**: Chlor Minimum/Maximum und pH Minimum/Maximum.
- **Schockchlorung Maximum**: Obergrenze fuer die automatische Schockchlorung in `mg/l`. Fuer deinen Whirlpool kannst du hier z.B. `3.0` setzen.
- **Chlorprodukt-Typ**: `Organisch / stabilisiert` oder `Anorganisch / unstabilisiert`.
- **Wirkstoffanteil**: Aktiver Chloranteil laut Produktangabe. Typische Startwerte sind etwa `0.56` fuer organisches Chlor, `0.65-0.70` fuer Calciumhypochlorit und `0.12-0.15` fuer Natriumhypochlorit.
- **pH-Dosierungen**: pH-Minus in `ml` und pH-Plus in `g`.
- **Benachrichtigungsdienst(e)** und **Follow-up-Zeit**.
- **Filter-Intervalle** und Warnschwellen.

## PoolLab-Abruf

- Die Integration verbindet sich nicht zyklisch per BLE mit dem PoolLab.
- Fuer einen BLE-Abruf: PoolLab einschalten, Messung oder Zero durchfuehren, kurz warten und dann `button.poollab_messwerte_abrufen` druecken.
- Der gleiche Abruf ist direkt in der Lovelace-Karte oben in einer eigenen **PoolLab**-Box integriert.
- Nach Erfolg gilt ein Cooldown von `20` Sekunden, nach Fehlern `30` Sekunden.
- Cloud-Daten laufen weiterhin zyklisch ueber das konfigurierte Intervall weiter.
- **BT Verbindung** zeigt nur den aktuell laufenden BLE-Connect an. Nach dem Lesen trennt die Integration bewusst wieder.
- Diagnose-Logs werden in `smart_pool_assistant_logs/smart_pool_assistant.log` im Home-Assistant-Konfigurationsverzeichnis geschrieben und automatisch rotiert.

## Nachmess-Workflow nach Chemiezugabe

- Wenn du Chlor, pH-Minus oder pH-Plus in der Karte bestaetigst, gilt die bisherige Messung fachlich als verbraucht.
- Solange noch keine neue Messung eingelesen wurde, zeigt die Integration **Warten auf erneute Messung** statt denselben Dosiervorschlag erneut an.
- Die betroffenen Eingabefelder bleiben bis zur naechsten Messung gesperrt.
- Die Follow-up-Erinnerung bleibt aktiv und passt weiterhin zum Nachmess-Ablauf.

## Weiterfuehrende Seiten

- [Chemielogik und Lernsystem](CHEMISTRY.md)
- [Lovelace-Karte und Demos](CARD_AND_DEMOS.md)
- [Entitaeten](ENTITIES.md)
- [FAQ](../FAQ.md)
