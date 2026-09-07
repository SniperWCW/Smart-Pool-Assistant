# Release Notes V3.0.34

## LayzSpa-Fehlerüberwachung

- Die Lovelace-Karte kann jetzt einen optionalen LayzSpa-Fehlercode-Sensor konfigurieren, zum Beispiel `sensor.layzspa_error`.
- Bei Fehlercode `0` zeigt die Karte keine Meldung.
- Für E02 erklärt die Karte die Durchflussstörung und empfiehlt Filter- sowie Einlassprüfung.
- Für E04 und E08 beschreibt sie die Temperaturursache und die Schritte zum Abkühlen, Schattieren und Zurücksetzen.
- Andere Nicht-Null-Fehlercodes bleiben als unbekannter Fehler sichtbar.
