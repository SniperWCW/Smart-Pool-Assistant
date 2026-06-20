# Release Notes V2.0.4

## Highlights

- Chlor und pH koennen jetzt als Zielbereich statt als fixer Einzelzielwert konfiguriert werden.
- Berechnung, Empfehlung, Badeampel und Lovelace-Karte bewerten die Werte durchgaengig gegen diese Bereiche.

## Details

### Zielbereiche

- Config Flow und Options Flow verwenden jetzt:
  - `chlor_min` / `chlor_max`
  - `ph_min` / `ph_max`
- Bestehende Installationen mit `chlor_target` und `ph_target` bleiben kompatibel. Die alten Einzelzielwerte werden als Fallback fuer Minimum und Maximum genutzt.
- Ungueltige Bereiche werden im Flow abgefangen, wenn Minimum groesser als Maximum ist.

### Berechnung

- Innerhalb des Zielbereichs wird keine Chemie empfohlen.
- Chlor wird bei Unterschreitung konservativ zur unteren Zielgrenze nachdosiert.
- pH wird bei Unterschreitung zur unteren Zielgrenze angehoben.
- pH wird bei Ueberschreitung zur oberen Zielgrenze gesenkt.
- Stoßchlor-, Wetter-, Temperatur-, Abdeckungs-, Nutzungs- und Messloeffel-Logik bleiben erhalten.

### Lovelace-Karte

- Die Zielspalte zeigt Bereiche wie `1-2 mg/l` oder `7,2-7,4`.
- Farblogik, Badeampel und Status-Texte bewerten Chlor und pH gegen den konfigurierten Zielbereich.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.0.4` aktualisiert.
