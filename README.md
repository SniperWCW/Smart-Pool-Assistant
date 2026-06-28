# Smart Pool Assistant

<p align="center">
  <img src="images/banner.png" alt="Smart Pool Assistant Banner" width="900">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/release-v3.0.8-blue" alt="Release">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5" alt="Home Assistant Custom Integration">
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json&query=%24.smart_pool_assistant.total&label=tracked%20installs&color=41BDF5" alt="Tracked installs">
  <img src="https://img.shields.io/github/downloads/SniperWCW/Smart-Pool-Assistant/total?label=downloads&color=F2C94C" alt="Downloads">
</p>

Der **Smart Pool Assistant** ist eine Home Assistant Integration fuer Pool- und Whirlpool-Pflege. Sie kombiniert PoolLab BLE, PoolLab Cloud, manuelle Sensoren, lernende Dosierlogik, Wartungshistorie und eine eigene Lovelace-Karte in einer zentralen Empfehlung.

**Aktueller Release-Stand: V3.0.8**

## Schnellueberblick

- volumenbezogene Chlor- und pH-Empfehlungen
- transparente Berechnungsdetails direkt in der Karte
- lernende Chlor- und pH-Analyse mit Prognosen
- manueller PoolLab-BLE-Abruf plus zyklischer Cloud-Sync
- CYA/Cyanursaeure aus PoolLab BLE und Cloud direkt in den aktuellen Messwerten
- PoolLab-Abruf oben in einer eigenen Box neben `Status` und `Baden`
- Nachmess-Workflow, Badeampel, Wetter- und LayZSpa-Integration

## Vorschau

<p align="center">
  <a href="demo/overview-status.jpg"><img src="demo/overview-status.jpg" alt="Status und Dosierempfehlung" width="320"></a>
</p>

## Dokumentation

- [Einrichtung und Konfiguration](docs/SETUP.md)
- [Chemielogik und Lernsystem](docs/CHEMISTRY.md)
- [Lovelace-Karte und Demos](docs/CARD_AND_DEMOS.md)
- [Entitaeten und bereitgestellte Sensoren](docs/ENTITIES.md)
- [FAQ und typische Diagnosefaelle](FAQ.md)
- [Technische Dokumentation](TECHNISCHE_DOKUMENTATION.md)
- [Changelog](Changelog.md)

## Navigation

| Thema | Seite |
| --- | --- |
| Setup und Konfiguration | [docs/SETUP.md](docs/SETUP.md) |
| Chemielogik und Lernsystem | [docs/CHEMISTRY.md](docs/CHEMISTRY.md) |
| Karte, Screenshots und Demos | [docs/CARD_AND_DEMOS.md](docs/CARD_AND_DEMOS.md) |
| Entitaeten | [docs/ENTITIES.md](docs/ENTITIES.md) |
| FAQ | [FAQ.md](FAQ.md) |
| Technische Referenz | [TECHNISCHE_DOKUMENTATION.md](TECHNISCHE_DOKUMENTATION.md) |

## Installation

### Ueber HACS

1. Oeffne **HACS** in Home Assistant.
2. Gehe auf **Benutzerdefinierte Repositories**.
3. Fuege dieses Repository als Typ `Integration` hinzu.
4. Installiere **Smart Pool Assistant**.
5. Starte Home Assistant neu.

### Manuell

1. Kopiere `custom_components/smart_pool_assistant` in deinen `custom_components` Ordner.
2. Starte Home Assistant neu.

## Was du als Naechstes lesen solltest

- Wenn du die Integration einrichten willst: [docs/SETUP.md](docs/SETUP.md)
- Wenn du die Chlor-Empfehlung fachlich verstehen willst: [docs/CHEMISTRY.md](docs/CHEMISTRY.md)
- Wenn du Screenshots, Kartenaufbau und LayZSpa sehen willst: [docs/CARD_AND_DEMOS.md](docs/CARD_AND_DEMOS.md)
- Wenn du tief in die Implementierung willst: [TECHNISCHE_DOKUMENTATION.md](TECHNISCHE_DOKUMENTATION.md)
