# Changelog - Smart Pool Assistant

## [2.1.9] - 2026-06-22

- **Bugfix PoolLab-BLE-Timeouts**: Der PoolLab-BLE-Client trennt nach Timeout oder Abbruch jetzt explizit Notifications und Verbindung.
- **Stabilerer ESP32-Bluetooth-Proxy-Betrieb**: Der BLE-Client nutzt den von `establish_connection(...)` gelieferten Client direkt und vermeidet eine doppelte Connect-/Disconnect-Verwaltung.
- **Separates Connect-Timeout**: Der Verbindungsaufbau bekommt ein eigenes Timeout, damit der Befehlsfluss nicht mitten im Home-Assistant-Bluetooth-Connect-State abgebrochen wird.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.1.9.md` auf den aktuellen Stand gebracht.

## [2.1.8] - 2026-06-22

- **Bugfix Home-Assistant-Event-Loop**: Die Manifest-Version fuer den Frontend-Cachebuster wird jetzt ueber `hass.async_add_executor_job(...)` gelesen.
- **Keine Blocking-Warnung beim Setup**: Der synchrone `open()`-Aufruf fuer `manifest.json` laeuft nicht mehr direkt im Event Loop.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.1.8.md` auf den aktuellen Stand gebracht.

## [2.1.7] - 2026-06-21

- **Pool-Verbindungswarnung**: Im Config Flow und Options Flow kann jetzt ein Binary Sensor fuer die Pool-/LayZSpa-Verbindung hinterlegt werden.
- **Offline-Benachrichtigung**: Wenn die Verbindung nach der konfigurierten Wartezeit weiterhin `off` oder `unavailable` ist, sendet die Integration eine Meldung an die hinterlegten Notify-Ziele und optional als HA-Benachrichtigung.
- **Keine Wiederholspam-Meldungen**: Pro Offline-Phase wird nur einmal benachrichtigt; bei `on` wird der Status zurueckgesetzt.
- **Follow-up-Erinnerungen stabilisiert**: Persistente Chemie-Follow-ups werden nach Neustarts robuster nachgeholt und nicht doppelt versendet.
- **LayZSpa-Heizzeit-Prognose veroeffentlicht**: Die Karte zeigt optional die ETA bis zur Wunschtemperatur auf Basis der Home-Assistant-Historie oder einer Fallback-Heizrate.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.1.7.md` auf den aktuellen Stand gebracht.

## [2.1.6] - 2026-06-21

- **LayZSpa Heizzeit-Prognose**: Das Panel zeigt jetzt optional `Auf Wunschtemperatur` mit ETA auf Basis der Home-Assistant-Historie der letzten 24/48h bzw. konfigurierbarer Stunden.
- **Fallback-Heizrate**: Wenn noch nicht genug Heizverlauf vorhanden ist, nutzt die Karte eine konfigurierbare Fallback-Rate statt fixer Template-Werte und kennzeichnet diese in der Detailzeile.
- **Bugfix Stoßchlor-Semantik**: `is_shock` steht jetzt für einen gemessenen Chlorwert im Stoßchlorbereich von `3,0 bis 5,0 mg/l`, nicht mehr für zu niedrigen Chlorwert.
- **Badeampel korrigiert**: Die Karte zeigt nicht mehr `Stoßchlor aktiv` nach einer Empfehlung oder Zugabe, sondern bei passendem Messwert `Chlor im Stoßchlorbereich`.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V2.1.6.md` auf den aktuellen Stand gebracht.

## [2.1.5] - 2026-06-21

- **Gemeinsame Statusbox**: Status und Badeampel werden oben in der Lovelace-Karte als eine gemeinsame Box mit zwei Spalten dargestellt.
- **Bessere Lesbarkeit**: Die Box nutzt einen gemeinsamen Rahmen mit Farbe nach kritischstem Zustand und trennt `Status` und `Baden` über klare Segment-Labels.
- **Mobile Darstellung**: Auf schmalen Displays werden die beiden Bereiche innerhalb derselben Box sauber untereinander gestapelt.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V2.1.5.md` auf den aktuellen Stand gebracht.

## [2.1.4] - 2026-06-21

- **Doppelte Warnbox zusammengeführt**: Wenn Status und Badeampel denselben kritischen Chlor-Grund anzeigen, wird in der Lovelace-Karte nur noch eine rote Box dargestellt.
- **Chlor-Warntext vereinheitlicht**: Die Badeampel nutzt bei zu hohem Chlor jetzt denselben Text `Chlor zu hoch` wie der allgemeine Status.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V2.1.4.md` auf den aktuellen Stand gebracht.

## [2.1.3] - 2026-06-21

- **Einheitliches Frontend-Layout**: `LayzSpa`, `Aktuelle Messwerte`, `Filter Wartung` und `Status & Nutzung` nutzen nun denselben einklappbaren Panel-Aufbau wie `Wetter` und `Stabilität`.
- **Messwerte neu positioniert**: `Aktuelle Messwerte` stehen jetzt direkt unterhalb der Stabilitätssektion.
- **Kompakte Panel-Zusammenfassungen**: Messwerte, Filterstatus und Nutzung zeigen ihren wichtigsten Zustand direkt in der Kopfzeile.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.1.3.md` auf den aktuellen Stand gebracht.

## [2.1.2] - 2026-06-21

- **Stabilität in der Lovelace-Karte**: Neuer einklappbarer Frontend-Block für Chlor- und pH-Stabilität mit Kopfzeile für Status/Qualität, Fortschritt in der Lernphase und Detailwerten nach dem Aufklappen.
- **Lesbare Lernphasen-Fallbacks**: Fehlende Lernwerte werden in der Karte als `Nicht genügend Daten` bzw. `Noch keine Bewertung` angezeigt statt als rohe `unknown`-Werte.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.1.2.md` auf den aktuellen Stand gebracht.

## [2.1.1] - 2026-06-21

- **pH-Stabilitätsanalyse**: Neue lokale Lernhistorie für pH-Messpunkte sowie pH-Plus- und pH-Minus-Korrekturen.
- **pH-Drift-Sensoren**: Neue Sensoren für `24h`, `7d` und `14d` in `pH/d`.
- **pH-Trend und Stabilität**: Neuer Trend (`rising`, `falling`, `stable`, `learning`) und Stabilitäts-Sensor mit Durchschnitt, Minimum, Maximum, Stichprobenzahl und Vorhersagequalität.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.1.1.md` auf den aktuellen Stand gebracht.

## [2.1.0] - 2026-06-20

- **Lernende Chloranalyse**: Neue lokale Lernhistorie für Chlor-Messpunkte und bestätigte Chlorzugaben.
- **Chlorverbrauch-Sensoren**: Neue Sensoren für `24h`, `7d` und `14d` in `mg/l/d`.
- **Persönlicher Chlorfaktor**: Neuer Faktor gegen einen konservativen Basisverlust von `0,8 mg/l/d`.
- **Chlor-Stabilität**: Neuer Stabilitäts-Sensor mit Durchschnitt, Minimum, Maximum, Stichprobenzahl, Lernphase und Vorhersagequalität.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.1.0.md` auf den aktuellen Stand gebracht.

## [2.0.4] - 2026-06-20

- **Zielbereiche für Chlor und pH**: Config Flow und Options Flow nutzen jetzt Min-/Max-Werte statt fixer Einzelzielwerte. Bestehende `chlor_target`- und `ph_target`-Konfigurationen bleiben als Fallback kompatibel.
- **Berechnungen auf Bereiche umgestellt**: Innerhalb des Zielbereichs wird keine Chemie empfohlen. Chlor wird bei Unterschreitung konservativ zur unteren Bereichsgrenze nachdosiert; pH wird bei Unterschreitung zur unteren und bei Überschreitung zur oberen Bereichsgrenze korrigiert.
- **Karte und Badeampel angepasst**: Zielspalte, Farblogik, Badeempfehlung und Status-Texte bewerten Chlor und pH jetzt gegen die konfigurierten Bereiche.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.0.4.md` auf den aktuellen Stand gebracht.


## [2.0.3] - 2026-06-20

- **Nachmessstatus bei einzelner Chemiezugabe korrigiert**: Sobald Chlor, pH-Minus oder pH-Plus nach der letzten Messung bestätigt wurde, springt der Gesamtstatus auf `Warten auf erneute Messung`, auch wenn weitere Empfehlungen rechnerisch noch offen wären.
- **Messlöffel-Dosierung**: Chlor, pH-Minus, pH-Plus und die Vor-Baden-Chlormenge werden konservativ auf praktische Kombinationen aus `1`, `2,5`, `5`, `7,5` und `15 g/ml` gerundet. Beispiel: `8 g` wird als `7,5 g` empfohlen.
- **Lovelace-Anzeige erweitert**: Die Karte zeigt Dosierungen mit deutscher Zahlenformatierung und passender Messlöffel-Kombination an.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.0.3.md` auf den aktuellen Stand gebracht.

## [2.0.2] - 2026-06-19

- **Mobile Messwerttabelle korrigiert**: Auf schmalen Displays werden Ist-, Ziel- und Quellenwerte jetzt mit kompakten Labels dargestellt, statt unklar untereinander zu laufen.
- **Wetter-Kopfzeile mobil verbessert**: Die kompakte Wetterzusammenfassung bricht auf dem Handy sauber um und wird nicht mehr ungünstig abgeschnitten.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.0.2.md` auf den aktuellen Stand gebracht.

## [2.0.1] - 2026-06-19

- **Badeampel in der Lovelace-Karte**: Neben der Empfehlung zeigt die Karte jetzt `Baden empfohlen`, `Baden möglich` oder `Nicht empfohlen` anhand von Chemie-, Nachmess-, Temperatur- und Wetterdaten.
- **Aktuelle Messwerte übersichtlicher**: Die Messwertetabelle nutzt jetzt getrennte Spalten für `Messwert`, `Ist`, `Ziel` und `Quelle`; passende Messzeitpunkte werden in der Quellen-Spalte angezeigt.
- **Karten-Editor bereinigt**: Wetter-Entität, Empfehlungs-Hauptsensor und PoolLab-Abruf-Button sind im visuellen Karten-Editor nicht mehr editierbar. Die Integration bzw. die automatische Erkennung bleiben die führende Quelle.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.0.1.md` auf den aktuellen Stand gebracht.

## [2.0.0] - 2026-06-19

- **Stabiler Abschluss der großen Umbauten**: Der Stand bündelt die Refactorings der Berechnungs-, Wartungs-, Benachrichtigungs-, PoolLab-Cloud-, PoolLab-BLE- und Wetterlogik als neue Major-Version.
- **Optimierte Lovelace-Karte**: Die Karte rendert nicht mehr bei jedem beliebigen Home-Assistant-State-Update neu, sondern nur noch bei relevanten Änderungen an Empfehlung, Wetter, PoolLab oder LayzSpa-Entitäten.
- **PoolLab-Button-Erkennung beschleunigt**: Die automatisch erkannte PoolLab-Abruf-Button-Entität wird gecacht und muss nicht wiederholt über alle States gesucht werden.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json`, Frontend-Banner und neue `release_notes/RELEASE_NOTES_V2.0.0.md` auf den aktuellen Stand gebracht.

## [1.1.5] - 2026-06-19

- **Wetter einklappbar**: Die Wettersektion der Lovelace-Karte ist jetzt als ein- und ausklappbares Panel umgesetzt, ähnlich zum LayzSpa-Bereich.
- **Kompakte Wetter-Kopfzeile**: In der Kopfzeile werden die heutigen Wetterdaten jetzt in einer Reihe mit Komma-Trennung angezeigt, z. B. Zustand, Temperatur, UV, Regen und Wind.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.5.md` auf den aktuellen Stand gebracht.

## [1.1.4] - 2026-06-19

- **Optionaler UV-Sensor**: Im Config Flow und Options Flow kann jetzt zusätzlich ein separater `sensor` für den UV-Index hinterlegt werden, z. B. `sensor.tomorrow_io_home_uv_index`.
- **UV priorisiert aus eigener Entity**: `weather.py` verwendet für `weather_uv_today` bevorzugt den konfigurierten UV-Sensor und fällt erst danach auf Forecast-Daten zurück.
- **Wetterattribute erweitert**: `weather_uv_sensor` wird zusätzlich bis in die Sensorattribute durchgereicht.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.4.md` auf den aktuellen Stand gebracht.

## [1.1.3] - 2026-06-19

- **Tomorrow.io-Forecast ins Backend verlagert**: Die Integration holt Daily-Forecasts nun in `weather.py` über Home Assistants Wetter-Service und normalisiert sie zentral für Coordinator und Karte.
- **Karte zeigt wieder heute und morgen**: Die Lovelace-Karte nutzt bevorzugt `weather_forecast_days` aus dem Empfehlungssensor statt sich allein auf direkte Forecast-Attribute der Weather-Entity zu verlassen.
- **Stabilere Wetterattribute**: `weather_wind_speed_unit` und die normalisierten Forecast-Tagesdaten werden nun bis in die Sensorattribute durchgereicht.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.3.md` auf den aktuellen Stand gebracht.

## [1.1.2] - 2026-06-19

- **Wetterlogik ausgelagert**: Die Backend-Normalisierung der Wetter-Entity liegt nun in `weather.py`.
- **BLE-Messwertauswahl ausgelagert**: PoolLab-BLE-Type-ID-Auswertung für Chlor, pH, Temperatur und Cyanursäure liegt nun in `poollab_ble_source.py`.
- **Wetterkarte robuster**: Die Lovelace-Karte verarbeitet mehr Forecast-Antwortformate und nutzt als Fallback die Coordinator-Wetterattribute, wenn kein Daily-Forecast geliefert wird.
- **Wetterattribute erweitert**: `weather_condition_today`, `weather_temperature_today` und `weather_wind_speed_today` werden nun an die Empfehlungssensor-Attribute durchgereicht.
- **Frontend-Cachebuster korrigiert**: Die Lovelace-Ressource nutzt nun die Manifest-Version statt der Config-Entry-Version.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.2.md` auf den aktuellen Stand gebracht.

## [1.1.1] - 2026-06-19

- **Cloud-Logik ausgelagert**: PoolLab-Cloud-GraphQL-Abruf und Messwert-Normalisierung liegen nun in `poollab_cloud.py`.
- **Benachrichtigungen ausgelagert**: Persistent Notifications, Notify-Service-Versand, Follow-up-Hinweise und Filterwarnungen liegen nun in `notifications.py`.
- **Zweites Notify-Ziel**: Optional kann nun ein zweiter `notify`-Dienst konfiguriert werden, damit Meldungen an zwei Geräte/Ziele gehen.
- **Release Notes aufgeräumt**: Alle `RELEASE_NOTES_*.md` liegen nun im Ordner `release_notes/`.
- **Coordinator weiter entlastet**: `coordinator.py` fokussiert sich weiter auf Ablaufsteuerung, Quellpriorisierung und Ergebniszusammenführung.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.1.md` auf den aktuellen Stand gebracht.

## [1.1.0] - 2026-06-19

- **Refactoring-Start für 1.1.x**: Wartungs-/History-Logik wurde aus `coordinator.py` in `maintenance.py` ausgelagert.
- **Berechnungslogik ausgelagert**: Chlor-, pH-, Nachmess- und Empfehlungslogik liegt nun in `calculation.py`, damit sie künftig gezielter getestet und angepasst werden kann.
- **Coordinator entlastet**: `coordinator.py` bleibt für Home-Assistant-Orchestrierung, Datenbeschaffung, Persistenz und Zusammenführung verantwortlich.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.1.0.md` auf den aktuellen Stand gebracht.

## [1.0.23] - 2026-06-19

- **Forecast-Logspam behoben**: Die Lovelace-Karte ruft Wetter-Forecasts im Frontend nicht mehr über den problematischen `weather.get_forecasts`-Servicepfad ab, der im Dashboard-Kontext WebSocket-Fehler mit `return_response=True` auslösen konnte.
- **Stabileres Forecast-Nachladen**: Für Tagesvorhersagen wird nur noch der Forecast-Endpunkt verwendet. Wenn kein Ergebnis zurückkommt, verhindert ein Retry-Cooldown sofortige Endlosschleifen und Log-Spam.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.23.md` auf den aktuellen Stand gebracht.

## [1.0.22] - 2026-06-19

- **Tomorrow.io-Forecast-Fallback in der Karte**: Die Lovelace-Karte liest Tagesvorhersagen jetzt nicht mehr nur aus `attributes.forecast`, sondern lädt bei Bedarf aktiv `daily`-Forecasts über Home Assistants Weather-Forecast-API nach.
- **Kompatiblere Wetteranzeige**: Wetterkarten mit Providern wie `weather.tomorrow_io_home_daily` zeigen damit wieder heute und morgen an, auch wenn die Forecast-Daten nicht direkt als Attribut an der Entity hängen.
- **Wind-Einheit korrigiert**: Die Windanzeige verwendet jetzt die von der Wetter-Entity gelieferte Einheit (`wind_speed_unit`) statt kleine Werte pauschal als `m/s` zu behandeln.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.22.md` auf den aktuellen Stand gebracht.

## [1.0.21] - 2026-06-18

- **Wetter in der Lovelace-Karte**: Zwischen Empfehlung und weiteren Bereichen kann jetzt eine Vorhersage für heute und morgen aus einer konfigurierbaren `weather`-Entität angezeigt werden, inklusive Sonne/UV, Regen und Wind.
- **Optionale Wetterquelle in der Integration**: Config Flow und Options Flow unterstützen jetzt eine `weather`-Entität direkt in der Integration, statt die Wetterlogik nur an die Kartenkonfiguration zu binden.
- **Konservative Wetterlogik für Chlor**: Hoher `uv_index` erhöht den Chlor-Zielbedarf leicht über einen separaten `UV-Zuschlag` im Breakdown.
- **Regen als Nachmess-Hinweis**: Erwarteter starker Regen führt zunächst nicht zu harter Überdosierung, sondern zu einem expliziten Hinweis, danach möglichst erneut zu messen.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.21.md` auf den aktuellen Stand gebracht.

## [1.0.20] - 2026-06-18

- **Nutzungsmodus korrigiert**: `none`, `normal` und `party` beeinflussen die finale Chlorempfehlung jetzt auch bei aktivem Stoßchlor-Ziel. Zuvor war die Endmenge in solchen Fällen fälschlich identisch, obwohl sich nur die Breakdown-Zeilen änderten.
- **Whirlpool-Fälle geprüft**: Für den gezeigten 0,916 m³-Fall ergibt die korrigierte Logik jetzt ca. `8,1 g` bei keiner Nutzung, `8,9 g` bei normaler Nutzung und `9,7 g` bei Party.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.20.md` auf den aktuellen Stand gebracht.

## [1.0.19] - 2026-06-18

- **Chlorlogik neu aufgebaut**: Die Chlorberechnung arbeitet jetzt über volumenbezogene Zielkonzentrationen in `mg/l` und rechnet erst am Ende über das konfigurierte `pool_volume` in Gramm Produkt um.
- **Plausiblere Whirlpool-Dosierung**: Feste Grammzuschläge für kleine Becken entfallen. Temperatur, offenes Becken, Nutzung und Stoßchlorung werden jetzt fachlich konsistenter berücksichtigt.
- **Frontend-Breakdown angepasst**: Die Karte zeigt jetzt `Stoßchlor-Ziel`, `Temperatur-Zuschlag`, `Offenes Becken` und `Nutzung` statt der alten Faktor-Begriffe.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.19.md` auf den aktuellen Stand gebracht.

## [1.0.16] - 2026-06-18

### Neu
- **Nachmess-Workflow in der Karte**: Nach bestätigter Chlor-, pH-Minus- oder pH-Plus-Zugabe zeigt die Integration jetzt **Warten auf erneute Messung**, bis neue Werte eingelesen wurden.
- **LayZSpa Zieltemperatur-Steuerung**: Die Karte kann die Zieltemperatur jetzt optional direkt per `+` / `-` über `number.*`- oder `climate.*`-Entitäten anpassen.
- **Markdown Release Notes**: Neue Datei `release_notes/RELEASE_NOTES_V1.0.16.md` für den GitHub-Release.

### Verbesserungen
- **Live-BLE-Status**: Die Zeile **BT Verbindung** ist nur während eines aktiven PoolLab-BLE-Abrufs grün und springt nach dem Disconnect wieder auf rot.
- **Dokumentation aktualisiert**: README und technische Doku spiegeln jetzt den aktuellen Ablauf für BLE, Cloud, Nachmessung und LayZSpa-Temperatursteuerung wider.

### Fixes
- **Keine sticky BLE-Anzeige mehr**: `bluetooth_connected` wird nicht mehr persistent als letzter Erfolgszustand gehalten.
- **Fachlich sauberere Dosieranzeige**: Bereits protokollierte Chemiezugaben führen nicht mehr dazu, dass alte Empfehlungen weiter aktiv dargestellt werden.

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
