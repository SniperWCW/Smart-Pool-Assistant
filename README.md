# Smart Pool Assistant 💧

Der **Smart Pool Assistant** ist eine Home Assistant Integration, die dir dabei hilft, die Wasserqualität deines Pools oder Whirlpools perfekt im Griff zu behalten. Basierend auf deinen aktuellen Messwerten für Chlor und pH-Wert berechnet die Integration präzise Dosierempfehlungen.

## Funktionen

- **Präzise Chlor-Berechnung**: Berücksichtigt Stoßchlorungs-Faktoren bei niedrigen Werten und berechnet die Menge basierend auf dem Wirkstoffanteil deines Granulats.
- **pH-Regulierung**: Berechnet die benötigte Menge an **PH-Minus** (ml) oder **PH-Plus** (g) basierend auf deinen Herstellerangaben.
- **Bade-Logik**: Gibt spezifische Empfehlungen für die Dosierung vor und nach dem Baden.
- **Flexible Datenquellen**: Unterstützt Bluetooth (PoolLab), PoolLab Cloud API und manuelle Home Assistant Sensoren, mit intelligenter Priorisierung.
- **Transparente Datenquelle**: Die Frontend-Karte zeigt an, ob die Daten von Bluetooth, der Cloud API oder manuellen Sensoren stammen.
- **Interaktive Log-Funktion**: Erfasse zugegebene Mengen direkt über die Karte inklusive Zeitstempel-Historie.
- **Benachrichtigungssystem**: Sofortige Bestätigung bei Chemie-Zugabe und automatische Erinnerung zur Nachmessung nach einer definierten Zeit.
- **Persistente Messzeiten**: Der Zeitstempel der letzten Messung bleibt auch nach einem Home Assistant Neustart erhalten.
- **Integrierte Frontend-Karte**: Spezialisierte Lovelace-Karte mit direkten Eingabefeldern.

* **Re-Konfiguration** Re-Konfiguration möglich! Entitäten und Einstellungen können nun über "Konfigurieren" geändert werden.
* **Persistent Notification:** Unterstützung für `persistent_notification` (konfigurierbar).
* **Frontend:** Neuer Bereich "Letzte Aktivitäten" zeigt die letzte Dosierung direkt auf der Karte an.

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

Der Konfigurationsprozess ist nun mehrstufig:

1.  **Datenquelle auswählen**: Wähle, ob du Bluetooth (PoolLab), die PoolLab Cloud API oder manuelle Home Assistant Sensoren verwenden möchtest.
2.  **Hardware & API Setup**:
    *   **Bluetooth**: Wenn ausgewählt, werden verfügbare PoolLab-Geräte automatisch gescannt und zur Auswahl angeboten.
    *   **Cloud API**: Gib deinen PoolLab Cloud API Key ein.
    *   **Manuelle Sensoren**: Wähle deine Home Assistant Entitäten für Chlor, pH und Temperatur.
3.  **Pool & Benachrichtigung**:
    *   **Poolvolumen**: Wassermenge in m³ (z.B. 0.96 für einen kleinen Whirlpool).
    *   **Zielwerte**: Deine gewünschten Idealwerte für Chlor und pH.
    *   **Wirkstoffanteil**: Der Anteil des Wirkstoffs in deinem Chlor-Produkt (Standard: 0.56 für 56%iges Granulat).
    *   **Dosierung PH-Minus**: Menge in ml, um 10 m³ Wasser um 0,2 Einheiten zu senken (z.B. 200 ml).
    *   **Dosierung PH-Plus**: Menge in g, um 10 m³ Wasser um 0,1 Einheiten zu heben (z.B. 100 g).
    *   **Benachrichtigungs-Dienst**: Wähle aus deinen vorhandenen Home Assistant `notify`-Diensten.
    *   **Persistente Benachrichtigung**: Optionale Anzeige einer Benachrichtigung in der Home Assistant Sidebar.
    *   **Erinnerung**: Zeitspanne in Minuten, nach der eine Aufforderung zur Nachmessung gesendet wird.

## Die Berechnungslogik

### Chlor
Die Integration nutzt einen dynamischen **Shock-Faktor**:
- Bei Chlor < 0.1 mg/l wird die 3-fache Menge empfohlen.
- Bei Chlor < 0.6 mg/l wird die 1.8-fache Menge empfohlen.
Zusätzlich wird eine **Mindestdosis** sichergestellt, damit die Desinfektion wirksam bleibt.

### pH-Wert
Basierend auf der Differenz zum Zielwert, dem Poolvolumen und den Herstellerangaben wird die exakte Menge an **PH-Plus** oder **PH-Minus** ermittelt. Dies gewährleistet eine präzise Anpassung an dein spezifisches Produkt.

## Frontend: Pool Chemistry Card

Die Integration registriert automatisch eine Custom Card. Du kannst sie manuell zu deinem Dashboard hinzufügen:

```yaml
type: custom:pool-chemistry-card
chlor_entity: sensor.pool_chlor_nachdosierung
ph_entity: sensor.pool_ph_senker
recommendation_entity: sensor.pool_empfehlung
```

## Sensoren

Die Integration stellt folgende Sensoren bereit:
- `sensor.pool_chlor_nachdosierung`: Gesamtmenge Chlor in Gramm.
- `sensor.pool_chlor_vor_baden`: Empfohlene Menge direkt vor dem Baden.
- `sensor.pool_ph_minus`: Benötigte Menge PH-Minus in ml.
- `sensor.pool_ph_plus`: Benötigte Menge PH-Plus in g.
- `sensor.pool_empfehlung`: Textuelle Zusammenfassung der nächsten Schritte.
