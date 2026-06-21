# Release Notes V2.0.1

## Highlights

- Neue Badeampel in der Lovelace-Karte: `Baden empfohlen`, `Baden möglich` oder `Nicht empfohlen`.
- Übersichtlichere Messwertetabelle mit getrennten Spalten für `Messwert`, `Ist`, `Ziel` und `Quelle`.
- Bereinigter Karten-Editor: Wetter-Entität, Empfehlungs-Hauptsensor und PoolLab-Abruf-Button sind dort nicht mehr editierbar.

## Details

### Frontend

- Die Badeampel bewertet die vorhandenen Empfehlungssensor-Attribute konservativ:
  - Rot bei fehlenden aktuellen Kernwerten, Speicherwerten, Nachmess-Zustand, Stoßchlor, deutlichen Chlor-/pH-Abweichungen, sehr hoher Temperatur oder unsicherem Wetter.
  - Gelb bei moderaten Chemieabweichungen, warmem Wasser, Regen-/Windhinweisen oder hoher UV-Belastung.
  - Grün, wenn keine Warn- oder Sperrgründe vorliegen.
- Die Messwertetabelle zeigt Chlor, pH und Temperatur klarer getrennt nach Istwert, Zielwert und Quelle.
- Passende Messzeitpunkte werden in der Quellen-Spalte angezeigt.
- PoolLab-Abrufstatus und Bluetooth-Status nutzen die zusätzliche Tabellenspalte für kompaktere Statusdetails.

### Karten-Editor

- Der visuelle Karten-Editor bietet nur noch die optionalen LayZSpa-Felder an.
- Wetter-Entität und UV-Sensor bleiben Aufgabe des Config Flow / Options Flow.
- Empfehlungssensor und PoolLab-Abruf-Button werden von der Karte fest bzw. automatisch verwendet.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Banner und diese Release Notes wurden auf `2.0.1` aktualisiert.
