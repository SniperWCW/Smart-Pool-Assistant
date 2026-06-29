# Changelog - Smart Pool Assistant

## [3.0.16] - 2026-06-29

- **CYA-Prognosetext fachlich praezisiert**: Die Anzeige beschreibt sinkende oder steigende Werte jetzt als modellierten Netto-Effekt statt als natuerlichen CYA-Abbau.
- **CYA-Ursachen klar benannt**: Sinkende Werte werden im Text auf dokumentierten Wasserwechsel, steigende Werte auf stabilisierte Chlorzugaben zurueckgefuehrt.
- **Release-Artefakte aktualisiert**: `manifest.json`, `README.md`, `TECHNISCHE_DOKUMENTATION.md`, Frontend-Versionshinweis und neue Release Notes wurden auf `3.0.16` angehoben.

## [3.0.15] - 2026-06-28

- **Schockchlorung jetzt konfigurierbar gedeckelt**: Neues Feld `chlor_shock_max` fuer die maximale automatische Schockchlorung in `mg/l`, z.B. `3.0` fuer Whirlpools.
- **Schockchlorungsgrenze wird jetzt wirklich eingehalten**: Die Berechnung kappt das Ziel sauber an der konfigurierten Obergrenze, auch wenn Temperatur, offene Abdeckung oder Nutzung weitere Zuschlaege liefern.
- **Benennung vereinheitlicht**: Frontend, Empfehlung, Config-Texte und Doku verwenden jetzt durchgaengig `Schockchlorung` statt `Stoßchlor`.
- **Release-Artefakte aktualisiert**: `manifest.json`, `README.md`, Frontend-Versionshinweis und neue Release Notes wurden auf `3.0.15` angehoben.

## [3.0.14] - 2026-06-28

- **Wirkstoff-Default fuer anorganisch korrigiert**: Der chlorproduktabhaengige Fallback nutzt jetzt `0.65` statt eines fachlich zu hohen `1.00`-Werts und greift konsistent in Berechnung, Lernlogik und CYA-Modell.
- **Wirkstofflogik zentralisiert**: Organisch/anorganisch und der daraus abgeleitete Wirkstoff-Fallback werden jetzt ueber einen gemeinsamen Helper vereinheitlicht, damit stille Abweichungen zwischen Config-Flow, Dosierung und Lernsystem vermieden werden.
- **CYA-Warnung auch bei anorganischem Chlor konsistent**: Werte ueber `80 ppm` erscheinen jetzt auch im Empfehlungstext wieder als `CYA hoch`, weil vorhandenes CYA die Wirksamkeit weiterhin beeinflusst, selbst wenn kuenftig unstabilisiert gechlort wird.
- **Dokumentation und Release-Artefakte aktualisiert**: README, Setup, Chemie-Doku, FAQ, technische Doku, Manifest, Frontend-Versionshinweis und neue Release Notes wurden auf `3.0.14` angehoben.

## [3.0.13] - 2026-06-28

- **Wetter-Forecast wieder wirksam in der Chemielogik**: Forecast-Status wird jetzt bis in den Tageskontext durchgereicht, sodass UV-Zuschlag und Regen-Hinweis wieder tatsaechlich in der Berechnung greifen.
- **BLE-Status sauber bis ins Frontend gespiegelt**: Nach erfolgreichem PoolLab-BLE-Abruf wird die Verbindung jetzt korrekt als aktiv markiert, ohne den eigentlichen Abrufpfad zu veraendern.
- **Config-Flow gegen doppelte BLE-Eintraege gehaertet**: Manuell eingetragene PoolLab-BLE-Adressen werden nun ebenfalls ueber die `unique_id` dedupliziert.
- **PoolLab-Button bei mehreren Eintraegen robuster zugeordnet**: Die Lovelace-Karte ordnet den manuellen Abruf-Button jetzt ueber die `config_entry_id` dem passenden Empfehlungssensor zu.

## [3.0.12] - 2026-06-28

- **Diagnose nicht mehr als Fehlerbox**: Verwarfene Chlor-Dosier-Samples aus der Reparatur-/Diagnoselogik werden nicht mehr als `WARNING`, sondern als unkritische Info protokolliert. Dadurch erscheint in Home Assistant keine irrefuehrende Fehlerbox mehr fuer fachliche Sample-Verwerfungen.

## [3.0.11] - 2026-06-28

- **Sample-Diagnose in Push erweitert**: Benachrichtigungen zu gewerteten oder verworfenen Chlor-Dosier-Samples enthalten jetzt direkt Vorherwert, Nachherwert, geloggte Gramm, theoretischen Anstieg und beobachteten Anstieg.

## [3.0.10] - 2026-06-28

- **Erste gueltige Nachmessung statt erste Nachmessung**: Fuer die Dosierqualitaet wird jetzt die erste Chlor-Nachmessung im gueltigen Fenster von `30 Minuten` bis `12 Stunden` nach der Zugabe verwendet. Zu fruehe Messungen blockieren damit kein spaeteres gueltiges Sample mehr.
- **Push-Hinweise fuer Dosier-Samples**: Nach einer Chlorzugabe weist die Integration jetzt auf das gueltige Nachmessfenster hin und informiert bei Sample-Erfolg oder Verwerfung mit Grund wie `zu frueh`, `zu spaet` oder `Faktor ausserhalb des Bereichs`.

## [3.0.9] - 2026-06-28

- **Manueller Reparatur-Service fuer Lernhistorie**: Neuer Service `smart_pool_assistant.repair_learning_history`, der den Lernhistorie-Abgleich erneut ausfuehrt und optional vorher einen frischen PoolLab-Abruf starten kann.
- **Sample-Diagnose im bestehenden Log**: Akzeptierte und verworfene Chlor-Dosier-Samples werden mit Grund, Zeitfenstern und Faktorwerten ins bestehende Diagnose-Log geschrieben.

## [3.0.8] - 2026-06-28

- **Quellsaubere Lernzeitstempel**: Chlor-, pH- und CYA-Lernen speichern Messpunkte jetzt mit dem Zeitstempel der tatsaechlichen Messquelle statt mit einem globalen Anzeige-Zeitstempel.
- **Reparaturpfad fuer Lernhistorie**: Historische PoolLab-BLE- und Cloud-Messungen werden beim Abruf in die Lernhistorie zurueckgespielt, damit verpasste Samples nach einem Timestamp-Mismatch wieder aufgebaut werden koennen.

## [3.0.7] - 2026-06-27

- **CYA-Verlauf als Prognosemodell**: Die Integration speichert jetzt CYA-Messpunkte dauerhaft und berechnet daraus zusammen mit Chlorprodukt, Chlorzugaben und Wasserwechseln einen modellierten CYA-Verlauf.
- **Wasserwechsel direkt protokollierbar**: In der Lovelace-Karte und im Service `log_maintenance` koennen Wasserwechsel jetzt in Litern oder Prozent dokumentiert werden.
- **CYA-Prognose sichtbar gemacht**: Die Karte zeigt jetzt einen modellierten aktuellen CYA-Wert, die geschaetzte Nettoveraenderung pro Tag und eine Prognose bis unter `80 ppm` bzw. ueber `100 ppm`.
- **Recorder-Problem entschärft**: `sensor.pool_empfehlung` haengt nicht mehr die komplette interne Historie als Attribut an, wodurch die Recorder-Warnung wegen zu grosser Attribute vermieden werden sollte.

## [3.0.6] - 2026-06-27

- **Chlorprodukt-Typ ergänzt**: Die Konfiguration unterscheidet jetzt zwischen `organisch / stabilisiert` und `anorganisch / unstabilisiert`.
- **Wirkstoff-Hinweis präzisiert**: Der Wirkstoffanteil erklaert jetzt direkt typische Startwerte fuer organisches und anorganisches Chlor.
- **CYA-Hinweise fachlich angepasst**: Die Lovelace-Karte bewertet Cyanursäure jetzt abhängig vom gewählten Chlorprodukt-Typ, damit anorganisches Chlor keine irreführenden CYA-Empfehlungen mehr auslöst.
- **CYA-Warnung in der Empfehlung**: Hohe Cyanursäure wird jetzt auch im Empfehlungstext als `CYA hoch` bzw. `CYA kritisch hoch` sichtbar.

## [3.0.5] - 2026-06-27

- **CYA-Zeile im Frontend verbessert**: `Cyanursäure` wird jetzt korrekt dargestellt, der Zielbereich `30-50 ppm` wird angezeigt und der Ist-Wert farblich eingeordnet.
- **CYA-Maßnahme direkt in der Tabelle**: Die letzte Spalte zeigt jetzt neben der Quelle auch eine passende Handlungsempfehlung abhängig vom gemessenen Cyanursäure-Wert.

## [3.0.4] - 2026-06-27

- **CYA jetzt wirklich bis zur Karte durchgereicht**: `sensor.pool_empfehlung` enthält nun auch `cyanuric_acid` und `cyanuric_acid_source` als Attribute, damit die Lovelace-Karte den bereits korrekt eingelesenen Wert auch anzeigen kann.
- **Frontend-/Backend-Pfad geschlossen**: Der PoolLab-BLE-Abruf war bereits erfolgreich, der fehlende Messwert lag nur noch in der Attribut-Weitergabe des Empfehlungssensors.

## [3.0.3] - 2026-06-27

- **CYA als echter PoolLab-Messwert**: Cyanursaeure aus PoolLab BLE wird jetzt bis in den Coordinator und ins Frontend als eigener aktueller Messwert inklusive Quelle durchgereicht.
- **Cloud-Pfad fuer CYA vorbereitet**: Falls die PoolLab-Cloud Cyanursaeure liefert, wird der Wert jetzt ebenfalls erkannt und in die Quellenlogik aufgenommen.
- **PoolLab-Abruf nach oben verlegt**: Die Lovelace-Karte zeigt den manuellen PoolLab-Abruf jetzt in einer dritten oberen Box neben `Status` und `Baden`, damit der Zugriff ohne Scrollen moeglich ist.
- **Messwerttabelle wieder fokussiert**: `Aktuelle Messwerte` enthaelt jetzt die neue CYA-Zeile und keinen separaten Abruf-Button mehr.

## [3.0.2] - 2026-06-26

- **Neueste Messquelle gewinnt pro Wert**: Chlor, pH und Temperatur werden jetzt quellenübergreifend nach Zeitstempel ausgewählt. Dadurch verdrängt ein älterer Bluetooth-Wert keinen neueren Messwert mehr.
- **PoolLab-BLE-Lesen des letzten Messblocks robuster**: Wenn der letzte `GET_MEASURES`-Block leer zurückkommt, versucht die Integration den Abruf mit alternativer `cell_id`-Byte-Reihenfolge erneut.
- **Leere PoolLab-Phantomdatensätze ignoriert**: BLE-Einträge mit `type=0`, `timestamp=0` und `value=0.0` werden nicht mehr als echte Messung übernommen.

## [3.0.1] - 2026-06-25

- **README deutlich besser lesbar aufgeteilt**: Die Hauptseite ist jetzt eine kompakte Landingpage mit Banner, Vorschau und klaren Links statt einer langen Vollreferenz.
- **Dokumentation in Themen-Seiten getrennt**: Neue Unterseiten fuer Setup, Chemielogik, Karte/Demos und Entitaeten machen die Projektdoku deutlich schneller erfassbar.
- **Konsistente Navigation zwischen den Doku-Seiten**: README, FAQ und alle neuen `docs/`-Seiten verlinken sich jetzt direkt gegenseitig.
- **Persoenlicher Dosierfaktor defensiver aktiviert**: Der gelernte Chlor-Dosierfaktor fliesst jetzt erst ab mindestens `5` verwertbaren Samples aktiv in die Chlorempfehlung ein.
- **Prognosetext fuer bereits zu niedrige Chlorwerte verbessert**: Statt `in 0 Stunden` meldet die Karte jetzt direkt, wenn Chlor bereits unter `0,6 mg/l` liegt.
- **Versionierung aktualisiert**: `README.md`, `FAQ.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V3.0.1.md` wurden auf `3.0.1` angehoben.

## [3.0.0] - 2026-06-25

- **GitHub- und lokaler Stand zusammengeführt**: Der Release basiert jetzt auf dem tatsächlich veröffentlichten GitHub-Stand und bündelt die manuell hochgeladenen `2.2.3`-Änderungen mit den lokalen Fixes in einem sauberen gemeinsamen Ausgangspunkt.
- **Dosierfaktor-Lernlogik fachlich gehärtet**: Der persönliche Chlor-Dosierfaktor nutzt nur noch zeitnahe Messpaare. Vorher-Messung und Nachmessung müssen jeweils innerhalb von `12 h` um die Zugabe liegen, damit späte Nachmessungen den Faktor nicht künstlich nach unten ziehen.
- **Diagnose deutlich schneller**: Die Chlor-Berechnungsdetails zeigen Volumen, gelernten Dosierfaktor und effektiven Wirkstoff direkt im Breakdown, damit Fälle wie `20 g trotz 0,916 m³` ohne Rätselraten nachvollziehbar werden.
- **FAQ für typische Supportfälle**: Neue `FAQ.md` mit den häufigsten Diagnosefällen rund um Volumen, Lernphase, Dosierfaktor und späte Nachmessungen.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `FAQ.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V3.0.0.md` auf den aktuellen Stand gebracht.

## [2.2.3] - 2026-06-24

- **Dosierfaktor-Lernlogik abgesichert**: Der persönliche Chlor-Dosierfaktor nutzt jetzt nur noch zeitnahe Messpaare. Vorher-Messung und Nachmessung muessen jeweils innerhalb von `12 h` um die Zugabe liegen, damit späte Nachmessungen den Faktor nicht unplausibel nach unten ziehen.
- **Breakdown-Diagnose erweitert**: Die Chlor-Berechnungsdetails zeigen jetzt zusätzlich den gelernten Dosierfaktor, den effektiven Wirkstoff und das verwendete Volumen direkt im Empfehlungsblock.
- **FAQ ergänzt**: Neue `FAQ.md` mit typischen Diagnosefällen, insbesondere zu zu hoher Chlorempfehlung bei kleinem Becken, Lernphase und spätem Nachmessen.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `FAQ.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.2.3.md` auf den aktuellen Stand gebracht.

## [2.2.2] - 2026-06-24

- **Volumen-Diagnose in der Chlor-Breakdown-Ansicht**: Die Lovelace-Karte zeigt jetzt direkt das fuer die Dosierberechnung verwendete Poolvolumen in `m³` und Litern an.
- **Abweichungen schneller sichtbar**: Wenn eine Chlorempfehlung nicht zur erwarteten Beckengroesse passt, ist jetzt sofort erkennbar, mit welchem Volumen der laufende Coordinator wirklich gerechnet hat.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.2.2.md` auf den aktuellen Stand gebracht.

## [2.2.1] - 2026-06-23

- **Zeitgewichteter Kontextverlauf**: `set_covered` und `set_usage` werden jetzt als eigener Verlauf gespeichert, damit Lernintervalle anteilig `offen/abgedeckt` und `none/normal/party` auswerten koennen.
- **Chlor-Stabilitaet kontextbereinigt**: Die Stabilitaetsbewertung nutzt neben dem rohen Tagesverlust jetzt auch eine heuristisch normalisierte Reihe, damit hohe Nutzung oder offene Abdeckung die Stabilitaetsampel nicht unnoetig verzerren.
- **Badetemperatur-Schwellen angepasst**: Die Temperaturgrenzen für die Badebewertung wurden nachgezogen.
- **Filterwechsel setzt Reinigung mit zurück**: Ein protokollierter Filterwechsel startet jetzt auch das Reinigungsintervall sauber neu, damit Anzeige, Sensoren und Benachrichtigungen konsistent bleiben.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.2.1.md` auf den aktuellen Stand gebracht.

## [2.2.0] - 2026-06-22

- **Persönlicher Chlor-Dosierfaktor**: Bestätigte Chlorzugaben und Nachmessungen werden jetzt als eigene Lernstrecke ausgewertet. Ab mindestens zwei verwertbaren Paaren fließt der persönliche Dosierfaktor direkt in die Chlorempfehlung ein.
- **Chlor-Prognose**: Neue Vorhersage für Tagesverlust sowie Zeit bis zur Zieluntergrenze oder bis `0,6 mg/l`, inklusive Konfidenz, Prognosebasis und kontextgewichteter Lernhistorie.
- **Kontextlernen erweitert**: Chlor-Messpunkte und Chlorzugaben speichern jetzt zusätzlich Temperatur, Abdeckung, Nutzungsmodus, Wetter/UV und optional Pumpenlaufzeit.
- **Optionale Pumpen-Entität**: Config Flow und Options Flow unterstützen jetzt `pump_entity` als `switch.*` oder `binary_sensor.*`, damit die Prognose reale Pumpenlaufzeit berücksichtigen kann.
- **Lovelace-Karte erweitert**: Die Stabilitätssektion zeigt jetzt Dosierfaktor, effektiven Wirkstoffanteil, Prognosehorizont, Konfidenz und Basis. Zusätzlich erscheint die aktuelle Chlor-Prognose direkt im Chlor-Empfehlungsblock.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V2.2.0.md` auf den aktuellen Stand gebracht.

## [2.1.11] - 2026-06-22

- **Eigenes Diagnose-Logfile**: Die Integration schreibt jetzt ein rotierendes DEBUG-Log nach `smart_pool_assistant_logs/smart_pool_assistant.log` im Home-Assistant-Konfigurationsverzeichnis.
- **PoolLab-Abrufe detaillierter nachvollziehbar**: Buttondruck, BLE-Geräteauflösung, Verbindungsdaten, Rohantworten, ausgewählte Messwerte, Cloud-Auswahl, Quellenpriorisierung und Wartungsaktionen werden im Diagnose-Log protokolliert.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.1.11.md` auf den aktuellen Stand gebracht.

## [2.1.10] - 2026-06-22

- **Bugfix PoolLab-BLE-Verbindungsaufbau**: Der zusätzliche 15-Sekunden-Timeout um `establish_connection(...)` wurde entfernt, damit `bleak-retry-connector` seine eigene Retry- und Safety-Timeout-Logik wieder vollständig nutzen kann.
- **Cleanup bleibt erhalten**: Das robuste Stoppen von Notifications und explizite Trennen der BLE-Verbindung aus `2.1.9` bleibt unverändert aktiv.
- **Dokumentation / Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und neue `release_notes/RELEASE_NOTES_V2.1.10.md` auf den aktuellen Stand gebracht.

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
- **Bugfix Schockchlorungs-Semantik**: `is_shock` steht jetzt für einen gemessenen Chlorwert im Schockchlorungsbereich von `3,0 bis 5,0 mg/l`, nicht mehr für zu niedrigen Chlorwert.
- **Badeampel korrigiert**: Die Karte zeigt nicht mehr `Schockchlorung aktiv` nach einer Empfehlung oder Zugabe, sondern bei passendem Messwert `Chlor im Schockchlorungsbereich`.
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

- **Nutzungsmodus korrigiert**: `none`, `normal` und `party` beeinflussen die finale Chlorempfehlung jetzt auch bei aktivem Schockchlorungsziel. Zuvor war die Endmenge in solchen Fällen fälschlich identisch, obwohl sich nur die Breakdown-Zeilen änderten.
- **Whirlpool-Fälle geprüft**: Für den gezeigten 0,916 m³-Fall ergibt die korrigierte Logik jetzt ca. `8,1 g` bei keiner Nutzung, `8,9 g` bei normaler Nutzung und `9,7 g` bei Party.
- **Versionierung aktualisiert**: `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und neue `release_notes/RELEASE_NOTES_V1.0.20.md` auf den aktuellen Stand gebracht.

## [1.0.19] - 2026-06-18

- **Chlorlogik neu aufgebaut**: Die Chlorberechnung arbeitet jetzt über volumenbezogene Zielkonzentrationen in `mg/l` und rechnet erst am Ende über das konfigurierte `pool_volume` in Gramm Produkt um.
- **Plausiblere Whirlpool-Dosierung**: Feste Grammzuschläge für kleine Becken entfallen. Temperatur, offenes Becken, Nutzung und Schockchlorung werden jetzt fachlich konsistenter berücksichtigt.
- **Frontend-Breakdown angepasst**: Die Karte zeigt jetzt `Schockchlorungsziel`, `Temperatur-Zuschlag`, `Offenes Becken` und `Nutzung` statt der alten Faktor-Begriffe.
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
