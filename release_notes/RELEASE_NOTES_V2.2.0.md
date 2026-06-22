# Release Notes V2.2.0

## Chemie-Lernen

- Bestätigte Chlorzugaben und passende Nachmessungen werden jetzt als eigene Lernstrecke ausgewertet.
- Daraus entsteht ein persönlicher `Chlor-Dosierfaktor`, der die reale Wirksamkeit des verwendeten Produkts besser abbildet als nur der Hersteller-Wirkstoffanteil.
- Ab mindestens zwei verwertbaren Zugabe-/Nachmess-Paaren fließt dieser Faktor direkt in die Chlorempfehlung ein.

## Chlor-Prognose

- Neue Chlor-Prognose für den erwarteten Tagesverlust sowie die Zeit bis zur Zieluntergrenze oder bis `0,6 mg/l`.
- Die Prognose gewichtet vorhandene Lernintervalle nach Temperatur, Abdeckung, Nutzungsmodus, UV/Regen und optionaler Pumpenlaufzeit.
- Zusätzlich werden Konfidenz, Prognosebasis und Detailattribute an den Empfehlungssensor durchgereicht.

## Frontend

- Die Lovelace-Karte zeigt die aktuelle Chlor-Prognose jetzt direkt im Chlor-Empfehlungsblock.
- Die einklappbare Stabilitätssektion wurde um Dosierfaktor, effektiven Wirkstoffanteil, Prognosehorizont, Konfidenz und Prognosebasis erweitert.
- Neue Sensorwerte für Dosierqualität und Prognose stehen ebenfalls zur Verfügung.

## Konfiguration / Dokumentation

- Neue optionale Config-Option `pump_entity` für `switch.*` oder `binary_sensor.*`, damit die Lernlogik Pumpenlaufzeit berücksichtigen kann.
- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json` und diese Release Notes wurden auf `2.2.0` aktualisiert.
