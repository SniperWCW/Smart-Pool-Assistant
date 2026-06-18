class PoolChemistryCard extends HTMLElement {
  constructor() {
    super();
    this._layzspa_expanded = false;
    this._poollabFetchInFlight = false;
    this._poollabFetchClientError = null;
  }

  setConfig(config) {
    this.config = config;
  }

  static getConfigElement() {
    return document.createElement("pool-chemistry-card-editor");
  }

  static getStubConfig() {
    return {
      recommendation_entity: "sensor.pool_empfehlung"
    };
  }

  static getLayoutOptions() {
    return {
      grid_columns: 2,
      grid_rows: "auto",
    };
  }

  _resolvePoolLabFetchButtonEntity() {
    if (!this._hass) return null;

    if (this.config?.fetch_button_entity && this._hass.states[this.config.fetch_button_entity]) {
      return this.config.fetch_button_entity;
    }

    if (this._hass.states["button.poollab_messwerte_abrufen"]) {
      return "button.poollab_messwerte_abrufen";
    }

    const candidates = Object.keys(this._hass.states)
      .filter((entityId) => entityId.startsWith("button.poollab_messwerte_abrufen"))
      .sort((a, b) => a.localeCompare(b));

    return candidates[0] || null;
  }

  _getPoolLabFetchUi(attr) {
    const buttonEntity = this._resolvePoolLabFetchButtonEntity();
    const nextAllowedAt = attr.next_poollab_fetch_allowed_at ? Date.parse(attr.next_poollab_fetch_allowed_at) : NaN;
    const remainingSeconds = Number.isFinite(nextAllowedAt)
      ? Math.max(0, Math.ceil((nextAllowedAt - Date.now()) / 1000))
      : 0;
    const lastCompletedAt = attr.last_poollab_fetch_completed_at
      ? new Date(attr.last_poollab_fetch_completed_at).toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      : null;
    const fetchResult = attr.poollab_fetch_result;
    const fetchError = attr.poollab_fetch_error;

    if (!buttonEntity) {
      return {
        entityId: null,
        disabled: true,
        label: "Nicht gefunden",
        status: "Kein PoolLab-Abruf-Button erkannt. Optional im Karten-Editor setzen.",
        meta: "fehlt",
      };
    }

    if (this._poollabFetchInFlight || fetchResult === "running") {
      return {
        entityId: buttonEntity,
        disabled: true,
        label: "Abruf läuft...",
        status: "PoolLab wird gerade abgefragt.",
        meta: "läuft",
      };
    }

    if (this._poollabFetchClientError) {
      return {
        entityId: buttonEntity,
        disabled: false,
        label: "Erneut abrufen",
        status: this._poollabFetchClientError,
        meta: "fehler",
      };
    }

    if (remainingSeconds > 0) {
      return {
        entityId: buttonEntity,
        disabled: true,
        label: `Warten (${remainingSeconds}s)`,
        status: `Nächster Abruf in ${remainingSeconds} Sekunden möglich.`,
        meta: "warte",
      };
    }

    if (fetchResult === "error" && fetchError) {
      return {
        entityId: buttonEntity,
        disabled: false,
        label: "Erneut abrufen",
        status: fetchError,
        meta: "fehler",
      };
    }

    if (lastCompletedAt) {
      return {
        entityId: buttonEntity,
        disabled: false,
        label: "Messwerte abrufen",
        status: `Zuletzt erfolgreich um ${lastCompletedAt}.`,
        meta: "bereit",
      };
    }

    return {
      entityId: buttonEntity,
      disabled: false,
      label: "Messwerte abrufen",
      status: "Bereit für einen manuellen PoolLab-Abruf.",
      meta: "bereit",
    };
  }

  async _pressPoolLabFetchButton() {
    if (!this._hass) return;

    const entityId = this._resolvePoolLabFetchButtonEntity();
    if (!entityId) return;
    this._poollabFetchClientError = null;
    this._poollabFetchInFlight = true;
    this.hass = this._hass;

    try {
      await this._hass.callService("button", "press", { entity_id: entityId });
    } catch (err) {
      this._poollabFetchClientError = `Abruf fehlgeschlagen: ${err?.message || err}`;
    } finally {
      this._poollabFetchInFlight = false;
      this.hass = this._hass;
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this.config || !hass) return;

    const rec = hass.states[this.config.recommendation_entity];
    if (!rec) {
      this.innerHTML = `
        <ha-card>
          <div style="padding: 16px; color: var(--error-color); text-align: center;">
            Entität <b>${this.config.recommendation_entity}</b> nicht gefunden.<br>
            Bitte prüfe die Dashboard-Konfiguration!
          </div>
        </ha-card>
      `;
      return;
    }

    const attr = rec.attributes;
    const hist = attr.history || {};
    const isShock = attr.is_shock === true;

    // Erstelle das Skelett der Karte nur einmal
    if (!this.content) {
      this.innerHTML = `
        <ha-card header="💧 Smart Pool Assistant">
          <div class="card-content">
            <div id="status-box"></div>
            <div class="recommendation-section">
              <div class="rec-row">
                <ha-icon icon="mdi:pill"></ha-icon>
                <div class="rec-content">
                  <div id="chlor-rec"></div>
                  <div id="chlor-hist" class="hist-text"></div>
                  <details class="chlor-breakdown-details">
                    <summary>Berechnungsdetails</summary>
                    <div id="chlor-breakdown-info"></div>
                  </details>
                  <div class="log-input">
                    <input type="number" id="input-chlor" step="0.1" placeholder="Menge g">
                    <button id="btn-chlor">OK</button>
                  </div>
                </div>
              </div>
              <div class="rec-row">
                <ha-icon icon="mdi:test-tube"></ha-icon>
                <div class="rec-content">
                  <div id="ph-rec"></div>
                  <div id="ph-hist" class="hist-text"></div>
                  <div class="log-input">
                    <input type="number" id="input-ph_plus" step="0.1" placeholder="Plus g">
                    <input type="number" id="input-ph_minus" step="0.1" placeholder="Minus ml">
                    <button id="btn-ph">OK</button>
                  </div>
                </div>
              </div>
            </div>

            <div id="layzspa-container"></div>

            <div class="info-row-container">
              <details id="maintenance-section" class="measurements-section history-section" style="display: none;">
                <summary class="section-title" style="cursor: pointer; outline: none; margin-bottom: 0;">🕒 Letzte Aktivitäten</summary>
                <div id="maintenance-info" class="history-table" style="margin-top: 8px;"></div>
              </details>
              <details id="api-history-section" class="measurements-section history-section" style="display: none;">
                <summary class="section-title" style="cursor: pointer; outline: none; margin-bottom: 0;">☁️ Letzte Cloud-Messwerte (API)</summary>
                <div id="api-history-list" class="history-table" style="margin-top: 8px;"></div>
              </details>
            </div>
            <div class="measurements-section">
              <div class="section-title">📅 Aktuelle Messwerte:</div>
              <div id="measurements-table" class="metrics-table"></div>
            </div>
            <div class="measurements-section">
              <div class="section-title">⚙️ Filter Wartung:</div>
              <div id="filter-maintenance-grid" class="m-grid">
                <div class="m-item">
                  <b>Reinigung:</b> <span id="filter-clean-hours">--</span> Stunden her <small>(Empf. alle <span id="filter-clean-interval">--</span> Stunden)</small>
                  <button id="btn-filter-clean" class="small-btn">Gereinigt</button>
                </div>
                <div class="m-item">
                  <b>Wechsel:</b> <span id="filter-replace-days">--</span> Tage her <small>(Empf. alle <span id="filter-replace-interval">--</span> Tage)</small>
                  <button id="btn-filter-replace" class="small-btn">Gewechselt</button>
                </div>
              </div>
            </div>
            <div class="measurements-section" style="margin-bottom: 12px;">
              <div class="section-title">🏖️ Status & Nutzung:</div>
              <div class="log-input" style="justify-content: space-between;">
                <div style="display: flex; gap: 8px; align-items: center;">
                  <ha-icon id="icon-covered" icon="mdi:pool"></ha-icon>
                  <button id="btn-toggle-cover" class="small-btn" style="margin-left:0;">--</button>
                </div>
                <div id="usage-modes" class="usage-grid">
                  <button class="mode-btn" data-mode="0"><ha-icon icon="mdi:sleep"></ha-icon> Keine</button>
                  <button class="mode-btn" data-mode="1"><ha-icon icon="mdi:account-group"></ha-icon> Normal</button>
                  <button class="mode-btn" data-mode="2"><ha-icon icon="mdi:party-popper"></ha-icon> Party</button>
                </div>
              </div>
            </div>
            <div id="footer-info" class="footer"></div>
          </div>
          <style>
            .status-box { padding: 12px; border-radius: 8px; margin-bottom: 16px; font-weight: bold; text-align: center; font-size: 1.1em; }
            .status-box.warning { background: rgba(255, 152, 0, 0.1); color: #ff9800; border: 1px solid #ff9800; }
            .status-box.critical { background: rgba(244, 67, 54, 0.1); color: #f44336; border: 1px solid #f44336; }
            .status-box.ok { background: rgba(76, 175, 80, 0.1); color: #4caf50; border: 1px solid #4caf50; }
            .status-box.waiting { background: rgba(3, 169, 244, 0.12); color: #03a9f4; border: 1px solid #03a9f4; }
            .recommendation-section { margin-bottom: 0; line-height: 1.5; }
            .rec-row { display: flex; flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
            @media (max-width: 350px) { .rec-row { flex-direction: column; align-items: center; text-align: center; } }
            .rec-row:last-of-type { margin-bottom: 0; }
            .rec-content { flex: 1; }
            .rec-row > ha-icon { color: var(--primary-color); --mdc-icon-size: 28px; margin-top: 2px; }
            .hist-text { font-size: 0.85em; opacity: 0.7; font-style: italic; margin-top: 2px; min-height: 1.2em; }
            .log-input { margin-top: 8px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
            .log-input input {
              flex: 1 1 80px;
              min-width: 0;
              height: 38px;
              border-radius: 6px;
              border: 1px solid var(--divider-color);
              background: var(--card-background-color);
              color: var(--primary-text-color);
              font-size: 1em;
              padding: 0 8px;
              box-sizing: border-box;
            }
            .log-input button {
              height: 38px;
              cursor: pointer;
              background: var(--primary-color);
              color: white;
              border: none;
              border-radius: 6px;
              padding: 0 16px;
              font-size: 1em;
              font-weight: bold;
              flex-shrink: 0;
            }
            .log-input button:hover { opacity: 0.8; }
            .measurements-section { background: var(--secondary-background-color); padding: 12px; border-radius: 8px; margin-top: 16px; }
            .section-title { font-size: 0.9em; font-weight: bold; margin-bottom: 8px; opacity: 0.8; }
            .m-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; font-size: 1em; }
            .m-item { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
            .m-item small { opacity: 0.6; }
            .history-section { padding-top: 10px; }
            .history-section > summary::-webkit-details-marker { display: none; }
            .history-table,
            .metrics-table {
              display: flex;
              flex-direction: column;
              gap: 0;
              font-size: 0.9em;
            }
            .table-head,
            .table-row {
              display: grid;
              grid-template-columns: minmax(120px, 1.1fr) minmax(140px, 1.2fr) minmax(90px, 0.8fr);
              gap: 12px;
              align-items: center;
              padding: 7px 0;
            }
            .table-head {
              font-size: 0.72em;
              text-transform: uppercase;
              letter-spacing: 0.06em;
              opacity: 0.65;
              border-bottom: 1px solid var(--divider-color);
              padding-top: 0;
              margin-bottom: 4px;
            }
            .table-row {
              border-bottom: 1px solid var(--divider-color);
            }
            .table-row:last-child {
              border-bottom: none;
            }
            .table-label {
              font-weight: 600;
            }
            .table-value {
              font-weight: 700;
              line-height: 1.25;
            }
            .table-sub {
              display: block;
              margin-top: 2px;
              font-size: 0.82em;
              opacity: 0.65;
              font-weight: 500;
            }
            .table-meta {
              text-align: right;
              opacity: 0.78;
              white-space: nowrap;
            }
            .table-value small {
              font-size: 0.82em;
              font-weight: 500;
              opacity: 0.7;
            }
            .table-action {
              display: flex;
              flex-direction: column;
              align-items: flex-start;
              gap: 6px;
            }
            .fetch-btn {
              height: 32px;
              padding: 0 12px;
              border-radius: 8px;
              border: 1px solid rgba(3, 169, 244, 0.35);
              background: rgba(3, 169, 244, 0.14);
              color: var(--primary-color);
              font-size: 0.85em;
              font-weight: 700;
              cursor: pointer;
            }
            .fetch-btn:hover {
              background: rgba(3, 169, 244, 0.2);
            }
            .fetch-btn:disabled {
              opacity: 0.6;
              cursor: default;
            }
            .fetch-status {
              margin-top: 0;
              white-space: normal;
            }
            .history-table .table-row .table-label { min-width: 0; }
            .history-table .table-row .table-value { font-weight: 600; }
            .footer { margin-top: 14px; font-size: 0.8em; color: var(--secondary-text-color); text-align: center; }
            #icon-covered { --mdc-icon-size: 24px; margin-right: 8px; color: var(--primary-color); }
            .status-ok { color: var(--success-color, #4CAF50); }
            .status-warning { color: var(--warning-color, #FF9800); }
            .status-critical { color: var(--error-color, #F44336); }
            .bt-badge {
              display: inline-flex;
              align-items: center;
              gap: 6px;
              padding: 4px 10px;
              border-radius: 999px;
              font-size: 0.85em;
              font-weight: 700;
              line-height: 1;
              border: 1px solid transparent;
              white-space: nowrap;
            }
            .bt-badge.connected {
              background: rgba(76, 175, 80, 0.14);
              color: var(--success-color, #4CAF50);
              border-color: rgba(76, 175, 80, 0.35);
            }
            .bt-badge.disconnected {
              background: rgba(244, 67, 54, 0.12);
              color: var(--error-color, #F44336);
              border-color: rgba(244, 67, 54, 0.35);
            }
            .bt-dot {
              width: 8px;
              height: 8px;
              border-radius: 50%;
              background: currentColor;
              flex: 0 0 8px;
              box-shadow: 0 0 6px currentColor;
            }
            .small-btn { height: 28px; padding: 0 10px; font-size: 0.85em; flex-shrink: 0; }
            .usage-grid { display: flex; gap: 8px; flex-wrap: wrap; }

            .info-row-container { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }
            .info-row-container > * { flex: 1; min-width: 250px; margin-top: 0 !important; }

            @media (max-width: 640px) {
              .table-head,
              .table-row {
                grid-template-columns: 1fr;
                gap: 4px;
              }
              .table-meta {
                text-align: left;
              }
              .table-head {
                display: none;
              }
            }

            .mode-btn {
              height: 32px;
              padding: 0 10px;
              font-size: 0.85em;
              border-radius: 8px;
              border: 1px solid var(--divider-color);
              background: var(--secondary-background-color);
              color: var(--primary-text-color);
              cursor: pointer;
              display: flex;
              align-items: center;
              gap: 4px;
              transition: all 0.2s ease;
            }
            .mode-btn ha-icon { --mdc-icon-size: 18px; margin: 0; color: inherit; display: block; }
            .mode-btn.active { background: var(--success-color, #4CAF50); color: white; border-color: var(--success-color, #4CAF50); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }

            /* LayzSpa Panel Styles */
            .layzspa-panel { border: 1px solid var(--divider-color); border-radius: 8px; margin-top: 16px; overflow: hidden; background: var(--card-background-color); }
            .layzspa-header { padding: 10px 12px; background: var(--secondary-background-color); cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
            .layzspa-title { display: flex; align-items: center; gap: 8px; font-weight: bold; }
            .layzspa-content { display: none; padding: 12px; flex-direction: column; gap: 12px; border-top: 1px solid var(--divider-color); }
            .layzspa-panel.expanded .layzspa-content { display: flex; }
            .layzspa-connection-badge { display: flex; align-items: center; gap: 8px; font-size: 0.85em; opacity: 0.8; }
            .layzspa-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
            .connected .layzspa-dot { background: var(--success-color, #4CAF50); box-shadow: 0 0 4px var(--success-color); }
            .disconnected .layzspa-dot { background: var(--error-color, #F44336); }
            .layzspa-info-row { display: flex; gap: 8px; flex-wrap: wrap; }
            .layzspa-info-chip { background: var(--secondary-background-color); padding: 4px 8px; border-radius: 6px; flex: 1; min-width: 100px; display: flex; flex-direction: column; }
            .lz-label { font-size: 0.75em; opacity: 0.6; text-transform: uppercase; }
            .lz-value { font-size: 0.9em; font-weight: bold; }
            .layzspa-controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
            .lz-btn { background: var(--secondary-background-color); border: 1px solid var(--divider-color); color: var(--primary-text-color); border-radius: 8px; padding: 8px; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 0.8em; transition: all 0.2s; }
            .lz-btn ha-icon { --mdc-icon-size: 20px; }
            .lz-btn.active.pump { background: #2196F3; color: white; border-color: #2196F3; }
            .lz-btn.active.heat { background: #FF5722; color: white; border-color: #FF5722; }
            .lz-btn.active.bubbles { background: #00BCD4; color: white; border-color: #00BCD4; }
            .lz-disabled { opacity: 0.5; cursor: not-allowed; }
            .lz-temp-row { display: flex; align-items: center; justify-content: space-around; background: rgba(0,0,0,0.05); padding: 8px; border-radius: 8px; }
            .lz-temp-block { text-align: center; }
            .lz-temp-val { font-size: 1.2em; font-weight: bold; }
            .lz-temp-target { color: var(--primary-color); }
            .lz-temp-adjust { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: -2px; }
            .lz-temp-adjust-label { font-size: 0.8em; opacity: 0.75; min-width: 120px; text-align: center; }
            .lz-temp-btn { height: 34px; min-width: 34px; border-radius: 999px; border: 1px solid rgba(3, 169, 244, 0.35); background: rgba(3, 169, 244, 0.14); color: var(--primary-color); font-size: 1.1em; font-weight: 700; cursor: pointer; }
            .lz-temp-btn:hover { background: rgba(3, 169, 244, 0.22); }
            .lz-temp-btn:disabled { opacity: 0.5; cursor: default; }
            .lz-rssi-excellent { color: #4CAF50; }
            .lz-rssi-good { color: #8BC34A; }
            .lz-rssi-fair { color: #FFC107; }
            .lz-rssi-weak { color: #FF9800; }
            .lz-rssi-bad { color: #F44336; }

            .chlor-breakdown-details {
              margin-top: 10px;
              background-color: var(--secondary-background-color);
              border-radius: 6px;
              padding: 8px 12px;
              font-size: 0.9em;
              color: var(--secondary-text-color);
              display: none; /* Wird per JS gesteuert */
            }
            .chlor-breakdown-details summary {
              cursor: pointer;
              font-weight: bold;
              color: var(--primary-text-color);
              padding: 4px 0;
            }
            .breakdown-item {
              padding: 2px 0;
              display: flex;
              justify-content: space-between;
            }
            .breakdown-item span {
              font-weight: bold;
              color: var(--primary-text-color);
            }
            .breakdown-sum {
              border-top: 1px solid var(--divider-color);
              margin-top: 5px;
              padding-top: 5px;
              font-weight: bold;
            }
            .breakdown-final {
              font-weight: bold;
              color: var(--primary-color);
              font-size: 1.1em;
              margin-top: 5px;
            }
          </style>
        </ha-card>
      `;
      this.content = this.querySelector('.card-content');

      // Event Listener binden
      this.querySelector('#btn-chlor').onclick = () => this._handleAdd('chlor');
      this.querySelector('#btn-ph').onclick = () => {
        if (this.querySelector('#input-ph_plus').value) this._handleAdd('ph_plus');
        else if (this.querySelector('#input-ph_minus').value) this._handleAdd('ph_minus'); // Use else if to prevent both from firing
      };
      this.querySelector('#btn-toggle-cover').onclick = () => {
        const isCovered = this._lastAttr.pool_covered;
        this._handleAdd('set_covered', isCovered ? 0 : 1);
      };
      this.querySelectorAll('.mode-btn').forEach(btn => {
        btn.onclick = () => this._handleAdd('set_usage', btn.dataset.mode);
      });
      this.querySelector('#btn-filter-clean').onclick = () => this._handleAdd('filter_clean');
      this.querySelector('#btn-filter-replace').onclick = () => this._handleAdd('filter_replace');
    }

    // Aktualisiere nur die dynamischen Inhalte
    const statusBox = this.querySelector('#status-box');
    this._lastAttr = attr; // Store for toggle
    const awaitingRetest = attr.awaiting_retest === true;
    const chlorAwaitingRetest = attr.awaiting_retest_chlor === true;
    const phAwaitingRetest = attr.awaiting_retest_ph === true;

    // Status Box Logik (Synchronisiert mit der Empfehlungs-Entität vom Coordinator)
    let statusText = rec.state || '✅ Alle Werte im Zielbereich';
    let statusClass = 'ok';

    // Sicherheit: Falls der State "unavailable" oder "unknown" ist
    if (statusText === 'unavailable' || statusText === 'unknown') {
        statusText = '⚠️ Warte auf Daten...';
    }

    if (statusText.includes('⏳')) {
        statusClass = 'waiting';
    } else if (statusText.includes('⚠️') || statusText.includes('hoch') || statusText.includes('niedrig')) {
        // Wenn "hoch" oder "Stoß" vorkommt, nutzen wir Rot (critical), sonst Gelb (warning)
        statusClass = (statusText.includes('hoch') || statusText.includes('Stoß')) ? 'critical' : 'warning';
    }

    statusBox.className = `status-box ${statusClass}`;
    statusBox.textContent = statusText;

    // LayzSpa Panel Rendering
    this._updateLayzSpaPanel();

    const isFromStorage = attr.data_source === "Speicher";
    const hasChlor = attr.chlor_ist !== null && attr.chlor_ist !== undefined && !isFromStorage;
    const chlorDiff = hasChlor ? attr.chlor_ist - attr.chlor_target : 0;

    if (!hasChlor) {
      this.querySelector('#chlor-rec').innerHTML = isFromStorage
        ? "<i>Warte auf neue Messung (Werte aus Speicher)</i>"
        : "Warte auf Messwerte...";
    } else if (chlorAwaitingRetest || awaitingRetest) {
      this.querySelector('#chlor-rec').innerHTML = "<i>Warten auf erneute Messung nach Chlor-Zugabe.</i>";
    } else {
      this.querySelector('#chlor-rec').innerHTML = attr.chlor_dose > 0
        ? `Bitte <b>${Number(attr.chlor_dose).toFixed(2)}g</b> Chlor für den Zielwert hinzufügen (Vor Baden: ca. ${Number(attr.chlor_pre).toFixed(2)}g).`
        : (chlorDiff > 0.2
            ? `<span class="status-critical">Chlorwert ist zu hoch! (+${chlorDiff.toFixed(2)} mg/l)</span>`
            : (chlorDiff < -0.2 ? `Chlorwert zu niedrig.` : `Chlorwert ist optimal.`));
    }

    this.querySelector('#chlor-hist').textContent = hist.chlor ? `Zuletzt: ${Number(hist.chlor.amount).toFixed(2)}g (${hist.chlor.time})` : '';

    let phText = isFromStorage ? "<i>Warte auf neue Messung...</i>" : "Warte auf Messwerte...";
    if (attr.ph_ist !== null && attr.ph_ist !== undefined && !isFromStorage) {
      if (phAwaitingRetest || awaitingRetest) {
        phText = "<i>Warten auf erneute Messung nach pH-Zugabe.</i>";
      } else {
        phText = "pH-Wert ist optimal.";
        if (attr.ph_senker_total > 0) phText = `📉 PH-Minus: ca. <b>${Number(attr.ph_senker_total).toFixed(2)}ml</b> hinzufügen.`;
        else if (attr.ph_erhoeher_total > 0) phText = `📈 PH-Plus: ca. <b>${Number(attr.ph_erhoeher_total).toFixed(2)}g</b> hinzufügen.`;
      }
    }
    this.querySelector('#ph-rec').innerHTML = phText;

    const chlorInput = this.querySelector('#input-chlor');
    const chlorButton = this.querySelector('#btn-chlor');
    if (chlorInput) {
      chlorInput.disabled = chlorAwaitingRetest || awaitingRetest;
      chlorInput.placeholder = (chlorAwaitingRetest || awaitingRetest) ? "Neue Messung abwarten" : "Menge g";
    }
    if (chlorButton) {
      chlorButton.disabled = chlorAwaitingRetest || awaitingRetest;
    }

    const phPlusInput = this.querySelector('#input-ph_plus');
    const phMinusInput = this.querySelector('#input-ph_minus');
    const phButton = this.querySelector('#btn-ph');
    if (phPlusInput) {
      phPlusInput.disabled = phAwaitingRetest || awaitingRetest;
      phPlusInput.placeholder = (phAwaitingRetest || awaitingRetest) ? "Neue Messung abwarten" : "Plus g";
    }
    if (phMinusInput) {
      phMinusInput.disabled = phAwaitingRetest || awaitingRetest;
      phMinusInput.placeholder = (phAwaitingRetest || awaitingRetest) ? "Neue Messung abwarten" : "Minus ml";
    }
    if (phButton) {
      phButton.disabled = phAwaitingRetest || awaitingRetest;
    }

    const phPlusHist = hist.ph_plus ? `Zuletzt PH+: ${Number(hist.ph_plus.amount).toFixed(2)}g (${hist.ph_plus.time})` : '';
    const phMinusHist = hist.ph_minus ? `Zuletzt PH-: ${Number(hist.ph_minus.amount).toFixed(2)}ml (${hist.ph_minus.time})` : '';
    this.querySelector('#ph-hist').innerHTML = `${phPlusHist}${phPlusHist && phMinusHist ? ' | ' : ''}${phMinusHist}`;

    const formatActivityText = (entry) => {
      const type = entry?.type;
      const amount = entry?.amount;
      if (entry?.text) return entry.text;
      if (type === 'chlor') return amount !== undefined && amount !== null ? `${Number(amount).toFixed(0)}g Chlor hinzugefügt` : 'Chlor hinzugefügt';
      if (type === 'ph_plus') return amount !== undefined && amount !== null ? `${Number(amount).toFixed(0)}g PH-Plus hinzugefügt` : 'PH-Plus hinzugefügt';
      if (type === 'ph_minus') return amount !== undefined && amount !== null ? `${Number(amount).toFixed(0)}ml PH-Minus hinzugefügt` : 'PH-Minus hinzugefügt';
      if (type === 'filter_clean') return 'Filter gereinigt';
      if (type === 'filter_replace') return 'Filter getauscht';
      if (type === 'set_covered') return `Abdeckung: ${entry?.amount > 0 ? 'Abgedeckt' : 'Offen'}`;
      if (type === 'set_usage') {
        const modeLabels = { 0: 'Keine', 1: 'Normal', 2: 'Party', none: 'Keine', normal: 'Normal', party: 'Party' };
        return `Nutzungsmodus: ${modeLabels[amount] || 'Keine'}`;
      }
      return entry?.text || '--';
    };

    const maintenanceSection = this.querySelector('#maintenance-section');
    const lastActivities = Array.isArray(attr.last_activities) && attr.last_activities.length
      ? attr.last_activities
      : (Array.isArray(hist.last_activities) ? hist.last_activities : []);
    const hasMaintenance = lastActivities.length > 0 || !!hist.last_action;
    if (hasMaintenance) {
      maintenanceSection.style.display = 'block';
      this.querySelector('#maintenance-info').innerHTML = lastActivities.length
        ? `
          <div class="table-head">
            <div>Aktion</div>
            <div>Detail</div>
            <div>Zeit</div>
          </div>
          ${lastActivities.map(entry => {
            const text = formatActivityText(entry);
            const time = entry?.time || '--';
            const label = entry?.type === 'set_covered' ? 'Abdeckung' : entry?.type === 'set_usage' ? 'Modus' : 'Aktivität';
            return `
              <div class="table-row">
                <div class="table-label">${label}</div>
                <div class="table-value">✅ ${text}</div>
                <div class="table-meta">${time}</div>
              </div>
            `;
          }).join('')}
        `
        : `<div class="table-row"><div class="table-label">Aktivität</div><div class="table-value">✅ ${(hist.last_action || '').replace(/^0\s+/, '')}</div><div class="table-meta">--</div></div>`;
    } else {
      maintenanceSection.style.display = 'none';
    }

    const formatNum = (val) => (val !== undefined && val !== null && val !== "") ? Number(val).toFixed(2) : '--';

    const c_ist = formatNum(attr.chlor_ist);
    const ph_ist = formatNum(attr.ph_ist);
    const t_ist = formatNum(attr.temp_ist);
    const c_target = formatNum(attr.chlor_target);
    const ph_target = formatNum(attr.ph_target);

    // Helper to get colored text for measurements based on deviation
    const getValColorClass = (val, target, t1, t2) => {
      if (val === undefined || val === null || target === undefined || target === null || isNaN(val)) return '';
      const diff = Math.abs(Number(val) - Number(target));
      if (diff <= t1) return 'status-ok';
      if (diff <= t2) return 'status-warning';
      return 'status-critical';
    };

    const chlorColor = getValColorClass(attr.chlor_ist, attr.chlor_target, 0.3, 0.7);
    const phColor = getValColorClass(attr.ph_ist, attr.ph_target, 0.1, 0.3);
    const chlorSource = attr.chlor_source || '--';
    const phSource = attr.ph_source || '--';
    const tempSource = attr.temp_source || '--';
    const bluetoothConnected = this._poollabFetchInFlight || attr.bluetooth_connected === true;
    const bluetoothBadge = bluetoothConnected
      ? '<span class="bt-badge connected"><span class="bt-dot"></span>Bluetooth: Ja</span>'
      : '<span class="bt-badge disconnected"><span class="bt-dot"></span>Bluetooth: Nein</span>';
    const fetchUi = this._getPoolLabFetchUi(attr);

    // Helper to get colored text for filter status
    const getColoredDays = (days, status) => {
      let className = '';
      if (status === 'ok') className = 'status-ok';
      else if (status === 'warning') className = 'status-warning';
      else if (status === 'critical') className = 'status-critical';
      return `<span class="${className}">${days !== null ? days : '--'}</span>`;
    };

    this.querySelector('#measurements-table').innerHTML = `
      <div class="table-head">
        <div>Messwert</div>
        <div>Ist / Ziel</div>
        <div>Quelle</div>
      </div>
      <div class="table-row">
        <div class="table-label">Chlor</div>
        <div class="table-value"><span class="${chlorColor}">${c_ist} mg/l</span><span class="table-sub">Ziel: ${c_target} mg/l</span></div>
        <div class="table-meta">${chlorSource}</div>
      </div>
      <div class="table-row">
        <div class="table-label">pH-Wert</div>
        <div class="table-value"><span class="${phColor}">${ph_ist}</span><span class="table-sub">Ziel: ${ph_target}</span></div>
        <div class="table-meta">${phSource}</div>
      </div>
      <div class="table-row">
        <div class="table-label">Temperatur</div>
        <div class="table-value">${t_ist}°C</div>
        <div class="table-meta">${tempSource}</div>
      </div>
      <div class="table-row">
        <div class="table-label">BT Verbindung</div>
        <div class="table-value">${bluetoothBadge}</div>
        <div class="table-meta">${bluetoothConnected ? 'aktiv' : 'inaktiv'}</div>
      </div>
      <div class="table-row">
        <div class="table-label">PoolLab Abruf</div>
        <div class="table-value table-action">
          <button id="btn-poollab-fetch" class="fetch-btn" ${fetchUi.disabled ? "disabled" : ""}>${fetchUi.label}</button>
          <span id="poollab-fetch-status" class="table-sub fetch-status">${fetchUi.status}</span>
        </div>
        <div class="table-meta">${fetchUi.meta}</div>
      </div>
    `;
    const fetchButton = this.querySelector('#btn-poollab-fetch');
    if (fetchButton) {
      fetchButton.onclick = () => this._pressPoolLabFetchButton();
    }
    // Filter Maintenance Display
    const hoursSinceClean = attr.hours_since_filter_clean;
    const cleanStatus = attr.filter_clean_status;
    const cleanInterval = attr.filter_clean_interval;
    const daysSinceReplace = attr.days_since_filter_replace;
    const replaceStatus = attr.filter_replace_status;
    const replaceInterval = attr.filter_replace_interval;

    this.querySelector('#filter-clean-hours').innerHTML = getColoredDays(hoursSinceClean, cleanStatus);
    this.querySelector('#filter-clean-interval').textContent = cleanInterval !== null ? cleanInterval : '--';
    this.querySelector('#filter-replace-days').innerHTML = getColoredDays(daysSinceReplace, replaceStatus);
    this.querySelector('#filter-replace-interval').textContent = replaceInterval !== null ? replaceInterval : '--';

    // Cloud History Display
    const apiHistorySection = this.querySelector('#api-history-section');
    const apiHistoryList = this.querySelector('#api-history-list');
    const hasApiHistory = attr.last_api_measurements && attr.last_api_measurements.length > 0;
    if (hasApiHistory) {
        apiHistorySection.style.display = 'block';
        apiHistoryList.innerHTML = `
          <div class="table-head">
            <div>Parameter</div>
            <div>Wert</div>
            <div>Zeit</div>
          </div>
          ${attr.last_api_measurements.map(m => {
            const time = m.timestamp ? new Date(m.timestamp).toLocaleString('de-DE', {hour:'2-digit', minute:'2-digit', day:'2-digit', month:'2-digit'}) : '--';
            const param = m.parameter ? m.parameter.replace('PL ', '') : 'Unbekannt';
            const val = !isNaN(parseFloat(m.value)) ? Number(m.value).toFixed(2) : m.value;
            return `
              <div class="table-row">
                <div class="table-label">${param}</div>
                <div class="table-value"><b>${val}</b></div>
                <div class="table-meta">${time}</div>
              </div>
            `;
          }).join('')}
        `;
    } else {
        apiHistorySection.style.display = 'none';
    }

    const infoRowContainer = this.querySelector('.info-row-container');
    if (infoRowContainer) {
        infoRowContainer.style.display = (hasMaintenance || hasApiHistory) ? 'flex' : 'none';
    }

    // Chlor Breakdown Info
    const chlorBreakdownDetails = this.querySelector('.chlor-breakdown-details');
    const chlorBreakdownInfo = this.querySelector('#chlor-breakdown-info');

    if (attr.chlor_dose > 0 && !chlorAwaitingRetest && !awaitingRetest) { // Nur Details anzeigen, wenn Chlor empfohlen wird
      const base = Number(attr.chlor_breakdown_base || 0);
      const shockAdj = Number(attr.chlor_breakdown_shock_adj || 0);
      const tempAdj = Number(attr.chlor_breakdown_temp_adj || 0);
      const envAdj = Number(attr.chlor_breakdown_env_adj || 0);
      const batherAdj = Number(attr.chlor_breakdown_bather_adj || 0);
      const sumRaw = Number(attr.chlor_breakdown_sum_raw || 0);
      const minDoseApplied = Number(attr.chlor_breakdown_min_dose_applied || 0);
      const finalDose = Number(attr.chlor_dose || 0); // attr.chlor_dose ist die finale Menge

      let breakdownHtml = `
        <div class="breakdown-item">Basis (Ziel-Ist): <span>${base.toFixed(2)}g</span></div>
      `;
      if (shockAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Stoßchlor-Ziel: <span>${shockAdj > 0 ? '+' : ''}${shockAdj.toFixed(2)}g</span></div>`;
      }
      if (tempAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Temperatur-Zuschlag: <span>${tempAdj > 0 ? '+' : ''}${tempAdj.toFixed(2)}g</span></div>`;
      }
      if (envAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Offenes Becken: <span>${envAdj > 0 ? '+' : ''}${envAdj.toFixed(2)}g</span></div>`;
      }
      if (batherAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Nutzung: <span>${batherAdj > 0 ? '+' : ''}${batherAdj.toFixed(2)}g</span></div>`;
      }

      breakdownHtml += `
        <div class="breakdown-item breakdown-sum">Summe (vor Min/Max): <span>${sumRaw.toFixed(2)}g</span></div>
      `;

      if (minDoseApplied > 0) {
        breakdownHtml += `<div class="breakdown-item">Mindestdosis angewendet: <span>+${(minDoseApplied - sumRaw).toFixed(2)}g</span></div>`;
      } else if (finalDose !== sumRaw) { // Falls die obere Stoßgrenze angewendet wurde
        breakdownHtml += `<div class="breakdown-item">Stoßgrenze angewendet: <span>${(finalDose - sumRaw).toFixed(2)}g</span></div>`;
      }

      breakdownHtml += `
        <div class="breakdown-item breakdown-final">Empfohlene Menge: <span>${finalDose.toFixed(2)}g</span></div>
      `;
      chlorBreakdownInfo.innerHTML = breakdownHtml;
      chlorBreakdownDetails.style.display = 'block';
    } else {
      chlorBreakdownDetails.style.display = 'none';
    }

    // Pool Status & Usage UI
    const btnCover = this.querySelector('#btn-toggle-cover');
    const iconCover = this.querySelector('#icon-covered');
    btnCover.textContent = attr.pool_covered ? 'Abgedeckt' : 'Offen';
    iconCover.icon = attr.pool_covered ? 'mdi:pool' : 'mdi:sun-side';

    const usageModes = ["none", "normal", "party"];
    this.querySelectorAll('.mode-btn').forEach(btn => {
      btn.className = `mode-btn ${usageModes[btn.dataset.mode] === attr.usage_mode ? 'active' : ''}`;
    });

    // Fallback auf den letzten Update-Zeitpunkt der Entität selbst, falls das Attribut fehlt
    const lastCalcRaw = attr.last_calculation_raw || rec.last_updated;
    const footer = this.querySelector('#footer-info');
    footer.innerHTML = `
      <div>Berechnet: ${attr.last_calculation || '--'} | Messung: ${attr.last_measurement || '--'}${attr.last_measurement_source ? ` (${attr.last_measurement_source})` : ''}</div>
      <div style="margin-top: 4px; opacity: 0.8;">Daten-Aktualität: <ha-relative-time id="rel-time-footer"></ha-relative-time></div>
    `;
    const relTime = this.querySelector('#rel-time-footer');
    if (relTime) {
      relTime.hass = hass;
      relTime.datetime = lastCalcRaw;
    }
  }

  _updateLayzSpaPanel() {
    const cfg = this.config.layzspa;
    const container = this.querySelector('#layzspa-container');
    if (!cfg || !cfg.connection) {
      container.innerHTML = '';
      return;
    }

    const formatTemp = (value) => Number.isFinite(value) ? `${value.toFixed(1)}°C` : '--';
    const hass = this._hass;
    const get = (eid) => eid ? hass.states[eid] : null;
    const tempControl = this._getLayzSpaTempControlInfo(cfg);

    const conn = get(cfg.connection);
    const isConnected = conn?.state === "on";
    const pump = get(cfg.pump);
    const heater = get(cfg.heater);
    const bubbles = get(cfg.airbubbles);
    const rssi = this._getRSSIInfo(get(cfg.rssi)?.state);
    const tempCurrentValue = parseFloat(get(cfg.temp_current)?.state);
    const tempTargetValue = tempControl?.currentValue ?? parseFloat(get(cfg.temp_target)?.state);

    container.innerHTML = `
      <div class="layzspa-panel ${this._layzspa_expanded ? 'expanded' : ''}">
        <div class="layzspa-header" id="lz-header">
          <div class="layzspa-title"><ha-icon icon="mdi:hot-tub"></ha-icon> LayzSpa</div>
          <div class="layzspa-connection-badge ${isConnected ? 'connected' : 'disconnected'}">
            <span class="layzspa-dot"></span>
            ${isConnected ? 'Verbunden' : 'Getrennt'}
            <ha-icon icon="${this._layzspa_expanded ? 'mdi:chevron-up' : 'mdi:chevron-down'}"></ha-icon>
          </div>
        </div>
        <div class="layzspa-content">
          <div class="layzspa-info-row">
            <div class="layzspa-info-chip">
              <span class="lz-label">IP-Adresse</span>
              <span class="lz-value">${get(cfg.ip)?.state || '--'}</span>
            </div>
            <div class="layzspa-info-chip">
              <span class="lz-label">WLAN-Signal</span>
              <span class="lz-value ${rssi.cssClass}">${rssi.label}</span>
            </div>
          </div>
          <div class="layzspa-controls">
            <button class="lz-btn ${pump?.state === 'on' ? 'active pump' : ''} ${!isConnected ? 'lz-disabled' : ''}" id="lz-pump"><ha-icon icon="mdi:pump"></ha-icon> Pumpe</button>
            <button class="lz-btn ${heater?.state === 'on' ? 'active heat' : ''} ${!isConnected ? 'lz-disabled' : ''}" id="lz-heat"><ha-icon icon="mdi:fire"></ha-icon> Heizung</button>
            <button class="lz-btn ${bubbles?.state === 'on' ? 'active bubbles' : ''} ${!isConnected ? 'lz-disabled' : ''}" id="lz-bubbles"><ha-icon icon="mdi:chart-bubble"></ha-icon> Blubber</button>
          </div>
          <div class="lz-temp-row">
            <div class="lz-temp-block">
              <span class="lz-label">Aktuell</span>
              <div class="lz-temp-val">${formatTemp(tempCurrentValue)}</div>
            </div>
            <ha-icon icon="mdi:arrow-right-thin" style="color: rgba(255,255,255,0.2); --mdc-icon-size: 20px;"></ha-icon>
            <div class="lz-temp-block">
              <span class="lz-label">Ziel</span>
              <div class="lz-temp-val lz-temp-target">${formatTemp(tempTargetValue)}</div>
            </div>
          </div>
          ${tempControl ? `
            <div class="lz-temp-adjust">
              <button class="lz-temp-btn ${!isConnected ? 'lz-disabled' : ''}" id="lz-temp-down" ${!isConnected ? 'disabled' : ''}>-</button>
              <div class="lz-temp-adjust-label">Zieltemperatur anpassen</div>
              <button class="lz-temp-btn ${!isConnected ? 'lz-disabled' : ''}" id="lz-temp-up" ${!isConnected ? 'disabled' : ''}>+</button>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    // Panel Toggle
    this.querySelector('#lz-header').onclick = () => {
      this._layzspa_expanded = !this._layzspa_expanded;
      this._updateLayzSpaPanel();
    };

    // Button Events
    this.querySelector('#lz-pump').onclick = () => this._toggleLayzSpaEntity(cfg.pump);
    this.querySelector('#lz-heat').onclick = () => this._toggleLayzSpaEntity(cfg.heater);
    this.querySelector('#lz-bubbles').onclick = () => this._toggleLayzSpaEntity(cfg.airbubbles);
    const tempDown = this.querySelector('#lz-temp-down');
    const tempUp = this.querySelector('#lz-temp-up');
    if (tempDown) tempDown.onclick = () => this._adjustLayzSpaTemperature(-1);
    if (tempUp) tempUp.onclick = () => this._adjustLayzSpaTemperature(1);
  }

  _toggleLayzSpaEntity(entityId) {
    if (!entityId || !this._hass) return;
    const state = this._hass.states[entityId].state;
    const domain = entityId.split(".")[0];
    this._hass.callService(domain, state === "on" ? "turn_off" : "turn_on", { entity_id: entityId });
  }

  _resolveLayzSpaTempControlEntity(cfg) {
    if (!cfg || !this._hass) return null;

    const preferred = cfg.temp_target_control;
    if (preferred) {
      const preferredState = this._hass.states[preferred];
      const preferredDomain = preferred.split(".")[0];
      if (preferredState && (preferredDomain === "number" || preferredDomain === "climate")) {
        return preferred;
      }
    }

    const fallback = cfg.temp_target;
    if (fallback) {
      const fallbackState = this._hass.states[fallback];
      const fallbackDomain = fallback.split(".")[0];
      if (fallbackState && (fallbackDomain === "number" || fallbackDomain === "climate")) {
        return fallback;
      }
    }

    return null;
  }

  _getLayzSpaTempControlInfo(cfg) {
    const entityId = this._resolveLayzSpaTempControlEntity(cfg);
    if (!entityId || !this._hass) return null;

    const stateObj = this._hass.states[entityId];
    if (!stateObj) return null;

    const domain = entityId.split(".")[0];
    const attrs = stateObj.attributes || {};
    const currentValue = domain === "climate"
      ? parseFloat(attrs.temperature)
      : parseFloat(stateObj.state);
    const step = parseFloat(domain === "climate" ? (attrs.target_temp_step ?? 1) : (attrs.step ?? 1));
    const min = parseFloat(domain === "climate" ? attrs.min_temp : attrs.min);
    const max = parseFloat(domain === "climate" ? attrs.max_temp : attrs.max);

    if (!Number.isFinite(currentValue)) return null;

    return {
      entityId,
      domain,
      currentValue,
      step: Number.isFinite(step) && step > 0 ? step : 1,
      min,
      max,
    };
  }

  _getStepPrecision(step) {
    if (!Number.isFinite(step)) return 0;
    const stepText = String(step);
    return stepText.includes(".") ? stepText.split(".")[1].length : 0;
  }

  async _adjustLayzSpaTemperature(direction) {
    if (!this._hass || !this.config?.layzspa) return;

    const info = this._getLayzSpaTempControlInfo(this.config.layzspa);
    if (!info) return;

    const precision = this._getStepPrecision(info.step);
    let nextValue = info.currentValue + (direction * info.step);

    if (Number.isFinite(info.min)) nextValue = Math.max(info.min, nextValue);
    if (Number.isFinite(info.max)) nextValue = Math.min(info.max, nextValue);

    nextValue = Number(nextValue.toFixed(precision));

    if (info.domain === "climate") {
      await this._hass.callService("climate", "set_temperature", {
        entity_id: info.entityId,
        temperature: nextValue,
      });
      return;
    }

    await this._hass.callService("number", "set_value", {
      entity_id: info.entityId,
      value: nextValue,
    });
  }

  _getRSSIInfo(rssiValue) {
    const v = parseInt(rssiValue, 10);
    if (isNaN(v)) return { label: "?", cssClass: "lz-rssi-bad" };
    if (v >= -55) return { label: `${v} dBm`, cssClass: "lz-rssi-excellent" };
    if (v >= -65) return { label: `${v} dBm`, cssClass: "lz-rssi-good" };
    if (v >= -75) return { label: `${v} dBm`, cssClass: "lz-rssi-fair" };
    if (v >= -85) return { label: `${v} dBm`, cssClass: "lz-rssi-weak" };
    return { label: `${v} dBm`, cssClass: "lz-rssi-bad" };
  }

  _handleAdd(type, overrideVal = null) {
    const input = this.querySelector(`#input-${type}`);
    let val = overrideVal !== null ? parseFloat(overrideVal) : (input ? parseFloat(input.value) : 0);

    if ((val >= 0 || type.startsWith('set_') || type === 'set_usage') && this._hass) {
      // Optimistic UI Update: Sofortiges visuelles Feedback
      if (type === 'set_usage') {
        this.querySelectorAll('.mode-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.mode == val);
        });
      }
      if (type === 'set_covered') {
        this.querySelector('#btn-toggle-cover').textContent = val > 0 ? 'Abgedeckt' : 'Offen';
        this.querySelector('#icon-covered').icon = val > 0 ? 'mdi:pool' : 'mdi:sun-side';
      }

      this._hass.callService("smart_pool_assistant", "log_maintenance", {
        entity_id: this.config.recommendation_entity,
        type: type,
        amount: val
      });
      if (input) input.value = "";
    } else if (type === 'filter_clean' || type === 'filter_replace') {
       this._hass.callService("smart_pool_assistant", "log_maintenance", {
        entity_id: this.config.recommendation_entity,
        type: type,
        amount: 0 // No amount for filter actions
      });
      // No input field to clear for filter actions
    }
  }

  getCardSize() {
    return 3;
  }
}

class PoolChemistryCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  _valueChanged(ev) {
    if (!this._config || !this._hass) return;
    const target = ev.target;
    if (!target.configValue) return;
    const configValue = target.configValue;
    const value = ev.detail.value;

    let newConfig = { ...this._config };

    if (configValue.startsWith("lz_")) {
      const key = configValue.replace("lz_", "");
      if (this._config.layzspa && this._config.layzspa[key] === value) return;
      newConfig.layzspa = { ...newConfig.layzspa, [key]: value };
    } else {
      if (this._config[configValue] === value) return;
      newConfig[configValue] = value;
    }

    this._dispatchConfigChanged(newConfig);
  }

  _dispatchConfigChanged(config) {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config },
      bubbles: true,
      composed: true,
    }));
  }

  _toggleLayzSpa(ev) {
    const newConfig = {
      ...this._config,
      layzspa: {
        ...(this._config.layzspa || {}),
        enabled: ev.target.checked
      }
    };
    this._dispatchConfigChanged(newConfig);
  }

  render() {
    if (!this._hass || !this._config) return;

    // Erstelle das Grundgerüst nur, wenn es noch nicht existiert
    if (!this._initialized) {
      this.innerHTML = `
        <div class="card-config" style="display: flex; flex-direction: column; gap: 12px; padding: 10px;">
          <ha-entity-picker id="main-picker" label="Empfehlungs-Entität (Hauptsensor)" allow-custom-entity></ha-entity-picker>
          <ha-entity-picker id="fetch-button-picker" label="PoolLab-Abruf-Button (optional)" allow-custom-entity></ha-entity-picker>
          <div style="font-size: 0.8em; opacity: 0.7;">Leer lassen = automatische Erkennung von <code>button.poollab_messwerte_abrufen</code>.</div>
          <hr style="width: 100%; border: 0.5px solid var(--divider-color);">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>Whirlpool-Steuerung (LayzSpa) aktivieren</span>
            <ha-switch id="lz-enabled-switch"></ha-switch>
          </div>
          <div id="lz-pickers" style="display: none; flex-direction: column; gap: 8px; padding-left: 12px; border-left: 2px solid var(--primary-color);"></div>
        </div>
      `;

      this.querySelector('#main-picker').addEventListener('value-changed', (ev) => this._valueChanged(ev));
      this.querySelector('#fetch-button-picker').addEventListener('value-changed', (ev) => this._valueChanged(ev));
      this.querySelector('#lz-enabled-switch').addEventListener('change', (ev) => this._toggleLayzSpa(ev));
      this._initialized = true;
    }

    // Update Haupt-Picker
    const mainPicker = this.querySelector('#main-picker');
    if (mainPicker) {
      mainPicker.hass = this._hass;
      mainPicker.value = this._config.recommendation_entity;
      mainPicker.configValue = "recommendation_entity";
    }

    const fetchButtonPicker = this.querySelector('#fetch-button-picker');
    if (fetchButtonPicker) {
      fetchButtonPicker.hass = this._hass;
      fetchButtonPicker.value = this._config.fetch_button_entity || "";
      fetchButtonPicker.configValue = "fetch_button_entity";
      fetchButtonPicker.includeDomains = ["button"];
    }

    // Update LayzSpa Switch
    const lzSwitch = this.querySelector('#lz-enabled-switch');
    if (lzSwitch) {
      lzSwitch.checked = !!this._config.layzspa?.enabled;
    }

    const pickersDef = [
        { key: "connection", label: "Verbindung (Binary Sensor)", domain: "binary_sensor" },
        { key: "ip", label: "IP-Adresse (Sensor)", domain: "sensor" },
        { key: "rssi", label: "WLAN-Signal (Sensor)", domain: "sensor" },
        { key: "pump", label: "Pumpe (Switch)", domain: "switch" },
        { key: "heater", label: "Heizung (Switch)", domain: "switch" },
        { key: "airbubbles", label: "Luftblasen (Switch)", domain: "switch" },
        { key: "temp_current", label: "Ist-Temperatur", domain: "sensor" },
        { key: "temp_target", label: "Ziel-Temperatur", domain: "sensor" },
        { key: "temp_target_control", label: "Ziel-Temperatur Steuerung", domains: ["number", "climate"] },
      ];

    const lzPickersContainer = this.querySelector('#lz-pickers');
    if (lzPickersContainer) {
      const isEnabled = !!this._config.layzspa?.enabled;
      lzPickersContainer.style.display = isEnabled ? 'flex' : 'none';

      if (isEnabled) {
        pickersDef.forEach(p => {
          let picker = lzPickersContainer.querySelector(`ha-entity-picker[data-key="${p.key}"]`);

          if (!picker) {
            picker = document.createElement('ha-entity-picker');
            picker.setAttribute('data-key', p.key);
            picker.label = p.label;
            picker.configValue = `lz_${p.key}`;
            picker.includeDomains = p.domains || [p.domain];
            picker.addEventListener('value-changed', (ev) => this._valueChanged(ev));
            lzPickersContainer.appendChild(picker);
          }

        picker.hass = this._hass;
          const currentValue = this._config.layzspa ? this._config.layzspa[p.key] : "";
          if (picker.value !== currentValue) {
            picker.value = currentValue;
          }
        });
      }
    }
  }
}

if (!customElements.get('pool-chemistry-card')) {
    customElements.define('pool-chemistry-card', PoolChemistryCard);
    customElements.define('pool-chemistry-card-editor', PoolChemistryCardEditor);
    console.info("%c SMART-POOL-ASSISTANT %c 1.0.19 ", "color: white; background: #03a9f4; font-weight: 700;", "color: #03a9f4; background: white; font-weight: 700;");
}


