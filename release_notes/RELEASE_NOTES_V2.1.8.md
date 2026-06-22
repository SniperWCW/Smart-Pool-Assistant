# Release Notes V2.1.8

## Bugfix

- Die Manifest-Version fuer den Lovelace-Cachebuster wird beim Setup nicht mehr direkt im Home-Assistant-Event-Loop per `open()` gelesen.
- Das Lesen von `manifest.json` laeuft jetzt ueber `hass.async_add_executor_job(...)` im Executor.
- Damit sollte die Home-Assistant-Warnung `Detected blocking call to open` fuer `custom_components/smart_pool_assistant/__init__.py` verschwinden.

## Dokumentation / Versionierung

- `README.md`, `TECHNISCHE_DOKUMENTATION.md`, `Changelog.md`, `manifest.json`, Frontend-Version und diese Release Notes wurden auf `2.1.8` aktualisiert.
