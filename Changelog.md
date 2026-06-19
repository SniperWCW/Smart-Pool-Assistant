# Changelog - Smart Pool Assistant

## [1.1.0] - 2026-06-19

- **Refactoring-Start fuer 1.1.x**: Wartungs-/History-Logik wurde aus `coordinator.py` in `maintenance.py` ausgelagert.
- **Berechnungslogik ausgelagert**: Chlor-, pH-, Nachmess- und Empfehlungslogik liegt nun in `calculation.py`, damit sie kuenftig gezielter getestet und angepasst werden kann.
- **Coordinator entlastet**: `coordinator.py` bleibt fuer Home-Assistant-Orchestrierung, Datenbeschaffung, Persistenz und Zusammenfuehrung verantwortlich.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.1.0.md` auf den aktuellen Stand gebracht.

## [1.0.23] - 2026-06-19

- **Forecast-Logspam behoben**: Die Lovelace-Karte ruft Wetter-Forecasts im Frontend nicht mehr ueber den problematischen `weather.get_forecasts`-Servicepfad ab, der im Dashboard-Kontext WebSocket-Fehler mit `return_response=True` ausloesen konnte.
- **Stabileres Forecast-Nachladen**: Fuer Tagesvorhersagen wird nur noch der Forecast-Endpunkt verwendet. Wenn kein Ergebnis zurueckkommt, verhindert ein Retry-Cooldown sofortige Endlosschleifen und Log-Spam.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.0.23.md` auf den aktuellen Stand gebracht.

## [1.0.22] - 2026-06-19

- **Tomorrow.io-Forecast-Fallback in der Karte**: Die Lovelace-Karte liest Tagesvorhersagen jetzt nicht mehr nur aus `attributes.forecast`, sondern laedt bei Bedarf aktiv `daily`-Forecasts ueber Home Assistants Weather-Forecast-API nach.
- **Kompatiblere Wetteranzeige**: Wetterkarten mit Providern wie `weather.tomorrow_io_home_daily` zeigen damit wieder heute und morgen an, auch wenn die Forecast-Daten nicht direkt als Attribut an der Entity haengen.
- **Wind-Einheit korrigiert**: Die Windanzeige verwendet jetzt die von der Wetter-Entity gelieferte Einheit (`wind_speed_unit`) statt kleine Werte pauschal als `m/s` zu behandeln.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.0.22.md` auf den aktuellen Stand gebracht.

## [1.0.21] - 2026-06-18

- **Wetter in der Lovelace-Karte**: Zwischen Empfehlung und weiteren Bereichen kann jetzt eine Vorhersage fuer heute und morgen aus einer konfigurierbaren `weather`-Entitaet angezeigt werden, inklusive Sonne/UV, Regen und Wind.
- **Optionale Wetterquelle in der Integration**: Config Flow und Options Flow unterstuetzen jetzt eine `weather`-Entitaet direkt in der Integration, statt die Wetterlogik nur an die Kartenkonfiguration zu binden.
- **Konservative Wetterlogik fuer Chlor**: Hoher `uv_index` erhoeht den Chlor-Zielbedarf leicht ueber einen separaten `UV-Zuschlag` im Breakdown.
- **Regen als Nachmess-Hinweis**: Erwarteter starker Regen fuehrt zunaechst nicht zu harter Ueberdosierung, sondern zu einem expliziten Hinweis, danach moeglichst erneut zu messen.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.0.21.md` auf den aktuellen Stand gebracht.

## [1.0.20] - 2026-06-18

- **Nutzungsmodus korrigiert**: `none`, `normal` und `party` beeinflussen die finale Chlorempfehlung jetzt auch bei aktivem Stoßchlor-Ziel. Zuvor war die Endmenge in solchen Fällen fälschlich identisch, obwohl sich nur die Breakdown-Zeilen änderten.
- **Whirlpool-Fälle geprüft**: Für den gezeigten 0,916 m³-Fall ergibt die korrigierte Logik jetzt ca. `8,1 g` bei keiner Nutzung, `8,9 g` bei normaler Nutzung und `9,7 g` bei Party.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.0.20.md` auf den aktuellen Stand gebracht.

## [1.0.19] - 2026-06-18

- **Chlorlogik neu aufgebaut**: Die Chlorberechnung arbeitet jetzt ueber volumenbezogene Zielkonzentrationen in `mg/l` und rechnet erst am Ende ueber das konfigurierte `pool_volume` in Gramm Produkt um.
- **Plausiblere Whirlpool-Dosierung**: Feste Grammzuschlaege fuer kleine Becken entfallen. Temperatur, offenes Becken, Nutzung und Stoßchlorung werden jetzt fachlich konsistenter beruecksichtigt.
- **Frontend-Breakdown angepasst**: Die Karte zeigt jetzt `Stoßchlor-Ziel`, `Temperatur-Zuschlag`, `Offenes Becken` und `Nutzung` statt der alten Faktor-Begriffe.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `RELEASE_NOTES_V1.0.19.md` auf den aktuellen Stand gebracht.

## [1.0.16] - 2026-06-18

### Neu
- **Nachmess-Workflow in der Karte**: Nach bestaetigter Chlor-, pH-Minus- oder pH-Plus-Zugabe zeigt die Integration jetzt **Warten auf erneute Messung**, bis neue Werte eingelesen wurden.
- **LayZSpa Zieltemperatur-Steuerung**: Die Karte kann die Zieltemperatur jetzt optional direkt per `+` / `-` ueber `number.*`- oder `climate.*`-Entitaeten anpassen.
- **Markdown Release Notes**: Neue Datei `RELEASE_NOTES_V1.0.16.md` fuer den GitHub-Release.

### Verbesserungen
- **Live-BLE-Status**: Die Zeile **BT Verbindung** ist nur waehrend eines aktiven PoolLab-BLE-Abrufs gruen und springt nach dem Disconnect wieder auf rot.
- **Dokumentation aktualisiert**: README und technische Doku spiegeln jetzt den aktuellen Ablauf fuer BLE, Cloud, Nachmessung und LayZSpa-Temperatursteuerung wider.

### Fixes
- **Keine sticky BLE-Anzeige mehr**: `bluetooth_connected` wird nicht mehr persistent als letzter Erfolgszustand gehalten.
- **Fachlich sauberere Dosieranzeige**: Bereits protokollierte Chemiezugaben fuehren nicht mehr dazu, dass alte Empfehlungen weiter aktiv dargestellt werden.

## [1.0.15] - 2026-06-17

### Neu
- **PoolLab-Abruf direkt in der Karte**: Die Lovelace-Karte enthält jetzt in den aktuellen Messwerten einen integrierten Abrufbutton mit Status-, Fehler- und Cooldown-Anzeige.
- **Technische Dokumentation**: Neue Datei `TECHNISCHE_DOKUMENTATION.md` dokumentiert Architektur, Datenfluss, Button-Plattform und aktuelle BLE-/Cloud-Logik.

### Verbesserungen
- **Cloud-Polling wieder konfigurierbar**: Das Cloud-Update-Intervall ist wieder über Config Flow und Options Flow einstellbar, Standard `5` Minuten.
- **Getrennte Abrufstrategie geschärft**: Der manuelle Abruf priorisiert BLE, während Cloud-Daten weiterhin zyklisch im Hintergrund aktualisiert werden.
- **Dokumentation bereinigt**: README und technische Doku spiegeln jetzt den tatsächlichen Stand mit Button-Plattform, Kartenintegration und Cloud-Intervall wider.

### Fixes
- **BT-Status bis ins Frontend durchgereicht**: `bluetooth_connected` wird jetzt sauber an den Empfehlungssensor und die Karte weitergegeben.
- **Stabilere BLE-Statusanzeige**: Die Zeile **BT Verbindung** bleibt am letzten erfolgreichen manuellen BLE-Verbindungsaufbau orientiert, statt bei jedem Cloud-Refresh wieder auf rot zu springen.

## [1.0.14] - 2026-06-17

### Neu
- **Manueller PoolLab-Abruf**: Neue Button-Entität `button.poollab_messwerte_abrufen` für gezielte Einzelabrufe nach einer Messung.

### Verbesserungen
- **Kein automatisches PoolLab-Polling mehr**: BLE- und Cloud-Abrufe werden nur noch explizit ausgelöst, nicht mehr zyklisch.
- **Proxy-schonendere BLE-Kommunikation**: Weniger aggressive Retries, längere Settling-Delays sowie Cooldowns nach Erfolg und Fehlern.
- **Konfigurationsbereinigung**: Das frühere Update-Intervall wurde aus dem Config Flow entfernt, da es keinen PoolLab-Abruf mehr steuert.
- **Dokumentation aktualisiert**: README, Versionsstand und Bedienablauf für den neuen manuellen Abruf wurden angepasst.

### Fixes
- **Wartungs-Refresh**: Lokale Housekeeping-Updates bleiben aktiv, damit Filter- und Erinnerungslogik weiterhin ohne automatischen PoolLab-Connect funktioniert.

## [1.0.9] - 2026-06-15

### Neu
- **Release 1.0.9**: Versionierung und Dokumentation wurden auf den neuen Release-Stand angehoben.

### Verbesserungen
- **README-Aktualisierung**: Der aktuelle Release-Stand wird nun als `V1.0.9` angezeigt.

## [1.0.8] - 2026-06-15

### Neu
- **Direkte Bluetooth-Anbindung**: Unterstützung für PoolLab 1.0 Geräte via BLE, inklusive stabiler Nutzung über einen **ESP Bluetooth Proxy**.
- **Getrennte Quellenlogik**: Bluetooth, Cloud/API und manuelle Werte werden pro Messwert getrennt behandelt, damit neuere BLE-Messungen nicht mehr von älteren Cloud-Werten überschrieben werden.
- **Batterie-Status**: Der Batteriestand des PoolLab-Geräts wird nun über Bluetooth ausgelesen und als Sensor zur Verfügung gestellt.
- **Erweiterte Frontend-Karte**:
  - Anzeige der **Datenquelle** (Bluetooth, Cloud, Manuell oder Speicher) in klarer Form.
  - Dynamische Anzeige des letzten Updates ("vor x Minuten") mittels `<ha-relative-time>`.
  - Aktuelle Messwerte als 3-Spalten-Tabelle.
  - Letzte Aktivitäten und Cloud-API-Messwerte als einheitliche, einklappbare Tabellen.
- **Letzte Aktivitäten**: Die letzten 5 Tätigkeiten werden in der Karte angezeigt, inklusive Einheiten und lesbarer Bezeichnungen.

### Verbesserungen
- **Robuster Verbindungsaufbau**: Explizites Handling von Timeouts und Verbindungsabbrüchen (`asyncio.CancelledError`), besonders wichtig bei der Nutzung von Bluetooth-Proxies (ESPHome).
- **Bessere Datenaktualität**: Die UI bleibt auf den frischeren Bluetooth-Wert fokussiert, statt beim Aktualisieren wieder auf ältere Cloud-Daten zurückzuspringen.
- **Lesbarere Darstellung**: Aktivitäten und Cloud-Messwerte werden in einer konsistenten Tabellenoptik dargestellt.

### Fixes
- **Bluetooth Discovery**: Überarbeitung der Bluetooth-Matcher in `manifest.json` für eine zuverlässigere Erkennung (Problem mit fehlenden Service-UUIDs behoben).
- **Config Flow**: Validierung korrigiert, sodass BLE nun als alleinige Datenquelle zulässig ist.
- **Discovery Logik**: Fehler behoben, bei dem die Liste der verfügbaren Geräte im Konfigurations-Dialog leer blieb.
- **Aktivitäten-Labels**: Fehler behoben, bei dem Einträge wie `0 Filter gereinigt` angezeigt wurden statt `Filter gereinigt`.
- **Einheiten**: Dosier-Aktionen werden nun mit Einheiten dargestellt, z. B. `10 g Chlor hinzugefügt` statt nur `10 Chlor hinzugefügt`.

## [0.4.0] - 2024-05-24

### ✨ Neu
- **LayZSpa Integration**: Neues Bedienfeld für Whirlpools inklusive Steuerung von Pumpe, Heizung und Bubbles.
- **Konnektivitäts-Monitor**: Anzeige von WLAN-Signalstärke (RSSI) und Verbindungsstatus direkt in der Karte.
- **Responsive Info-Rows**: "Letzte Aktivitäten" und "Cloud API Messwerte" werden nun platzsparend nebeneinander dargestellt, sofern die Breite es zulässt.

### 🔧 Verbesserungen
- **Icon-System**: Umstellung aller Icons auf native Home Assistant `mdi:` Icons für ein konsistentes Design und bessere Performance.
- **Einklapp-Logik**: Die LayZSpa-Sektion lässt sich nun einklappen, wobei der Status (ausgeklappt/eingeklappt) während der Sitzung erhalten bleibt.
- **Layout-Feinschliff**: Vereinheitlichung der Abstände (16px) zwischen allen Sektionen für ein ruhigeres Gesamtbild.

## [0.3.1] - 2024-05-22

### 🔧 Verbesserungen
- **Robuste Zeitstempel-Logik**: Vollständige Überarbeitung der Zeitstempel-Verarbeitung. Es wird nun präzise zwischen `last_api_measurement` und `last_manual_measurement` unterschieden. Der Vergleich erfolgt auf Basis von echten `datetime`-Objekten, was Fehler bei Neustarts oder Zeitformat-Wechseln verhindert.
- **Erweiterte Warn-Zustände**: Die Status-Box im Frontend unterstützt nun eine "Kritisch"-Farbe (Rot), wenn Werte wie Chlor oder pH deutlich zu hoch sind.

### 🐛 Fixes
- Korrektur der Anzeige in der Fußzeile ("Letzte Messung"): Manuelle Messungen überschreiben Cloud-Daten nur noch dann, wenn sie zeitlich wirklich neuer sind.

## [0.3.0] - Aktuelle Änderungen

### ✨ Neu
- **Zentralisierte Empfehlungs-Logik**: Die Logik für Status-Texte (z.B. "pH zuerst anpassen") wurde vom Frontend in den Coordinator verschoben. Dadurch zeigt die Entität `sensor.pool_empfehlung` nun exakt denselben Status wie die UI-Karte an.
- **Hoch-Chlor-Warnung**: Wenn der Chlorwert den Zielwert um mehr als 0.2 mg/l überschreitet, wechselt der Status auf "⚠️ Chlorwert ist zu hoch!" und wird im Frontend rot markiert.

### 🔧 Verbesserungen
- **Intelligente Dosier-Sperre**: Die Mindestdosis-Logik wurde angepasst. Wenn der aktuelle Chlorwert bereits über dem Zielwert liegt, wird konsequent **0g** empfohlen, anstatt fälschlicherweise die Mindestdosis anzuzeigen.
- **Null-Werte Sicherheit**: Verbesserte Fehlerbehandlung im Coordinator, falls Sensoren temporär `None` oder `unavailable` liefern, um Abstürze in der Berechnung zu verhindern.

### 🐛 Fixes
- Fehler behoben, bei dem die Empfehlung "Chlorwert optimal" angezeigt wurde, obwohl der Wert deutlich zu hoch war.
- Abgleich der Zeitstempel zwischen manuellen Messungen und Cloud-Daten optimiert.
