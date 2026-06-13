class PoolChemistryCard extends HTMLElement {
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
            <div id="maintenance-section" class="measurements-section" style="margin-top: 12px; display: none;">
              <div class="section-title">🕒 Letzte Aktivitäten:</div>
              <div id="maintenance-info" class="m-grid"></div>
            </div>
            <details id="api-history-section" class="measurements-section" style="margin-top: 12px; display: none; background: rgba(3, 169, 244, 0.05); border: 1px dashed var(--primary-color);">
              <summary class="section-title" style="cursor: pointer; outline: none; margin-bottom: 0;">☁️ Letzte Cloud-Messwerte (API)</summary>
              <div id="api-history-list" style="font-size: 0.85em; margin-top: 8px;"></div>
            </details>
            <div class="measurements-section" style="margin-top: 12px;">
              <div class="section-title">📅 Aktuelle Messwerte:</div>
              <div id="measurements-grid" class="m-grid"></div>
            </div>
            <div class="measurements-section" style="margin-top: 12px;">
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
            <div class="measurements-section" style="margin-top: 12px; margin-bottom: 12px;">
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
            .status-box.ok { background: rgba(76, 175, 80, 0.1); color: #4caf50; border: 1px solid #4caf50; }
            .recommendation-section { margin-bottom: 16px; line-height: 1.5; }
            .rec-row { display: flex; flex-direction: row; align-items: flex-start; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
            @media (max-width: 350px) { .rec-row { flex-direction: column; } }
            .rec-content { flex: 1; }
            ha-icon { color: var(--primary-color); --mdc-icon-size: 28px; margin-top: 2px; }
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
            .measurements-section { background: var(--secondary-background-color); padding: 12px; border-radius: 8px; }
            .section-title { font-size: 0.9em; font-weight: bold; margin-bottom: 8px; opacity: 0.8; }
            .m-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; font-size: 1em; }
            .m-item { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
            .m-item small { opacity: 0.6; }
            .footer { margin-top: 14px; font-size: 0.8em; color: var(--secondary-text-color); text-align: center; }
            .status-ok { color: var(--success-color, #4CAF50); }
            .status-warning { color: var(--warning-color, #FF9800); }
            .status-critical { color: var(--error-color, #F44336); }
            .small-btn { height: 28px; padding: 0 10px; font-size: 0.85em; flex-shrink: 0; }
            .usage-grid { display: flex; gap: 8px; flex-wrap: wrap; }
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
            .mode-btn ha-icon { --mdc-icon-size: 18px; margin: 0; color: inherit; }
            .mode-btn.active { background: var(--success-color, #4CAF50); color: white; border-color: var(--success-color, #4CAF50); box-shadow: 0 2px 4px rgba(0,0,0,0.2); }

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

    // Status Box Logik erweitern
    const hasPhIssue = (attr.ph_senker_total > 0 || attr.ph_erhoeher_total > 0);
    const isShockRecommended = attr.is_shock === true; // Renamed for clarity with isShock variable

    let statusText = '✅ Wasserqualität in Ordnung';
    let statusClass = 'ok';

    if (hasPhIssue && isShockRecommended) {
      statusText = '⚠️ pH-Wert anpassen, danach Stoßchlorung!';
      statusClass = 'warning';
    } else if (hasPhIssue) {
      statusText = '⚠️ pH-Wert zuerst anpassen!';
      statusClass = 'warning';
    } else if (isShockRecommended) {
      statusText = '⚠️ Stoßchlorung empfohlen';
      statusClass = 'warning';
    }

    statusBox.className = `status-box ${statusClass}`;
    statusBox.textContent = statusText;

    this.querySelector('#chlor-rec').innerHTML = attr.chlor_dose > 0
      ? `Bitte <b>${Number(attr.chlor_dose).toFixed(2)}g</b> Chlor für den Zielwert hinzufügen (Vor Baden: ca. ${Number(attr.chlor_pre).toFixed(2)}g).`
      : `Chlorwert ist optimal.`;

    this.querySelector('#chlor-hist').textContent = hist.chlor ? `Zuletzt: ${Number(hist.chlor.amount).toFixed(2)}g (${hist.chlor.time})` : '';

    let phText = "pH-Wert ist optimal.";
    if (attr.ph_senker_total > 0) phText = `📉 PH-Minus: ca. <b>${Number(attr.ph_senker_total).toFixed(2)}ml</b> hinzufügen.`;
    else if (attr.ph_erhoeher_total > 0) phText = `📈 PH-Plus: ca. <b>${Number(attr.ph_erhoeher_total).toFixed(2)}g</b> hinzufügen.`;
    this.querySelector('#ph-rec').innerHTML = phText;

    const phPlusHist = hist.ph_plus ? `Zuletzt PH+: ${Number(hist.ph_plus.amount).toFixed(2)}g (${hist.ph_plus.time})` : '';
    const phMinusHist = hist.ph_minus ? `Zuletzt PH-: ${Number(hist.ph_minus.amount).toFixed(2)}ml (${hist.ph_minus.time})` : '';
    this.querySelector('#ph-hist').innerHTML = `${phPlusHist}${phPlusHist && phMinusHist ? ' | ' : ''}${phMinusHist}`;

    const maintenanceSection = this.querySelector('#maintenance-section');
    if (hist.last_action) {
      maintenanceSection.style.display = 'block';
      this.querySelector('#maintenance-info').innerHTML = `<div class="m-item">✅ ${hist.last_action}</div>`;
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

    // Helper to get colored text for filter status
    const getColoredDays = (days, status) => {
      let className = '';
      if (status === 'ok') className = 'status-ok';
      else if (status === 'warning') className = 'status-warning';
      else if (status === 'critical') className = 'status-critical';
      return `<span class="${className}">${days !== null ? days : '--'}</span>`;
    };

    this.querySelector('#measurements-grid').innerHTML = `
      <div class="m-item"><b>Chlor:</b> <span class="${chlorColor}">${c_ist} mg/l</span> <small>(Ziel: ${c_target})</small></div>
      <div class="m-item"><b>pH-Wert:</b> <span class="${phColor}">${ph_ist}</span> <small>(Ziel: ${ph_target})</small></div>
      <div class="m-item">🌡️ <b>Temperatur:</b> ${t_ist}°C</div>
    `;

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
    if (attr.last_api_measurements && attr.last_api_measurements.length > 0) {
        apiHistorySection.style.display = 'block';
        apiHistoryList.innerHTML = attr.last_api_measurements.map(m => {
            const time = m.timestamp ? new Date(m.timestamp).toLocaleString('de-DE', {hour:'2-digit', minute:'2-digit', day:'2-digit', month:'2-digit'}) : '--';
            const param = m.parameter ? m.parameter.replace('PL ', '') : 'Unbekannt';
            const val = !isNaN(parseFloat(m.value)) ? Number(m.value).toFixed(2) : m.value;
            return `<div style="display:flex; justify-content:space-between; border-bottom:1px solid var(--divider-color); padding: 4px 0;">
                <span>${param}:</span>
                <span><b>${val}</b> <small>(${time})</small></span>
            </div>`;
        }).join('');
    } else {
        apiHistorySection.style.display = 'none';
    }

    // Chlor Breakdown Info
    const chlorBreakdownDetails = this.querySelector('.chlor-breakdown-details');
    const chlorBreakdownInfo = this.querySelector('#chlor-breakdown-info');

    if (attr.chlor_dose > 0) { // Nur Details anzeigen, wenn Chlor empfohlen wird
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
        breakdownHtml += `<div class="breakdown-item">Schock-Faktor: <span>${shockAdj > 0 ? '+' : ''}${shockAdj.toFixed(2)}g</span></div>`;
      }
      if (tempAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Temperatur-Korrektur: <span>${tempAdj > 0 ? '+' : ''}${tempAdj.toFixed(2)}g</span></div>`;
      }
      if (envAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Abdeckung: <span>${envAdj > 0 ? '+' : ''}${envAdj.toFixed(2)}g</span></div>`;
      }
      if (batherAdj !== 0) {
        breakdownHtml += `<div class="breakdown-item">Nutzung (Badelast): <span>${batherAdj > 0 ? '+' : ''}${batherAdj.toFixed(2)}g</span></div>`;
      }

      breakdownHtml += `
        <div class="breakdown-item breakdown-sum">Summe (vor Min/Max): <span>${sumRaw.toFixed(2)}g</span></div>
      `;

      if (minDoseApplied > 0) {
        breakdownHtml += `<div class="breakdown-item">Mindestdosis angewendet: <span>+${(minDoseApplied - sumRaw).toFixed(2)}g</span></div>`;
      } else if (finalDose !== sumRaw) { // Falls Maximaldosis angewendet wurde
        breakdownHtml += `<div class="breakdown-item">Maximaldosis angewendet: <span>${(finalDose - sumRaw).toFixed(2)}g</span></div>`;
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

    this.querySelector('#footer-info').textContent = `Berechnet: ${attr.last_calculation || '--'} | Messung: ${attr.last_measurement || '--'}`;
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

  render() {
    if (!this.innerHTML) {
      this.innerHTML = `
        <div class="card-config" style="padding: 8px;">
          <p>Die Konfiguration dieser Karte erfolgt aktuell primär über YAML.</p>
          <p>Nutze die Tabs oben, um <b>Sichtbarkeit</b> und <b>Layout</b> (Breite/Spalten) anzupassen.</p>
        </div>
      `;
    }
  }
}

if (!customElements.get('pool-chemistry-card')) {
    customElements.define('pool-chemistry-card', PoolChemistryCard);
    customElements.define('pool-chemistry-card-editor', PoolChemistryCardEditor);
    console.info("%c SMART-POOL-ASSISTANT %c 0.2.0 ", "color: white; background: #03a9f4; font-weight: 700;", "color: #03a9f4; background: white; font-weight: 700;");
}
