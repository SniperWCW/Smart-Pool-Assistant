# Release Notes - v0.0.1.5 🛠️

*   **NEU:** Re-Konfiguration möglich! Entitäten und Einstellungen können nun über "Konfigurieren" geändert werden.
*   **NEU:** Unterstützung für `persistent_notification` (konfigurierbar).
*   **Frontend:** Neuer Bereich "Letzte Aktivitäten" zeigt die letzte Dosierung direkt auf der Karte an.
*   **Stabilität:** Fehlerbehandlung bei der Registrierung statischer Pfade verbessert.

# Release Notes - v0.0.1.4💧

Wir freuen uns, die erste Version des **Smart Pool Assistant** vorstellen zu dürfen! Diese Integration verwandelt Home Assistant in einen intelligenten Pool-Manager, der nicht nur Werte anzeigt, sondern aktiv bei der Wasserpflege unterstützt.

### 🚀 Hauptfunktionen

*   **Präzise Dosierberechnung**: 
    *   Berechnung der benötigten Chlormenge unter Berücksichtigung eines dynamischen Stoßchlorungs-Faktors (bei niedrigen Werten wird automatisch eine höhere Dosis empfohlen).
    *   Exakte Berechnung für **PH-Plus (Granulat)** und **PH-Minus (Flüssig)** basierend auf individuellen Herstellerangaben (einstellbar in ml/g pro 10m³).
*   **Interaktive Dashboard-Karte**:
    *   Eigene `pool-chemistry-card` zur Visualisierung der Ist- und Zielwerte.
    *   Direkte Eingabefelder auf der Karte, um die Zugabe von Chemie zu loggen.
*   **Wartungshistorie**:
    *   Die Integration speichert den Zeitstempel und die Menge der letzten Chemie-Zugaben dauerhaft (auch nach Neustarts).
*   **Benachrichtigungssystem & Reminder**:
    *   Konfigurierbarer Benachrichtigungs-Dienst für Bestätigungen.
    *   Automatischer "Follow-up"-Reminder: Erhalte nach einer einstellbaren Zeit (z. B. 60 Min) eine Nachricht, um die Werte nach der Einwirkzeit erneut zu prüfen.
*   **Echtzeit-Aktualisierung**:
    *   Die Integration überwacht deine Sensoren und berechnet die Empfehlungen sofort neu, sobald sich Chlor-, pH- oder Temperaturwerte ändern.

### 🛠 Installation & Einrichtung

1.  Füge dieses Repository als **Benutzerdefiniertes Repository** in HACS hinzu.
2.  Installiere "Smart Pool Assistant" und starte Home Assistant neu.
3.  Gehe zu **Einstellungen > Geräte & Dienste** und füge die Integration hinzu.
4.  Gib deine Sensoren und die Dosieranweisungen deiner Poolchemie an.

### 📋 Voraussetzungen

*   Home Assistant 2025.1.0 oder neuer.
*   Vorhandene Sensoren für Chlor (mg/l), pH-Wert und Wassertemperatur.

---
*Ein großes Dankeschön an alle, die bei der Entwicklung und dem Testen der ersten Logik-Entwürfe geholfen haben!*