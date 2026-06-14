# Smart Pool Assistant 💧

Der **Smart Pool Assistant** ist eine leistungsstarke Home Assistant Integration, die dich bei der Wasserpflege deines Pools oder Whirlpools unterstützt. Basierend auf aktuellen Messwerten liefert sie präzise Dosierempfehlungen und verwaltet die Wartungshistorie.

## Hauptfunktionen

- **Präzise Chlor-Berechnung**: Berücksichtigt Stoßchlorungs-Faktoren, eine **Temperatur-Korrektur** sowie den **Abdeckungs-Status** und die **Badelast** (Nutzungsmodus).
- **Transparente Berechnung**: Aufschlüsselung der Dosierempfehlung (Basis, Temperatur, UV, Badelast) direkt in der UI.
- **pH-Regulierung**: Berechnet die benötigte Menge an **PH-Minus** (ml) oder **PH-Plus** (g).
- **Sicherheits-Logik**: Erkennt automatisch, wenn Werte bereits über dem Zielwert liegen und stoppt die Empfehlung (keine Überdosierung).
- **Intelligente Status-Warnungen**: Visuelle Warnung (Rot) im Frontend und in der Entität, wenn der Chlorwert signifikant zu hoch ist.
- **Zentralisierte Logik**: Die Empfehlungs-Entität (`sensor.pool_empfehlung`) nutzt dieselbe Logik wie das Frontend für konsistente Anzeigen in Automationen.
- **Whirlpool-Steuerung (LayZSpa)**:
  - Vollständige Integration von **Pumpe, Heizung und Luftsprudler**.
  - Echtzeit-Anzeige der **Ist- und Zieltemperatur**.
  - Überwachung der **Verbindungsqualität (RSSI)** mit farblicher Ampellogik.
  - Anzeige der IP-Adresse und des Online-Status.
  - Platzsparende, **einklappbare Sektion** in der Frontend-Karte.
- **Bade-Logik**: Gibt spezifische Empfehlungen für die Dosierung vor und nach dem Baden.
- **Präzise Zeitstempel**: Intelligente Unterscheidung zwischen Cloud-Messwerten (API) und manuellen Messungen (Sensoren). Zeitstempel bleiben auch nach Neustarts korrekt erhalten.
- **Benachrichtigungssystem**:
  - Auswahl des Dienstes via Dropdown.
  - Bestätigung bei Chemie-Zugabe und automatische Erinnerung zur Nachmessung (Follow-up).
- **Filter-Wartung**: Verfolge Reinigungs- und Wechselintervalle des Filters.
  - **Ampellogik**: Visuelle Anzeige (grün, gelb, rot) der Fälligkeit.
  - **Benachrichtigungen**: Automatische Meldungen bei Erreichen der Schwellenwerte.
- **Integrierte Frontend-Karte**: Spezialisierte Lovelace-Karte mit direkten Eingabefeldern.
- **Dynamisches UI-Layout**: Intelligente Anordnung der Info-Boxen (Letzte Aktivität & Cloud-API) nebeneinander auf großen Bildschirmen.
- **Visuelle Messwerte**: Farbliche Kennzeichnung (Grün/Gelb/Rot) basierend auf Abweichungen zum Zielwert.
- **Erweiterte Status-Logik**: Intelligente Hinweise (z.B. "pH-Wert zuerst anpassen"), um die Wirksamkeit der Chemie zu maximieren.
- **Kompaktes Design**: Einklappbare Bereiche für Berechnungsdetails und Cloud-Messwerte.
- **Re-Konfiguration möglich!** Entitäten und Einstellungen können nun über "Konfigurieren" geändert werden.
- **Langzeitstatistiken**: Unterstützung für native Statistiken (pH, Chlor, Temperatur), um Verläufe über Monate hinweg zu verfolgen.
- **Unterstützung für `persistent_notification` (konfigurierbar).**
- **Letzte Aktivitäten**: Zeigt die letzte durchgeführte Aktion (z.B. "Chlor zugegeben" oder "Filter gereinigt") direkt auf der Karte an.

## Installation

### Über HACS (Empfohlen)
1. Öffne **HACS** in deinem Home Assistant.
2. Klicke auf die drei Punkte oben rechts und wähle **Benutzerdefinierte Repositories**.
3. Füge die URL deines GitHub-Repositories hinzu und wähle als Typ `Integration`.
4. Suche nach "Smart Pool Assistant" und installiere die Integration.
5. Starte Home Assistant neu.

### Manuell
1. Kopiere den Ordner `custom_components/smart_pool_assistant` in deinen `custom_components` Ordner.
2. Starte Home Assistant neu.

## Konfiguration

Gehe zu **Einstellungen > Geräte & Dienste > Integration hinzufügen** und suche nach **Smart Pool Assistant**.

Du wirst nach folgenden Informationen gefragt:
- **Sensoren**: Entitäten für Chlor (mg/l), pH-Wert und Temperatur.
- **Poolvolumen**: Wassermenge in m³ (z.B. 0.96 für einen kleinen Whirlpool).
- **Zielwerte**: Deine gewünschten Idealwerte für Chlor und pH.
- **Wirkstoffanteil**: Der Anteil des Wirkstoffs in deinem Chlor-Produkt (Standard: 0.56 für 56%iges Granulat).
- **Dosierung PH-Minus**: Menge in ml, um 10 m³ Wasser um 0,2 Einheiten zu senken (z.B. 200 ml).
- **Dosierung PH-Plus**: Menge in g, um 10 m³ Wasser um 0,1 Einheiten zu heben (z.B. 100 g).
- **Benachrichtigungs-Dienst**: Der zu verwendende Dienst (z.B. `notify.mobile_app_iphone`).
- **Erinnerung**: Zeitspanne in Minuten, nach der eine Aufforderung zur Nachmessung gesendet wird.

### Filter-Wartung Einstellungen
- **Reinigungsintervall**: Wie oft der Filter gereinigt werden soll (Standard: 24 Stunden).
- **Wechselintervall**: Wie oft der Filter ersetzt werden soll (Standard: 180 Tage).
- **Gelb-Schwelle**: Stunden (Reinigung) bzw. Tage (Wechsel) **vor** Ablauf des Intervalls für die Warnanzeige.
- **Rot-Schwelle**: Stunden (Reinigung) bzw. Tage (Wechsel) **nach** Ablauf des Intervalls für den kritischen Status.

## Die Berechnungslogik

Wichtig: Die Integration empfiehlt bei Abweichungen im pH-Wert immer, diesen **zuerst** zu korrigieren, da Chlor außerhalb des idealen pH-Bereichs (7.0 - 7.4) seine Wirkung nicht voll entfalten kann.

### Chlor
Die Chlormenge wird durch eine Kombination verschiedener Faktoren ermittelt:

1. **Dynamischer Shock-Faktor**:
- Bei Chlor < 0.1 mg/l: 3.0x Menge
- Bei Chlor < 0.6 mg/l: 1.8x Menge

2. **Temperatur-Korrektur**:
- Ab 28°C Wassertemperatur: +20% Chlorbedarf.
- Ab 32°C Wassertemperatur: +50% Chlorbedarf.

3. **Umgebungs-Faktor (Abdeckung)**:
- **Abgedeckt**: Reduziert den Bedarf um 20% (geringerer UV-Verlust).
- **Offen**: Erhöht den Bedarf um 20% (hohe UV-Zehrung).

4. **Badelast (Nutzungsmodus)**:
- **Normal**: +3g Chlor-Zuschlag.
- **Party**: +8g Chlor-Zuschlag.
5. **Zielwert-Check**: Sobald der Ist-Wert den Zielwert erreicht oder überschreitet, wird die Empfehlung sofort auf **0g** gesetzt, um eine Überdosierung zu verhindern.
6. **Warn-Schwellen**: Abweichungen von > 0.1 pH oder > 0.2 mg/l Chlor triggern spezifische Warnmeldungen ("pH zu hoch", "Chlor zu hoch").

Zusätzlich wird eine **Mindestdosis** sichergestellt, damit die Desinfektion wirksam bleibt.

### pH-Wert
Basierend auf der Differenz zum Zielwert, dem Poolvolumen und den Herstellerangaben wird die exakte Menge an **PH-Plus** oder **PH-Minus** ermittelt. Dies gewährleistet eine präzise Anpassung an dein spezifisches Produkt.

## Frontend: Pool Chemistry Card
Die Integration registriert automatisch eine Custom Card. Du kannst sie manuell zu deinem Dashboard hinzufügen:

<img width="1042" height="818" alt="image" src="https://github.com/user-attachments/assets/49d88901-1857-4d5d-95e4-9d74f7274b4c" />

Menü zur Aktivierung von Pool Steuerungsentitäten
<img width="528" height="687" alt="image" src="https://github.com/user-attachments/assets/00f47680-9cdd-4bbc-8754-3f1a6d013dd8" />

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
```

## Sensoren

Die Integration stellt folgende Sensoren bereit:
- `sensor.pool_chlor_nachdosierung`: Gesamtmenge Chlor in Gramm.
- `sensor.pool_chlor_vor_baden`: Empfohlene Menge direkt vor dem Baden.
- `sensor.pool_ph_minus`: Benötigte Menge PH-Minus in ml.
- `sensor.pool_ph_plus`: Benötigte Menge PH-Plus in g.
- `sensor.pool_empfehlung`: Textuelle Zusammenfassung der nächsten Schritte.
- `sensor.pool_filter_reinigung_fällig`: Stunden seit letzter Filterreinigung.
- `sensor.pool_filter_wechsel_fällig`: Tage seit letztem Filterwechsel.
