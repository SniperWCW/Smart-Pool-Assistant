# FAQ - Smart Pool Assistant

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

Wenn das Becken nur `0,916 m³` hat, waeren `20 g` bei `56 %` Wirkstoff normalerweise deutlich zu viel. Wenn die Karte gleichzeitig etwa `Dosierfaktor 0,40` und `Effektiver Wirkstoff 0,224` zeigt, ist die hohe Empfehlung meist durch die Lernlogik erklaert.

Ohne Lernfaktor waere die Empfehlung in so einem Fall eher im Bereich um `8 g`. Mit einem effektiven Wirkstoff von nur `0,224` steigt die rechnerische Produktmenge dagegen fast auf `20 g`.

## Was bedeutet "Dosierfaktor"?

Der Dosierfaktor beschreibt, wie stark bestaetigte Chlorzugaben in der Praxis wirklich im Wasser angekommen sind. `1,00` bedeutet: Die reale Wirkung entspricht ungefaehr dem Hersteller-Wirkstoff. Ein Wert unter `1,00` bedeutet: In der Historie kam rechnerisch weniger an als erwartet.

## Warum kann der Dosierfaktor zu niedrig werden?

Der haeufigste Grund sind späte Nachmessungen:

- Du gibst Chlor zu.
- Die Nachmessung erfolgt erst viele Stunden spaeter oder sogar erst am naechsten Tag.
- Bis dahin ist bereits wieder Chlor verbraucht worden.
- Die Lernlogik sieht dann nur noch einen kleinen Restanstieg und lernt eine zu geringe Wirksamkeit.

Seit `v2.2.3` werden fuer den Dosierfaktor deshalb nur noch zeitnahe Messpaare verwendet:

- Vorher-Messung maximal `12 h` vor der Zugabe
- Nachmessung maximal `12 h` nach der Zugabe

## Hat die Erfassung von offen/abgedeckt und Nutzung damit direkt zu tun?

Meist nein. Diese Kontextdaten beeinflussen vor allem Verbrauch, Prognose und Stabilitaetsbewertung. Eine massiv zu hohe Chlorempfehlung bei kleinem Becken ist eher ein Thema von:

- Volumen
- Lernfaktor / effektivem Wirkstoff
- sehr niedrigem Ist-Chlor

## Wann ist eine Nachmessung fuer den Dosierfaktor sinnvoll?

Am besten:

- moeglichst mit frischer Vorher-Messung
- nach ausreichender Umwaelzung und Einwirkzeit
- aber nicht erst sehr spaet oder am naechsten Tag

Praktisch ist ein Zeitfenster von wenigen Stunden deutlich besser als eine sehr späte Kontrolle.

## Wie erkenne ich, dass die Lernphase noch unsicher ist?

Typische Hinweise in der Karte:

- `Lernphase`
- wenige Intervalle oder wenige Samples
- noch keine oder nur schwache Prognose

In dieser Phase sollten hohe Abweichungen immer mit gesundem Menschenverstand gegen Beckenvolumen, Produkt und frische Messung gegengeprueft werden.
