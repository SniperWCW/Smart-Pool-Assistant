# Smart Pool Assistant 💧

Der **Smart Pool Assistant** ist eine leistungsstarke Home Assistant Integration, die dich bei der Wasserpflege deines Pools oder Whirlpools unterstützt. Basierend auf aktuellen Messwerten liefert sie präzise Dosierempfehlungen und verwaltet die Wartungshistorie.

## Hauptfunktionen

- **Präzise Chlor-Berechnung**: Berücksichtigt Stoßchlorungs-Faktoren, eine **Temperatur-Korrektur** sowie den **Abdeckungs-Status** und die **Badelast** (Nutzungsmodus).
- **pH-Regulierung**: Berechnet die benötigte Menge an **PH-Minus** (ml) oder **PH-Plus** (g).
- **Bade-Logik**: Gibt spezifische Empfehlungen für die Dosierung vor und nach dem Baden.
- **Interaktive Log-Funktion**: Erfasse zugegebene Mengen direkt über die Karte inklusive Zeitstempel-Historie.
- **Benachrichtigungssystem**: 
  - Auswahl des Dienstes via Dropdown.
  - Bestätigung bei Chemie-Zugabe und automatische Erinnerung zur Nachmessung (Follow-up).
- **Filter-Wartung**: Verfolge Reinigungs- und Wechselintervalle des Filters.
  - **Ampellogik**: Visuelle Anzeige (grün, gelb, rot) der Fälligkeit.
  - **Benachrichtigungen**: Automatische Meldungen bei Erreichen der Schwellenwerte.
- **Integrierte Frontend-Karte**: Spezialisierte Lovelace-Karte mit direkten Eingabefeldern.
- **Maximale Datensicherheit**: Nutzt die Home Assistant Storage-API. Alle Zeitstempel und Historien bleiben nach einem Neustart oder Update erhalten.
- **Re-Konfiguration möglich!** Entitäten und Einstellungen können nun über "Konfigurieren" geändert werden.
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
- **Reinigungsintervall**: Wie oft der Filter gereinigt werden soll (Standard: 30 Tage).
- **Wechselintervall**: Wie oft der Filter ersetzt werden soll (Standard: 180 Tage).
- **Gelb-Schwelle**: Tage **vor** Ablauf des Intervalls, ab denen die Warnung (Gelb) erscheint.
- **Rot-Schwelle**: Tage **nach** Ablauf des Intervalls (Überfälligkeit), ab denen der Status auf Kritisch (Rot) springt.

## Die Berechnungslogik

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

Zusätzlich wird eine **Mindestdosis** sichergestellt, damit die Desinfektion wirksam bleibt.

### pH-Wert
Basierend auf der Differenz zum Zielwert, dem Poolvolumen und den Herstellerangaben wird die exakte Menge an **PH-Plus** oder **PH-Minus** ermittelt. Dies gewährleistet eine präzise Anpassung an dein spezifisches Produkt.

## Frontend: Pool Chemistry Card

Die Integration registriert automatisch eine Custom Card. Du kannst sie manuell zu deinem Dashboard hinzufügen:

```yaml
type: custom:pool-chemistry-card
recommendation_entity: sensor.pool_empfehlung
```

## Sensoren

Die Integration stellt folgende Sensoren bereit:
- `sensor.pool_chlor_nachdosierung`: Gesamtmenge Chlor in Gramm.
- `sensor.pool_chlor_vor_baden`: Empfohlene Menge direkt vor dem Baden.
- `sensor.pool_ph_minus`: Benötigte Menge PH-Minus in ml.
- `sensor.pool_ph_plus`: Benötigte Menge PH-Plus in g.
- `sensor.pool_empfehlung`: Textuelle Zusammenfassung der nächsten Schritte.
- `sensor.pool_filter_reinigung_fällig`: Tage seit letzter Filterreinigung.
- `sensor.pool_filter_wechsel_fällig`: Tage seit letztem Filterwechsel.
