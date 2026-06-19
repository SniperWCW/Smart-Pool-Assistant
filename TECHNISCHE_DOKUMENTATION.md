# Smart Pool Assistant – Technische Dokumentation

**Projekt:** Smart Pool Assistant  
**Repository:** https://github.com/SniperWCW/Smart-Pool-Assistant  
**Integration Domain:** `smart_pool_assistant`  
**Dokumentationsstand:** 2026-06-19  
**Bezugsstand Codebasis:** lokaler Arbeitsstand am 2026-06-19 auf Basis von `manifest.json` Version `1.1.4`, inklusive manueller PoolLab-Abruf-UI, Live-BLE-Status, Nachmess-Workflow, ausgelagerter Berechnungs-, Wartungs-, Benachrichtigungs-, Wetter-, PoolLab-Cloud- und PoolLab-BLE-Auswahllogik sowie optionaler Wetterintegration mit Backend-Forecast-Fallback, separatem UV-Sensor und LayZSpa-Zieltemperatur-Steuerung

---

## 1. Zweck der Integration

Der **Smart Pool Assistant** ist eine Custom Integration für Home Assistant zur Pflege von Pool oder Whirlpool. Die Integration kombiniert Messwerte, Zielwerte, Dosierlogik, Wartungshistorie, PoolLab-Bluetooth, PoolLab-Cloud und eine eigene Lovelace-Karte zu einer zentralen Empfehlung.

Die Integration zeigt nicht nur Rohwerte an, sondern berechnet konkrete Handlungsanweisungen:

- Chlormenge zur Nachdosierung
- separate Vorab-Empfehlung vor dem Baden
- pH-Minus- oder pH-Plus-Mengen
- Filter-Reinigungs- und Wechselstatus
- Herkunft der aktuellen Messwerte
- Zeitpunkte der letzten Messung und der letzten Aktionen
- Status des letzten PoolLab-BLE-Abrufs

Die Architektur ist auf einen zentralen Coordinator mit ausgelagerter Fachlogik ausgelegt. Sensoren, Button-Entität und Frontend greifen auf dieselbe Datenbasis zu.

---

## 2. Aktueller Architekturstand

Die Integration folgt diesem Aufbau:

```text
Config Flow
   │
   ▼
Config Entry
   │
   ▼
SmartPoolCoordinator
   │
   ├── zyklischer Refresh (Cloud, manuelle Sensoren, Wartung, Persistenz)
   ├── manueller One-shot PoolLab-Abruf
   ├── BLE-Kommunikation und BLE-Auswertung ueber poollab_ble.py / poollab_ble_source.py
   ├── Cloud-Abruf ueber poollab_cloud.py
   ├── Zeitstempel- und Quellenlogik
   ├── Chemieberechnung ueber calculation.py
   ├── Filterwartung ueber maintenance.py
   ├── Benachrichtigungen ueber notifications.py
   └── zentrale Ausgabe in coordinator.data
   │
   ├── Sensor Platform
   ├── Button Platform
   └── Lovelace Custom Card
```

Wichtige Designentscheidung im aktuellen Stand:

- **BLE wird nicht zyklisch gepollt.**
- **Cloud-Daten werden weiterhin zyklisch abgerufen**, sofern ein API-Key konfiguriert ist.
- **Der Button `button.poollab_messwerte_abrufen` löst genau einen PoolLab-Abruf aus.**
- **Bei konfiguriertem BLE-Gerät priorisiert der manuelle Abruf BLE und verbindet sich nur einmal.**

---

## 3. Repository-Struktur

Die Home Assistant Integration liegt unter:

```text
custom_components/smart_pool_assistant/
```

Relevante Dateien:

```text
custom_components/smart_pool_assistant/
├── __init__.py
├── button.py
├── calculation.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── maintenance.py
├── notifications.py
├── poollab_cloud.py
├── poollab_ble.py
├── poollab_ble_source.py
├── sensor.py
├── services.yaml
├── strings.json
├── translations/
├── weather.py
└── frontend/
    └── pool-chemistry-card.js
```

Zusätzliche Projektdokumente im Root:

```text
README.md
Changelog.md
TECHNISCHE_DOKUMENTATION.md
release_notes/
```

### Dateiübersicht

| Datei | Aufgabe |
|---|---|
| `manifest.json` | Home Assistant Metadaten, Version, Requirements, Bluetooth-Matcher |
| `calculation.py` | reine Dosier-, Nachmess- und Empfehlungslogik |
| `const.py` | zentrale Konstanten und Config-Keys |
| `__init__.py` | Setup/Unload, Coordinator-Erzeugung, Service-Registrierung, Frontend-Registrierung |
| `config_flow.py` | UI-Konfiguration, Bluetooth Discovery und Options Flow |
| `coordinator.py` | Home-Assistant-Orchestrierung, Datenbeschaffung, Persistenz, Quellpriorisierung und PoolLab-Abrufablauf |
| `maintenance.py` | Wartungs-/History-Logik, Activity-Texte, Filterstatus und Zeitberechnung |
| `notifications.py` | Persistent Notifications, Notify-Service-Versand, Follow-up-Hinweise und Filterwarnungen |
| `poollab_cloud.py` | PoolLab-Cloud-GraphQL-Abruf und Normalisierung der Cloud-Messwerte |
| `poollab_ble.py` | direkte BLE-Kommunikation mit dem PoolLab 1.0 |
| `poollab_ble_source.py` | Auswahl der relevanten PoolLab-BLE-Messwerte und Type-ID-Mapping |
| `sensor.py` | Sensor-Entitäten auf Basis des Coordinators |
| `button.py` | native Button-Entität für den manuellen PoolLab-Abruf |
| `services.yaml` | Service-Definition für `smart_pool_assistant.log_maintenance` |
| `frontend/pool-chemistry-card.js` | Custom Lovelace Card inkl. Aktionen, Statusanzeige und optionalem LayZSpa-Panel |
| `weather.py` | Backend-Abruf und Normalisierung der Wetter-Entity sowie optionaler UV-Sensor fuer Chemie-Logik und Wetterkarte |

---

## 4. `manifest.json`

Aktueller Stand:

```json
{
  "domain": "smart_pool_assistant",
  "name": "Smart Pool Assistant",
  "version": "1.1.4",
  "documentation": "https://github.com/SniperWCW/Smart-Pool-Assistant",
  "issue_tracker": "https://github.com/SniperWCW/Smart-Pool-Assistant/issues",
  "dependencies": ["bluetooth"],
  "requirements": ["bleak-retry-connector>=3.5.0"],
  "config_flow": true,
  "iot_class": "local_polling",
  "integration_type": "service"
}
```

### Bedeutung

| Feld | Bedeutung |
|---|---|
| `domain` | interne Domain der Integration |
| `version` | aktuelle Manifest-Version |
| `dependencies` | Nutzung der Home Assistant Bluetooth-Infrastruktur |
| `requirements` | BLE-Verbindungsaufbau über `bleak-retry-connector` |
| `config_flow` | UI-Einrichtung über Home Assistant |
| `iot_class` | lokales Polling mit ergänzender Cloud-Komponente |
| `integration_type` | Integration mit eigenem Service und zusätzlicher Button-Plattform |

### Bluetooth-Erkennung

Das Manifest enthält Matcher für:

```text
PoolLab
PoolLab 1.0
PoolLab*
```

Damit kann Home Assistant passende Geräte als Kandidaten für die BLE-Konfiguration erkennen.

---

## 5. `const.py` – zentrale Konstanten

`const.py` enthält die Domain und sämtliche Config-Keys. Wichtige aktuelle Keys:

```python
DOMAIN = "smart_pool_assistant"
CONF_API_KEY = "api_key"
CONF_BLE_ADDRESS = "ble_address"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CHLOR_SENSOR = "chlor_sensor"
CONF_PH_SENSOR = "ph_sensor"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_POOL_VOLUME = "pool_volume"
CONF_CHLOR_TARGET = "chlor_target"
CONF_PH_TARGET = "ph_target"
CONF_CHLOR_CONTENT = "chlor_content"
CONF_PH_DOWN_DOSAGE = "ph_down_dosage"
CONF_PH_UP_DOSAGE = "ph_up_dosage"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_SERVICE_2 = "notify_service_2"
CONF_PERSISTENT_NOTIFICATION = "persistent_notification"
CONF_FOLLOW_UP_TIME = "follow_up_time"
```

Für Filterwartung zusätzlich:

```python
CONF_FILTER_CLEAN_INTERVAL
CONF_FILTER_REPLACE_INTERVAL
CONF_FILTER_CLEAN_YELLOW_THRESHOLD
CONF_FILTER_CLEAN_RED_THRESHOLD
CONF_FILTER_REPLACE_YELLOW_THRESHOLD
CONF_FILTER_REPLACE_RED_THRESHOLD
```

Neu gegenüber älteren Ständen ist besonders:

- `CONF_UPDATE_INTERVAL` ist wieder aktiv und steuert das zyklische Cloud-/Coordinator-Refresh-Intervall.

---

## 6. `__init__.py` – Setup, Plattformen und Frontend

### Geladene Plattformen

Aktueller Stand:

```python
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]
```

Damit erzeugt die Integration:

- Sensoren
- eine native Button-Entität

Sie erzeugt weiterhin **keine** eigene Switch-, Binary-Sensor- oder Number-Plattform.

### Setup-Ablauf

`async_setup_entry()` übernimmt:

1. `SmartPoolCoordinator` erstellen
2. Update-Listener registrieren
3. Coordinator unter `hass.data[DOMAIN][entry.entry_id]` speichern
4. Service `smart_pool_assistant.log_maintenance` registrieren
5. Wartungshistorie laden
6. ersten Refresh starten
7. Listener für manuelle Quellsensoren registrieren
8. Frontend-Datei registrieren
9. Sensor- und Button-Plattformen laden

### Service-Registrierung

Der Service `smart_pool_assistant.log_maintenance` bleibt im Backend der zentrale Weg, Wartungs- und Chemieaktionen zu protokollieren.

### Frontend-Registrierung

Die Lovelace-Karte wird unter diesem Pfad bereitgestellt:

```text
/smart_pool_assistant/pool-chemistry-card.js
```

Zusätzlich wird bei aktivem HA-Frontend `add_extra_js_url()` verwendet, damit die Karte automatisch verfügbar ist.

---

## 7. `config_flow.py` – Einrichtung und Re-Konfiguration

Die Integration lässt sich über den normalen Home Assistant Config Flow einrichten und unterstützt zusätzlich Bluetooth Discovery.

### Gültige Datenquellen

`validate_data_source()` akzeptiert mindestens eine der folgenden Quellen:

1. PoolLab API-Key
2. PoolLab BLE-Adresse
3. manuelle Sensoren für Chlor **und** pH

Wichtig:

- Für die rein manuelle Quelle müssen **Chlor und pH gemeinsam** vorhanden sein.

### Bluetooth Discovery

Bei erkannter BLE-Quelle wird die Adresse als Unique ID verwendet:

```python
await self.async_set_unique_id(discovery_info.address)
self._abort_if_unique_id_configured()
```

Damit wird eine Mehrfachkonfiguration desselben PoolLab verhindert.

### Schema und aktuelle Konfigurationsbereiche

Das aktuelle Formular deckt folgende Bereiche ab:

#### Datenquellen

- `ble_address`
- `api_key`
- `chlor_sensor`
- `ph_sensor`
- `temp_sensor`

#### Aktualisierung

- `update_interval` in Minuten
- Standard: `5`
- Bereich: `1` bis `60`

#### Poolparameter

- `pool_volume`
- `chlor_target`
- `ph_target`
- `chlor_content`

#### pH-Dosierung

- `ph_down_dosage`
- `ph_up_dosage`

#### Benachrichtigung

- `notify_service`
- `notify_service_2`
- `persistent_notification`
- `follow_up_time`

#### Filterwartung

- `filter_clean_interval`
- `filter_replace_interval`
- `filter_clean_yellow_threshold`
- `filter_clean_red_threshold`
- `filter_replace_yellow_threshold`
- `filter_replace_red_threshold`

### Aktuelle Default-Werte aus dem Config Flow

| Key | Default |
|---|---:|
| `update_interval` | 5 min |
| `pool_volume` | 0.916 m³ |
| `chlor_target` | 1.5 mg/l |
| `ph_target` | 7.2 |
| `chlor_content` | 0.56 |
| `ph_down_dosage` | 200 ml |
| `ph_up_dosage` | 100 g |
| `follow_up_time` | 60 min |
| `filter_clean_interval` | 24 h |
| `filter_replace_interval` | 5 Tage |
| `filter_clean_yellow_threshold` | 8 h |
| `filter_clean_red_threshold` | 2 h |
| `filter_replace_yellow_threshold` | 2 Tage |
| `filter_replace_red_threshold` | 1 Tag |

### Options Flow

Der Options Flow kombiniert `entry.data` und `entry.options`:

```python
current_config = {**self.config_entry.data, **self.config_entry.options}
```

Damit bleiben bisherige Werte als Default erhalten und spätere Änderungen wirken nach Reload direkt weiter.

---

## 8. `coordinator.py` – zentrale Logik

`SmartPoolCoordinator` ist das Herzstück der Integration. Er übernimmt:

- zyklische Aktualisierung
- manuellen PoolLab-Abruf
- Cloud-Abruf
- manuelle Sensor-Auswertung
- BLE-/Cloud-/Manuell-/Speicher-Priorisierung
- Persistenz über Home Assistant `Store`
- Chemieberechnung
- Filterwartung
- Benachrichtigungen
- Ausgabe aller Daten für Sensoren, Button und Karte

### Update-Intervall

Der Coordinator liest das Intervall aus Config/Options:

```python
update_interval=timedelta(minutes=update_interval_minutes)
```

Dieses Intervall steuert im aktuellen Stand:

- zyklischen Cloud-Abruf
- Wartungsstatus
- Benachrichtigungsprüfungen
- Zeitstempelaktualisierung

Es steuert **nicht** den BLE-Abruf.

### Persistenz

Gespeichert wird über:

```python
self._store = Store(hass, _STORAGE_VERSION, f"{_STORAGE_KEY}_{entry.entry_id}")
```

Persistiert werden unter anderem:

- letzte Messwerte
- letzte Messquellen-Zeitstempel
- letzte Aktivitäten
- Pool-Abdeckungsstatus
- Nutzungsmodus
- Batterie
- Cyanursäure
- PoolLab-Abrufstatus
- nächster erlaubter Button-Abrufzeitpunkt

### Kombinierte Config

```python
return {**self.entry.data, **self.entry.options}
```

Dadurch arbeitet die restliche Logik immer mit einem vereinheitlichten Konfigurationsobjekt.

---

## 9. Manueller PoolLab-Abruf

Der aktuelle PoolLab-Abruf ist bewusst zweigeteilt:

- **BLE nur manuell**
- **Cloud weiterhin zyklisch**

### Einstiegspunkt

Die Button-Entität ruft auf:

```python
await self.coordinator.async_fetch_poollab_measurements()
```

### Verhalten von `async_fetch_poollab_measurements()`

Die Methode:

1. prüft, ob wenigstens BLE oder API-Key konfiguriert ist
2. blockiert parallele Abrufe per `asyncio.Lock`
3. prüft einen Cooldown
4. setzt den Abrufstatus auf `running`
5. triggert genau einen Coordinator-Refresh
6. wertet danach `poollab_fetch_result` aus

### Cooldowns

Aktuelle Werte:

- Erfolg: `20` Sekunden
- Fehler: `30` Sekunden

Während des Cooldowns liefert die Methode einen Home Assistant Fehler zurück und aktualisiert den Abrufstatus auf `cooldown`.

### Verhalten je nach Konfiguration

#### Fall A: BLE-Adresse vorhanden

Dann gilt:

- der Button versucht genau **einen BLE-Verbindungsaufbau**
- es werden `GET_INFO` und `GET_MEASURES` gelesen
- danach wird sauber getrennt
- während dieses manuellen Abrufs wird **keine Cloud** als Parallelquelle verwendet

#### Fall B: kein BLE, aber API-Key vorhanden

Dann gilt:

- der Button kann als manueller One-shot-Cloud-Abruf arbeiten

### Abrufstatus-Daten

Der Coordinator stellt für UI und Automationen bereit:

- `poollab_fetch_result`
- `poollab_fetch_error`
- `last_poollab_fetch_requested_at`
- `last_poollab_fetch_completed_at`
- `next_poollab_fetch_allowed_at`

---

## 10. Datenquellen und Priorisierung

Aktiv genutzte Quellen:

1. BLE
2. Cloud/API
3. manuelle Sensoren
4. Persistenzspeicher

### Quelle 1: BLE

BLE wird nur verwendet, wenn `perform_remote_fetch` aktiv ist, also nur beim expliziten Button-Abruf.

Gelesene Fachwerte:

- Chlor
- pH
- Temperatur
- Cyanursäure
- Batterie

Die aktuelle Mapping-Logik im Coordinator:

```text
Chlor: 1, 8, 3
pH: 9, 27, 28, 29, 30, 31, 32, 33, 34, 36, 48
Temperatur: 4
Cyanursäure: 11
```

### Quelle 2: Cloud/API

Cloud wird zyklisch verwendet, wenn:

- ein API-Key konfiguriert ist
- noch keine Chlor-/pH-Werte aus einer vorrangigen Quelle für den aktuellen Lauf vorliegen
- kein manueller BLE-Abruf mit vorhandener BLE-Adresse läuft

Die Abfrage erfolgt per GraphQL gegen:

```text
https://backend.labcom.cloud/graphql
```

Verwendete Parameter:

```text
PL Chlorine Free
PL pH
PL Temperature
```

Zusätzlich speichert der Coordinator die letzten vier Cloud-Messwerte in `last_api_measurements` für Anzeige und Fehlersuche.

### Quelle 3: manuelle Sensoren

Manuelle Sensoren werden immer geprüft. Sie ergänzen fehlende Werte aus BLE oder Cloud.

Zeitstempelquelle für manuelle Sensoren:

1. Attribut `measured_at`
2. Attribut `timestamp`
3. `state.last_updated`

### Quelle 4: Speicher

Wenn aktuell keine aktive Quelle Werte liefert, wird auf persistierte letzte Werte zurückgegriffen:

- `last_c`
- `last_ph`
- `last_temp`

Dann wird die Quelle als `Speicher` markiert.

### Caching neuerer BLE-Werte

Wenn ein späterer Lauf keine frischen BLE-Werte liefert, aber ältere Cloud-Daten vorliegen, kann der Coordinator gespeicherte BLE-Werte weiter bevorzugen, sofern deren Zeitstempel neuer sind als die Cloud-Daten.

Das verhindert ein Zurückspringen von frischen BLE-Werten auf ältere Cloud-Messungen.

### Quellenattribute

Der Coordinator liefert:

- `chlor_source`
- `ph_source`
- `temp_source`
- `last_measurement_source`
- `data_source`

`data_source` kann zusammengesetzt sein, z. B.:

```text
Bluetooth & Manuell
Cloud
Speicher
Nicht verfügbar
```

---

## 11. BLE-Verbindungsstatus

Die Karte zeigt eine Zeile **BT Verbindung**. Backend-seitig basiert diese auf:

```text
bluetooth_connected
```

Wichtige Semantik im aktuellen Stand:

- `true` bedeutet: es laeuft genau jetzt ein aktiver manueller BLE-Abruf mit bestehender Verbindung
- `false` bedeutet: aktuell keine BLE-Verbindung aktiv

Das ist **kein Dauer-Connection-Status**. Die Integration haelt die BLE-Verbindung nicht offen, sondern verbindet sich nur kurz fuer den One-shot-Abruf und trennt danach wieder. Die Karte kombiniert dafuer den Backend-Wert mit ihrem lokalen In-Flight-Status, damit der Benutzer den Connect bereits waehrend des laufenden Abrufs als gruen sieht.

---

## 12. `poollab_ble.py` – direkte BLE-Kommunikation

Diese Datei kapselt die Kommunikation mit dem PoolLab 1.0.

### UUIDs

```python
SERVICE_UUID = "a7ee04a9-507b-4910-a528-b619d5501924"
MOSI_UUID = "91bfa536-3036-4901-8813-3635fced7b90"
MISO_UUID = "2ff18b59-195d-4ee1-b78c-0cbde3eff9c2"
SIGNAL_UUID = "c2296c06-c7e0-4657-b42e-c8330826454c"
```

### Datenklassen

#### `PoolLabMeasurement`

```python
@dataclass
class PoolLabMeasurement:
    measure_id: int
    measure_type: int
    status: int
    timestamp: int
    value: float
```

#### `PoolLabData`

```python
@dataclass
class PoolLabData:
    battery: int
    measurements: dict[int, PoolLabMeasurement]
```

### Aktueller BLE-Ablauf

`async_read_data()`:

1. verbindet sich über `establish_connection`
2. startet Notifications
3. wartet bewusst kurz für Proxy-Stabilität
4. sendet `GET_INFO`
5. liest Batteriestand und Anzahl Messwerte
6. liest gespeicherte Messdaten blockweise per `GET_MEASURES`
7. parst Datensätze
8. stoppt Notifications
9. wählt pro `measure_type` den neuesten Datensatz mit `STATUS_OK`
10. gibt `PoolLabData` zurück

### Stabilitätsmaßnahmen für Proxy/BLE

Der aktuelle Code ist bewusst zurückhaltender als frühere Stände:

- Retry für `start_notify`
- kurze Settling-Delays vor Write und Read
- erneuter Retry für `GET_INFO`
- Retry pro `GET_MEASURES`-Chunk
- kein paralleler Abruf

Das ist besonders für ESPHome Bluetooth Proxy relevant.

---

## 13. Chemieberechnung

Die Chemieberechnung findet vollständig im Coordinator statt.

### Chlorberechnung

Eingänge:

- `chlor_ist`
- `chlor_target`
- `pool_volume`
- `chlor_content`
- `temp_ist`
- `pool_covered`
- `usage_mode`

### Aktuelle Faktoren

Die Basisdosis wird aus `Ziel - Ist`, Volumen und Wirkstoffanteil berechnet.
Alle Zusatzlogiken arbeiten als zusaetzliche Zielkonzentration in `mg/l`
(Temperatur, offenes Becken, Nutzung, Stoßchlorung). Erst ganz am Ende wird
die benoetigte Gesamtkonzentration ueber das konfigurierte Poolvolumen und den
Wirkstoffanteil in Gramm Produkt umgerechnet.

#### Temperatur-Zuschlag

```text
> 32 °C  -> +0.7 mg/l
> 28 °C  -> +0.3 mg/l
sonst    -> +0.0 mg/l
```

#### Stoßchlor-Ziel

```text
chlor < 0.1 -> Ziel 5.0 mg/l
chlor < 0.3 -> Ziel 4.0 mg/l
chlor < 0.6 -> Ziel 3.0 mg/l
chlor < 1.0 -> Ziel 2.0 mg/l
sonst       -> kein Stoßziel
```

#### Abdeckungs-Zuschlag

```text
abgedeckt -> +0.0 mg/l
offen     -> +0.3 mg/l
```

#### Nutzungsmodus

```text
none   -> +0.0 mg/l
normal -> +0.5 mg/l
party  -> +1.0 mg/l
```

#### Mindestdosis

```text
chlor < 0.3 -> 6.0 g pro m³
chlor < 0.8 -> 3.0 g pro m³
sonst       -> 2.0 g pro m³
```

#### Maximaldosis

```text
maximales Ziel: 10.0 mg/l freies Chlor
```

#### Zielwert-Sperre

Wenn `chlor_ist >= chlor_target`, dann:

```text
chlor_dose = 0.0
```

### Chlor-Ausgaben

- `chlor_dose`
- `chlor_pre`

`chlor_pre` wird aktuell berechnet als:

```python
round(max(chlor_dose * 0.3, 1.0 * pool_volume), 1) if chlor_dose > 0 else 0.0
```

### Breakdown-Werte

Für die Karte werden detaillierte Teilwerte geliefert:

- `chlor_breakdown_base`
- `chlor_breakdown_shock_adj`
- `chlor_breakdown_temp_adj`
- `chlor_breakdown_env_adj`
- `chlor_breakdown_bather_adj`
- `chlor_breakdown_sum_raw`
- `chlor_breakdown_min_dose_applied`

### pH-Berechnung

Aktuelle Ausgaben:

- `ph_senker_total`
- `ph_erhoeher_total`

Berechnungslogik:

- `ph_diff < 0`: pH zu hoch, `ph_senker_total`
- `ph_diff > 0`: pH zu niedrig, `ph_erhoeher_total`

Formeln:

```python
factor_down = ph_down_dosage / 10.0 / 0.2
factor_up = ph_up_dosage / 10.0 / 0.1
```

---

## 14. Empfehlungstext und Warnlogik

Die finale Empfehlung wird zentral im Coordinator erstellt.

Vor den normalen Warnregeln greift zusaetzlich ein Nachmess-Schutz:

```text
wenn empfohlene Chemie bereits nach der letzten Messung protokolliert wurde
-> "⏳ Warten auf erneute Messung"
```

Damit verhindert die Integration, dass bereits "verbrauchte" Messwerte weiter als aktive Handlungsempfehlung erscheinen.

Aktuelle Warnregeln:

### pH

```text
pH > Ziel + 0.1 -> "pH zu hoch"
pH < Ziel - 0.1 -> "pH zu niedrig"
```

### Chlor

```text
chlor < 0.5 -> "Stoßchlorung empfohlen"
chlor > Ziel + 0.2 -> "Chlor zu hoch"
chlor < Ziel - 0.2 und chlor_dose > 0 -> "Chlor nachdosieren"
```

### Ausgabe

Wenn keine Warnung aktiv ist:

```text
✅ Alle Werte im Zielbereich
```

Sonst:

```text
⚠️ <Warnung 1> & <Warnung 2> ...
```

---

## 15. Wartungshistorie und Aktionen

### Persistierte Aktionsarten

```text
chlor
ph_plus
ph_minus
filter_clean
filter_replace
set_covered
set_usage
```

### `async_log_maintenance()`

Diese Methode:

1. speichert die Aktion in `maintenance_history`
2. aktualisiert `last_action`
3. pflegt `last_activities`
4. aktualisiert Pool-Abdeckung oder Nutzungsmodus
5. sendet optional Benachrichtigungen
6. startet bei Chemieaktionen einen Follow-up-Timer
7. triggert einen Refresh

### Follow-up

Ein Follow-up wird nur gesetzt für:

- `chlor`
- `ph_plus`
- `ph_minus`

Der Text lautet:

```text
Die Einwirkzeit ist um. Bitte Pool-Werte erneut prüfen!
```

---

## 16. Filterwartung

Die Integration verfolgt:

- Stunden seit letzter Filterreinigung
- Tage seit letztem Filterwechsel
- Fälligkeitsstatus
- Benachrichtigungen

### Statuswerte

```text
unknown
ok
warning
critical
```

Berechnung:

```python
time_until_due = interval - time_since
```

Dann:

- `<= red_threshold` -> `critical`
- `<= yellow_threshold` -> `warning`
- sonst -> `ok`

### Exportierte Attribute

- `hours_since_filter_clean`
- `filter_clean_status`
- `filter_clean_interval`
- `days_since_filter_replace`
- `filter_replace_status`
- `filter_replace_interval`
- `weather_condition_today`
- `weather_temperature_today`
- `weather_wind_speed_today`

### Benachrichtigungen

Benachrichtigungen koennen an bis zu zwei konfigurierte `notify`-Dienste gesendet werden:

- `notify_service`
- `notify_service_2`

Die Filterbenachrichtigungen werden maximal einmal pro Tag pro Status versendet. Wenn beide Notify-Ziele identisch gesetzt sind, wird nur einmal gesendet.

---

## 17. `services.yaml` – Service API

Weiterhin vorhanden:

```yaml
smart_pool_assistant.log_maintenance
```

### Felder

| Feld | Pflicht | Bedeutung |
|---|---:|---|
| `entity_id` | ja | Ziel-Entität der Integration |
| `type` | ja | Aktionstyp |
| `amount` | ja | Menge oder Steuerwert |

### Unterstützte Typen

```text
chlor
ph_plus
ph_minus
filter_clean
filter_replace
set_covered
set_usage
```

### Steuerwerte

Für `set_usage` gilt:

```text
0 = none
1 = normal
2 = party
```

Für `set_covered` gilt:

```text
0 = offen
1 = abgedeckt
```

---

## 18. `sensor.py` – Sensorplattform

Beim Setup werden aktuell diese Sensoren angelegt:

```python
Pool Chlor Nachdosierung
Pool Chlor Vor Baden
Pool PH-Minus
Pool PH-Plus
Pool Chlor Istwert
Pool pH Istwert
Pool Temperatur Istwert
Pool Datenquelle
Pool Abdeckung Status
Pool Nutzungsmodus
Pool Filter Reinigung Fällig
Pool Filter Wechsel Fällig
Pool Cyanursäure
PoolLab Batterie
Pool Empfehlung
```

### Besondere Sensoren

#### `PoolLab Batterie`

- Device Class: `battery`
- Einheit: `%`
- Wertquelle: `history.ble_battery`

#### `Pool Empfehlung`

Der Statussensor ist die zentrale Frontend-Schnittstelle.

Wichtige aktuelle Attribute:

- `last_calculation`
- `last_measurement`
- `last_measurement_source`
- `chlor_ist`
- `ph_ist`
- `temp_ist`
- `chlor_source`
- `ph_source`
- `temp_source`
- `chlor_target`
- `ph_target`
- `chlor_dose`
- `chlor_pre`
- `ph_senker_total`
- `ph_erhoeher_total`
- `data_source`
- `bluetooth_connected`
- `last_api_measurements`
- `last_activities`
- `poollab_fetch_result`
- `poollab_fetch_error`
- `last_poollab_fetch_requested_at`
- `last_poollab_fetch_completed_at`
- `next_poollab_fetch_allowed_at`
- `awaiting_retest`
- `awaiting_retest_chlor`
- `awaiting_retest_ph`
- `awaiting_retest_since`
- `filter_clean_status`
- `filter_replace_status`
- `chlor_breakdown_*`

---

## 19. `button.py` – native Button-Plattform

Neu gegenüber älteren Doku-Ständen ist die eigene Button-Plattform.

### Entität

```text
button.poollab_messwerte_abrufen
```

### Erzeugung

Die Button-Entität wird erstellt, wenn mindestens eine dieser Quellen konfiguriert ist:

- `ble_address`
- `api_key`

### Verhalten

`async_press()` ruft ausnahmslos:

```python
await self.coordinator.async_fetch_poollab_measurements()
```

### Button-Attribute

Der Button selbst exportiert zusätzlich:

- `last_fetch_requested_at`
- `last_fetch_completed_at`
- `last_fetch_result`
- `last_fetch_error`
- `next_fetch_allowed_at`

Damit lässt sich der Abruf auch außerhalb der Karte diagnostizieren.

---

## 20. Frontend – `pool-chemistry-card.js`

Die Karte ist eine Custom Lovelace Card:

```yaml
type: custom:pool-chemistry-card
recommendation_entity: sensor.pool_empfehlung
```

### Aktuelle Hauptaufgaben

Die Karte:

- zeigt die zentrale Empfehlung
- zeigt Messwerte und Zielwerte
- zeigt Messquellen
- zeigt BLE-Verbindungsstatus
- integriert den PoolLab-Abrufbutton
- zeigt einen Wartezustand nach bestaetigten Chemiezugaben
- protokolliert Chemie- und Wartungsaktionen
- zeigt Filterwartung
- zeigt Berechnungsdetails
- zeigt letzte Aktivitäten
- zeigt Cloud-Messhistorie
- zeigt optional Wetter heute und morgen aus einer `weather`-Entitaet
- unterstützt optional ein LayZSpa-Panel

### Neue PoolLab-Abruf-UI

Die Messwertetabelle enthält aktuell zwei relevante Zeilen:

- `BT Verbindung`
- `PoolLab Abruf`

Die Karte ermittelt den Button standardmäßig automatisch:

1. `config.fetch_button_entity`, falls gesetzt
2. `button.poollab_messwerte_abrufen`
3. erste passende Fallback-Entität mit diesem Prefix

### Statuslogik des Karten-Buttons

`_getPoolLabFetchUi()` kennt folgende UI-Zustände:

- `fehlt`
- `läuft`
- `warte`
- `fehler`
- `bereit`

Die Karte zeigt passend dazu:

- Button-Label
- deaktiviert/aktiv
- Status-Text
- Meta-Spalte

### BLE-Statusanzeige

Die Zeile **BT Verbindung** nutzt:

```javascript
this._poollabFetchInFlight || attr.bluetooth_connected === true
```

Darstellung:

- grün: `Bluetooth: Ja`
- rot: `Bluetooth: Nein`

Die Anzeige ist damit bewusst live und springt nach dem Disconnect wieder zurueck.

### Nachmess-Zustand in der Karte

Die Karte wertet zusaetzlich diese Attribute aus:

- `awaiting_retest`
- `awaiting_retest_chlor`
- `awaiting_retest_ph`

Wenn sie aktiv sind:

- wechselt die Statusbox auf `⏳ Warten auf erneute Messung`
- die betroffenen Dosierfelder werden deaktiviert
- alte Chlor- oder pH-Empfehlungen werden nicht weiter als aktive Handlungsanweisung dargestellt

### Card Editor

Im Karten-Editor gibt es aktuell zusätzlich:

```text
PoolLab-Abruf-Button (optional)
Ziel-Temperatur Steuerung
```

Damit kann die Karte explizit auf eine konkrete Button-Entitaet gebunden werden. Fuer LayZSpa kann zusaetzlich eine `number.*`- oder `climate.*`-Entitaet fuer die Zieltemperatur-Steuerung hinterlegt werden.

### Wetter-Forecast in der Karte

Wenn eine `weather`-Entitaet konfiguriert ist, rendert die Karte einen Block fuer heute und morgen.

Abrufreihenfolge:

1. Direktes `attributes.forecast` der Wetter-Entitaet
2. Falls leer: Backend-Abruf ueber Home Assistants Wetter-Service mit `type: daily`
3. Optionaler UV-Wert aus separat konfiguriertem `uv_sensor`
4. Falls weiterhin leer: Fallback auf Coordinator-Attribute fuer das heutige Wetter

Damit bleibt die Karte kompatibel mit Integrationen, die Tagesvorhersagen nicht dauerhaft im Entity-Attribut halten, sondern nur dynamisch ueber den Wetter-Service bereitstellen. Fuer UV kann zusaetzlich eine eigene Sensor-Entity konfiguriert werden, wenn der Wetter-Provider den UV-Index nicht im Daily-Forecast liefert. Die normalisierten Forecast-Tage werden vom Coordinator als `weather_forecast_days` an den Empfehlungssensor und von dort an die Karte weitergereicht. Wenn auch dort kein Daily-Forecast verfuegbar ist, zeigt die Karte zumindest die heutigen Wetterdaten aus dem Coordinator bzw. aus den aktuellen Weather-Entity-Attributen.

Die Frontend-Ressource wird mit der Manifest-Version als Cachebuster registriert, damit Kartenfixes nach einem Update zuverlaessig neu geladen werden.

Fuer die Darstellung nutzt die Karte aktuell vor allem:

- `condition`
- `temperature`
- `templow`
- `precipitation_probability`
- `wind_speed`
- `wind_speed_unit`

### Messwertanzeige

Die Karte zeigt:

- Chlor Ist/Ziel
- pH Ist/Ziel
- Temperatur
- Quelle je Wert

Farbgrenzen:

```text
Chlor: grün bis ±0.3, gelb bis ±0.7, sonst rot
pH:    grün bis ±0.1, gelb bis ±0.3, sonst rot
```

### Cloud-Historie

Wenn `last_api_measurements` vorhanden ist, wird eine Tabelle mit:

- Parameter
- Wert
- Zeit

angezeigt.

### LayZSpa

Die LayZSpa-Sektion ist weiterhin optional und rein frontend-getrieben. Sie arbeitet mit vorhandenen Home Assistant Entitaeten und nicht mit eigener Backend-Logik der Integration.

Aktueller Stand:

- Anzeige von Ist- und Zieltemperatur
- optionale Zieltemperatur-Steuerung unterhalb der Temperaturanzeige
- Steuerung ueber `layzspa.temp_target_control`
- unterstuetzt `number.*` und `climate.*`
- Schrittweite sowie Min-/Max-Grenzen werden aus der Zielentitaet uebernommen

---

## 21. Datenfluss im aktuellen Stand

### Zyklischer Lauf

```text
DataUpdateCoordinator Timer
   │
   ▼
_async_update_data()
   │
   ├── kein BLE-Connect
   ├── Cloud lesen, falls API-Key vorhanden
   ├── manuelle Sensoren prüfen
   ├── neuere gespeicherte BLE-Werte bevorzugen
   ├── Speicher-Fallback anwenden
   ├── Zeitstempel synchronisieren
   ├── Chemie berechnen
   ├── Filterstatus berechnen
   ├── Benachrichtigungen prüfen
   └── Ergebnisdict zurückgeben
```

### Manueller BLE-Abruf

```text
Button press
   │
   ▼
async_fetch_poollab_measurements()
   │
   ├── Lock prüfen
   ├── Cooldown prüfen
   ├── Status auf running setzen
   ├── _poollab_fetch_requested = True
   ├── async_request_refresh()
   │    └── _async_update_data()
   │         └── BLE lesen, falls BLE konfiguriert
   ├── Status speichern
   └── Fehler oder Erfolg an UI/Entity zurückgeben
```

### Manueller Cloud-Abruf ohne BLE

```text
Button press
   │
   ▼
async_fetch_poollab_measurements()
   │
   └── _async_update_data()
        └── Cloud lesen, wenn kein BLE konfiguriert ist
```

### Aktion über UI

```text
Kartenbutton oder Service
   │
   ▼
smart_pool_assistant.log_maintenance
   │
   ▼
async_log_maintenance()
   │
   ├── Aktion speichern
   ├── last_activities aktualisieren
   ├── Benachrichtigung senden
   ├── Follow-up setzen
   └── Refresh auslösen
```

---

## 22. Zeitstempel-Logik

Relevante Zeitstempel:

```text
last_calc_raw
last_manual_measurement_raw
last_api_measurement_raw
last_ble_measurement_raw
last_measurement_raw
```

### Zweck

| Zeitstempel | Bedeutung |
|---|---|
| `last_calc_raw` | letzter Berechnungslauf |
| `last_manual_measurement_raw` | letzte manuelle Sensoränderung |
| `last_api_measurement_raw` | letzte Cloud-Messung |
| `last_ble_measurement_raw` | letzte BLE-Messung |
| `last_measurement_raw` | für die UI aktuell relevantester Messzeitpunkt |

Die Anzeige von `last_measurement_source` priorisiert die tatsächlich neueste Quelle unter BLE, Cloud und Manuell.

---

## 23. Persistenz und Neustartverhalten

Durch `Store` bleiben nach einem Neustart erhalten:

- letzte Werte
- letzte Aktivitäten
- Zeitpunkte der Wartungen
- Abdeckungsstatus
- Nutzungsmodus
- letzte Cloud-Messwerte
- letzte BLE-Werte
- Batteriestand
- Cyanursäure
- Status des letzten PoolLab-Abrufs
- Abruf-Cooldown

Dadurch kann die Karte auch ohne aktuelles BLE-Gerät oder ohne frische Cloud-Daten weiter mit sinnvollen Speicherwerten arbeiten.

---

## 24. Wichtige Unterschiede zu älteren Doku-Ständen

Die folgenden Punkte waren in älteren Dokumentationen teils anders beschrieben und sind jetzt bewusst aktualisiert:

- Es gibt inzwischen eine **native Button-Plattform**.
- `PLATFORMS` ist **nicht mehr nur `SENSOR`**, sondern `SENSOR` und `BUTTON`.
- BLE wird **nicht mehr zyklisch** gelesen.
- Das **Cloud-Intervall ist wieder konfigurierbar** und läuft weiterhin zyklisch.
- Die Lovelace-Karte enthält jetzt einen **integrierten PoolLab-Abruf-Button**.
- Die Karte kann optional eine eigene `fetch_button_entity` konfigurieren.
- `bluetooth_connected` ist jetzt ein Live-Status nur fuer den aktiven BLE-Abruf und keine persistente "letzter Erfolg"-Anzeige mehr.
- Die Karte kennt jetzt einen expliziten Nachmess-Zustand nach Chemiezugaben.
- Das LayZSpa-Panel kann optional die Zieltemperatur direkt verstellen.

---

## 25. Entwicklerhinweise

### Zentrale Erweiterungspunkte

| Erweiterung | Datei |
|---|---|
| neue Berechnungslogik | `coordinator.py` |
| neue Sensoren | `sensor.py` |
| neue Buttons | `button.py` |
| neue Config-Optionen | `const.py`, `config_flow.py` |
| neue UI-Felder | `frontend/pool-chemistry-card.js` |
| neue Wartungsaktionen | `services.yaml`, `__init__.py`, `coordinator.py` |
| neue PoolLab-Parameter | `poollab_ble.py`, Mapping in `poollab_ble_source.py` |

### Technische Schulden / sinnvolle nächste Schritte

- Aufteilung von `coordinator.py` in kleinere Fachmodule
- Unit Tests für Chlor-, pH- und Quellenlogik
- Diagnostics-Schnittstelle für Supportfälle
- konsolidierte Konstanten/Defaults für Filter-Intervalle an einer Stelle

---

## 26. Kurzfazit

Der aktuelle Smart Pool Assistant ist technisch keine reine Sensorintegration mehr, sondern eine kombinierte:

- Berechnungsintegration
- Wartungsintegration
- Button-Integration
- Bluetooth-/Cloud-Integration
- Lovelace-UI-Erweiterung

Die wichtigste Architekturentscheidung im aktuellen Stand lautet:

- **BLE wird gezielt und manuell gelesen**
- **Cloud bleibt als zyklische Hintergrundquelle aktiv**
- **Frontend, Sensoren und Button teilen sich denselben Coordinator-Zustand**

Damit bleibt die Bedienung für das PoolLab deutlich robuster, ohne auf automatische Cloud-Aktualisierung und die restliche Wartungslogik zu verzichten.
