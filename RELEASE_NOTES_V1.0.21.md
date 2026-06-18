# Release Notes V1.0.21

## Highlights

- Wettervorhersage fuer heute und morgen direkt in der Pool-Karte.
- Optionale Wetter-Entitaet jetzt auch in der Integration selbst konfigurierbar.
- UV kann den Chlorbedarf jetzt fachlich konservativ leicht erhoehen.
- Regen fuehrt zunaechst nur zu einem Nachmess-Hinweis, nicht zu aggressiver Zusatzdosierung.

## Details

### Wetteranzeige

- Die Lovelace-Karte kann Daten aus einer Home-Assistant-`weather`-Entitaet anzeigen.
- Vorgesehen sind vor allem `UV`, `Regen` und `Wind` fuer heute und morgen.
- Die Karte liest die Forecast-Daten generisch aus dem `forecast`-Attribut.

### Wetter in der Berechnung

- In Config Flow und Options Flow kann jetzt optional eine `weather`-Entitaet hinterlegt werden.
- Der Coordinator liest daraus die Tagesvorhersage fuer heute.
- Bei `uv_index >= 6` wird ein kleiner Zuschlag angesetzt.
- Bei `uv_index >= 8` wird ein etwas hoeherer Zuschlag angesetzt.
- Die Breakdown-Anzeige weist diesen Einfluss als `UV-Zuschlag` separat aus.

### Regenlogik

- Erwarteter starker Regen fuehrt noch nicht direkt zu einer erhoehten Chlor-Dosierung.
- Stattdessen wird ein Hinweis ausgegeben, danach moeglichst erneut zu messen.
- Damit bleibt die Logik fachlich vorsichtig und vermeidet Ueberreaktionen auf unsichere Vorhersagen.

### Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `manifest.json` und die Release-Dateien wurden auf `1.0.21` angehoben.
