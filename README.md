# Smart Pool Assistant 💧

Der **Smart Pool Assistant** ist eine Home Assistant Integration, die dir dabei hilft, die Wasserqualität deines Pools oder Whirlpools perfekt im Griff zu behalten. Basierend auf deinen aktuellen Messwerten für Chlor und pH-Wert berechnet die Integration präzise Dosierempfehlungen.

## Funktionen

- **Präzise Chlor-Berechnung**: Berücksichtigt Stoßchlorungs-Faktoren bei niedrigen Werten und berechnet die Menge basierend auf dem Wirkstoffanteil deines Granulats.
- **pH-Regulierung**: Berechnet die benötigte Menge an pH-Senker (ml) oder pH-Heber (g).
- **Bade-Logik**: Gibt spezifische Empfehlungen für die Dosierung vor und nach dem Baden.
- **Integrierte Frontend-Karte**: Eine spezialisierte Lovelace-Karte zur übersichtlichen Darstellung der Werte.

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
- **Dosierung pH-Senker**: Die Menge an pH-Senker (in ml), die benötigt wird, um den pH-Wert in 10 m³ Wasser um 0,2 Einheiten zu senken (z.B. 200 für 200ml/10m³/0.2pH).
- **Dosierung pH-Heber**: Die Menge an pH-Heber (in g), die benötigt wird, um den pH-Wert in 10 m³ Wasser um 0,1 Einheiten zu heben (z.B. 100 für 100g/10m³/0.1pH).

## Die Berechnungslogik

### Chlor
Die Integration nutzt einen dynamischen **Shock-Faktor**:
- Bei Chlor < 0.1 mg/l wird die 3-fache Menge empfohlen.
- Bei Chlor < 0.6 mg/l wird die 1.8-fache Menge empfohlen.
Zusätzlich wird eine **Mindestdosis** sichergestellt, damit die Desinfektion wirksam bleibt.

### pH-Wert
Basierend auf der Differenz zum Zielwert, dem Poolvolumen und den von dir angegebenen Dosierangaben des Herstellers (z.B. "200 ml / 10 m³ für -0,2 pH") wird die exakte Menge an pH-Senker oder pH-Heber ermittelt. Dies gewährleistet eine präzise Anpassung an dein spezifisches Produkt.

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
- `sensor.pool_ph_senker`: Benötigte Menge pH-Senker in ml.
- `sensor.pool_ph_erhoher`: Benötigte Menge pH-Heber in g.
- `sensor.pool_empfehlung`: Textuelle Zusammenfassung der nächsten Schritte.
