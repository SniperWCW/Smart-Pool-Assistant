# Release Notes V1.0.21

## Highlights

- Wettervorhersage für heute und morgen direkt in der Pool-Karte.
- Optionale Wetter-Entität jetzt auch in der Integration selbst konfigurierbar.
- UV kann den Chlorbedarf jetzt fachlich konservativ leicht erhöhen.
- Regen führt zunächst nur zu einem Nachmess-Hinweis, nicht zu aggressiver Zusatzdosierung.

## Details

### Wetteranzeige

- Die Lovelace-Karte kann Daten aus einer Home-Assistant-`weather`-Entität anzeigen.
- Vorgesehen sind vor allem `UV`, `Regen` und `Wind` für heute und morgen.
- Die Karte liest die Forecast-Daten generisch aus dem `forecast`-Attribut.

### Wetter in der Berechnung

- In Config Flow und Options Flow kann jetzt optional eine `weather`-Entität hinterlegt werden.
- Der Coordinator liest daraus die Tagesvorhersage für heute.
- Bei `uv_index >= 6` wird ein kleiner Zuschlag angesetzt.
- Bei `uv_index >= 8` wird ein etwas höherer Zuschlag angesetzt.
- Die Breakdown-Anzeige weist diesen Einfluss als `UV-Zuschlag` separat aus.

### Regenlogik

- Erwarteter starker Regen führt noch nicht direkt zu einer erhöhten Chlor-Dosierung.
- Stattdessen wird ein Hinweis ausgegeben, danach möglichst erneut zu messen.
- Damit bleibt die Logik fachlich vorsichtig und vermeidet Überreaktionen auf unsichere Vorhersagen.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.0.21` angehoben.
