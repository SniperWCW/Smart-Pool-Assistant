# Release Notes V3.0.2

## PoolLab BLE

- Der Abruf des letzten gespeicherten PoolLab-Messblocks wurde robuster gemacht.
- Wenn ein `GET_MEASURES`-Block leer wirkt, wird derselbe Block einmal mit alternativer `cell_id`-Byte-Reihenfolge erneut gelesen.
- Leere Phantomdatensätze (`type=0`, `timestamp=0`, `value=0.0`) werden verworfen.

## Quellenpriorisierung

- Chlor, pH und Temperatur werden jetzt pro Messwert nach dem neuesten Zeitstempel aus Bluetooth, Cloud oder manuellen Sensoren ausgewählt.
- Dadurch bleibt kein älterer Bluetooth-Wert mehr stehen, wenn bereits ein neuerer Wert aus einer anderen Quelle vorliegt.
