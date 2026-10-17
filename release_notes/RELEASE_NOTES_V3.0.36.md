# Release Notes V3.0.36

## Stabilität und Performance

- BLE-Abruf liest nur noch die neuesten 6 Messblöcke und stoppt früh, sobald alle relevanten Werte vorliegen.
- Doppelte Lernwerte durch wiederholte BLE-Abrufe werden vermieden (persistenter Geräteuhr-Offset). Einmalig kann sich die Zuordnung der Zeitstempel verschieben.
- Cloud-Abruf, Benachrichtigungen und Abbruch-Handling sind robuster; Speichern wird gebündelt.

## Struktur

- Alle Entitäten gehören zu einem Gerät „Smart Pool Assistant“.
- Services und Config-Flow validieren Eingaben, neue englische Übersetzung.
- Wettervorhersage wird zwischengespeichert, große Attribute werden nicht aufgezeichnet.
