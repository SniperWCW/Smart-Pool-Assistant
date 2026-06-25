# Chemielogik und Lernsystem

Navigation:

- [Startseite](../README.md)
- [Setup](SETUP.md)
- [Karte und Demos](CARD_AND_DEMOS.md)
- [Entitaeten](ENTITIES.md)
- [FAQ](../FAQ.md)
- [Technische Dokumentation](../TECHNISCHE_DOKUMENTATION.md)

Diese Seite beschreibt die fachliche Logik hinter Dosierung, Lernsystem und Prognosen. Fuer technische Implementierungsdetails siehe [../TECHNISCHE_DOKUMENTATION.md](../TECHNISCHE_DOKUMENTATION.md).

## Chlorberechnung

Die Chlorempfehlung beruecksichtigt:

1. Basisbedarf aus `untere Zielgrenze - Ist` in `mg/l`, wenn Chlor unter dem Zielbereich liegt.
2. Temperatur-Zuschlag ab `28 C` beziehungsweise `32 C`.
3. Zuschlag fuer offene Abdeckung.
4. Nutzungsmodus `none`, `normal` oder `party`.
5. Stosschlor-Ziele bei sehr niedrigen Chlorwerten.
6. Umrechnung ueber Poolvolumen und Wirkstoffanteil in Gramm Produkt.
7. Zielbereich-Check, damit innerhalb des Bereichs oder bei Ueberdosierung `0 g` empfohlen wird.

### Stossziel

Das Stossziel ist stufenweise definiert:

- Chlor `< 0,1 mg/l` -> Ziel `5,0 mg/l`
- Chlor `< 0,3 mg/l` -> Ziel `4,0 mg/l`
- Chlor `< 0,6 mg/l` -> Ziel `3,0 mg/l`
- Chlor `< 1,0 mg/l` -> Ziel `2,0 mg/l`

Die Logik setzt nicht blind auf dieses Ziel, sondern vergleicht zuerst Basisziel plus Temperatur, Abdeckung und UV mit dem Stossziel. Der Nutzungszuschlag kommt erst danach zusaetzlich auf die Endmenge.

## pH-Berechnung

Die pH-Berechnung ermittelt anhand Zielbereich, Poolvolumen und Produktdosierung die benoetigte Menge an:

- **pH-Minus** in `ml`
- **pH-Plus** in `g`

## Lernende Chloranalyse

Die Integration speichert neue Chlor-Messpunkte und bestaetigte Chlorzugaben in der lokalen Home-Assistant-Storage-Historie. Dabei werden zusaetzliche Kontextdaten wie Temperatur, Abdeckung, Nutzungsmodus, Wetter, UV und optional Pumpenlaufzeit mitgespeichert.

Berechnet werden:

- Chlorverbrauch ueber `24 h`, `7 d` und `14 d` in `mg/l/d`
- persoenlicher Chlorfaktor gegen einen konservativen Basisverlust von `0,8 mg/l/d`
- persoenlicher Chlor-Dosierfaktor aus bestaetigten Zugabe-/Nachmess-Paaren
- effektiver Wirkstoffanteil auf Basis der real beobachteten Dosierwirkung
- Chlor-Prognose fuer den erwarteten Abfall unter die Zieluntergrenze beziehungsweise unter `0,6 mg/l`
- Chlor-Stabilitaet mit Durchschnitt, Minimum, Maximum, Stichprobenzahl und Qualitaetsbewertung

Bis mindestens drei verwertbare Intervalle vorhanden sind, bleibt die Auswertung in der Lernphase.

### Dosierfaktor

Fuer den persoenlichen Dosierfaktor werden nur zeitnahe Messpaare verwendet:

- Vorher-Messung maximal `12 h` vor der Zugabe
- Nachmessung maximal `12 h` nach der Zugabe
- kein weiterer Chlor-Dosiervorgang dazwischen

Aktiv in die Chlorempfehlung fliesst der Faktor erst ab mindestens `5` verwertbaren Samples ein.

Ein **Sample** ist genau ein verwertbares Zugabe-/Nachmess-Paar fuer die Lernlogik:

- eine frische Vorher-Messung
- eine bestaetigte Chlorzugabe
- eine passende Nachmessung
- beide Messungen innerhalb des erlaubten Zeitfensters

## Chlor-Prognose und Stabilitaet

- Die Prognose schaetzt den erwarteten Tagesverlust und die Zeit bis zur Zieluntergrenze oder bis `0,6 mg/l`.
- Die Prognose nutzt Temperatur, Abdeckung, Nutzung, UV, Regen und optional Pumpenlaufzeit als Kontextgewichtung.
- Die Konfidenz wird als `high`, `medium`, `low` oder `learning` ausgegeben.
- Fuer die Stabilitaet bleibt der angezeigte `24 h`-, `7 d`- und `14 d`-Verbrauch roh beobachtet.
- Die Stabilitaetsbewertung selbst nutzt zusaetzlich eine kontextbereinigte Reihe, damit offene Abdeckung oder hohe Nutzung die Ampel nicht unnoetig verzerren.

## pH-Stabilitaetsanalyse

Die Integration speichert neue pH-Messpunkte sowie bestaetigte pH-Plus- und pH-Minus-Zugaben. Daraus entstehen bereinigte Drift-Intervalle, bei denen die erwartete Korrekturwirkung der Zugaben herausgerechnet wird.

Berechnet werden:

- pH-Drift ueber `24 h`, `7 d` und `14 d` in `pH/d`
- pH-Trend als `rising`, `falling`, `stable` oder `learning`
- pH-Stabilitaet mit Durchschnitt, Minimum, Maximum, Stichprobenzahl und Vorhersagequalitaet

## Weiterfuehrende Seiten

- [Einrichtung und Konfiguration](SETUP.md)
- [Lovelace-Karte und Demos](CARD_AND_DEMOS.md)
- [FAQ](../FAQ.md)
