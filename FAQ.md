# FAQ - Smart Pool Assistant

Zur Uebersicht zurueck: [README.md](README.md)

Weitere Doku:

- [Einrichtung und Konfiguration](docs/SETUP.md)
- [Chemielogik und Lernsystem](docs/CHEMISTRY.md)
- [Lovelace-Karte und Demos](docs/CARD_AND_DEMOS.md)
- [Entitaeten](docs/ENTITIES.md)
- [Technische Dokumentation](TECHNISCHE_DOKUMENTATION.md)

## Warum empfiehlt die Integration ploetzlich sehr viel Chlor?

Die haeufigsten Ursachen sind:

- Das laufend verwendete Poolvolumen passt nicht zur erwarteten Beckengroesse.
- Der persoenliche Chlor-Dosierfaktor hat den effektiven Wirkstoff stark nach unten gezogen.
- Die Messung ist sehr alt oder der Chlorwert ist real bereits fast bei `0 mg/l`.

Pruefe zuerst in den Berechnungsdetails:

- `Berechnetes Volumen`
- `Gelernter Dosierfaktor`
- `Effektiver Wirkstoff`

## Beispiel: 20 g bei nur 0,916 m3

Wenn das Becken nur `0,916 m3` hat, waeren `20 g` bei `56 %` Wirkstoff normalerweise deutlich zu viel. Wenn die Karte gleichzeitig etwa `Dosierfaktor 0,40` und `Effektiver Wirkstoff 0,224` zeigt, ist die hohe Empfehlung meist durch die Lernlogik erklaert.

Ohne Lernfaktor waere die Empfehlung in so einem Fall eher im Bereich um `8 g`. Mit einem effektiven Wirkstoff von nur `0,224` steigt die rechnerische Produktmenge dagegen fast auf `20 g`.

Seit der aktuellen Anpassung wird der persoenliche Dosierfaktor aber erst ab `5` verwertbaren Samples aktiv in die Empfehlung eingerechnet. Davor ist der Wert zwar schon als Diagnose sichtbar, die eigentliche Chlorempfehlung rechnet aber noch nur mit dem konfigurierten Produkt-Wirkstoff.

## Was bedeutet "Dosierfaktor"?

Der Dosierfaktor beschreibt, wie stark bestaetigte Chlorzugaben in der Praxis wirklich im Wasser angekommen sind. `1,00` bedeutet: Die reale Wirkung entspricht ungefaehr dem Hersteller-Wirkstoff. Ein Wert unter `1,00` bedeutet: In der Historie kam rechnerisch weniger an als erwartet.

## Ist bei anorganischem Chlor `1,00` als Wirkstoffanteil richtig?

Nein, in der Regel nicht. `Anorganisch` beschreibt hier zuerst den Chlor-Typ ohne eingebauten Stabilisator, nicht automatisch `100 %` aktives Chlor.

Typische Groessenordnungen:

- organisches Chlor: oft etwa `0.56`
- Calciumhypochlorit: oft etwa `0.65-0.70`
- Natriumhypochlorit: oft etwa `0.12-0.15`

Massgeblich bleibt immer die Produktangabe auf dem Etikett.

## Warum kann der Dosierfaktor zu niedrig werden?

Der haeufigste Grund sind spaete Nachmessungen:

- Du gibst Chlor zu.
- Die Nachmessung erfolgt erst viele Stunden spaeter oder sogar erst am naechsten Tag.
- Bis dahin ist bereits wieder Chlor verbraucht worden.
- Die Lernlogik sieht dann nur noch einen kleinen Restanstieg und lernt eine zu geringe Wirksamkeit.

Seit `v2.2.3` werden fuer den Dosierfaktor deshalb nur noch zeitnahe Messpaare verwendet:

- Vorher-Messung maximal `12 h` vor der Zugabe
- Nachmessung maximal `12 h` nach der Zugabe

Zusaetzlich greift der Faktor jetzt erst ab `5` verwertbaren Samples aktiv in die Chlorempfehlung ein. Das ist fuer kleine Becken und noch duenne Historie deutlich robuster.

## Was ist ein "Sample" beim Dosierfaktor?

Ein Sample ist genau ein verwertbares Zugabe-/Nachmess-Paar fuer die Lernlogik:

- eine frische Vorher-Messung vor der Chlorzugabe
- eine bestaetigte Chlorzugabe
- eine Nachmessung nach der Zugabe
- kein weiterer Chlor-Dosiervorgang dazwischen
- Vorher- und Nachmessung jeweils innerhalb von `12 h`

Nur wenn dieses Paar sauber auswertbar ist, zaehlt es als `1 Sample` fuer den persoenlichen Dosierfaktor.

## Hat die Erfassung von offen/abgedeckt und Nutzung damit direkt zu tun?

Meist nein. Diese Kontextdaten beeinflussen vor allem Verbrauch, Prognose und Stabilitaetsbewertung. Eine massiv zu hohe Chlorempfehlung bei kleinem Becken ist eher ein Thema von:

- Volumen
- Lernfaktor / effektivem Wirkstoff
- sehr niedrigem Ist-Chlor

## Wie funktioniert `Baden in X Stunden`?

Wenn du in der Karte einen Badezeitpunkt setzt, berechnet die Integration die Vor-Baden-Menge nicht mehr nur fuer den aktuellen Moment.

- `chlor_pre` wird dann auf den geplanten Badezeitpunkt ausgerichtet.
- Dazu wird der erwartete Chlorverlust bis dahin abgeschaetzt.
- Ohne gesetzte Zeit bleibt die Hauptlogik wie bisher auf die Nach-Nutzungs-Dosierung ausgelegt.

Das ist vor allem fuer Werktage praktisch, wenn zwischen Messung und Baden mehrere Stunden liegen.

## Wann ist eine Nachmessung fuer den Dosierfaktor sinnvoll?

Am besten:

- moeglichst mit frischer Vorher-Messung
- nach ausreichender Umwaelzung und Einwirkzeit
- aber nicht erst sehr spaet oder am naechsten Tag

Praktisch ist ein Zeitfenster von wenigen Stunden deutlich besser als eine sehr spaete Kontrolle.

Wichtig ist die Trennung:

- Verbrauch lernen: `Messung -> Messung` mindestens `3 h`
- Dosierwirkung lernen: `Messung -> Zugabe -> Nachmessung` mit eigener Logik, dort gilt aktuell `0.5 h` bis `12 h` nach der Zugabe

## Wie erkenne ich, dass die Lernphase noch unsicher ist?

Typische Hinweise in der Karte:

- `Lernphase`
- wenige Intervalle oder wenige Samples
- noch keine oder nur schwache Prognose

Beim Dosierfaktor gilt die Lernphase jetzt bis mindestens `5` verwertbare Samples erreicht sind.

In dieser Phase sollten hohe Abweichungen immer mit gesundem Menschenverstand gegen Beckenvolumen, Produkt und frische Messung gegengeprueft werden.
