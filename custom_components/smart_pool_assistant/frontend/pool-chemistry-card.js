class PoolChemistryCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    if (!this.config || !hass) return;

    const rec = hass.states[this.config.recommendation_entity];
    if (!rec) return;

    const attr = rec.attributes;
    const hist = attr.history || {};
    const isShock = attr.chlor_ist < 0.5;

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
            <div class="measurements-section">
              <div class="section-title">📅 Aktuelle Messwerte:</div>
              <div id="measurements-grid" class="m-grid"></div>
            </div>
            <div id="footer-info" class="footer"></div>
          </div>
          <style>
            .status-box { padding: 12px; border-radius: 8px; margin-bottom: 16px; font-weight: bold; text-align: center; font-size: 1.1em; }
            .status-box.warning { background: rgba(255, 152, 0, 0.1); color: #ff9800; border: 1px solid #ff9800; }
            .status-box.ok { background: rgba(76, 175, 80, 0.1); color: #4caf50; border: 1px solid #4caf50; }
            .recommendation-section { margin-bottom: 16px; line-height: 1.5; }
            .rec-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; }
            .rec-content { flex: 1; }
            ha-icon { color: var(--primary-color); --mdc-icon-size: 28px; margin-top: 2px; }
            .hist-text { font-size: 0.85em; opacity: 0.7; font-style: italic; margin-top: 2px; min-height: 1.2em; }
            .log-input { margin-top: 8px; display: flex; gap: 8px; align-items: center; }
            .log-input input { 
              width: 100px; 
              height: 38px; 
              border-radius: 6px; 
              border: 1px solid var(--divider-color); 
              background: var(--card-background-color); 
              color: var(--primary-text-color); 
              font-size: 1em; 
              padding: 0 8px;
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
            }
            .log-input button:hover { opacity: 0.8; }
            .measurements-section { background: var(--secondary-background-color); padding: 12px; border-radius: 8px; }
            .section-title { font-size: 0.9em; font-weight: bold; margin-bottom: 8px; opacity: 0.8; }
            .m-grid { display: grid; grid-template-columns: 1fr; gap: 6px; font-size: 1em; }
            .m-item small { opacity: 0.6; margin-left: 6px; }
            .footer { margin-top: 14px; font-size: 0.8em; color: var(--secondary-text-color); text-align: center; }
          </style>
        </ha-card>
      `;
      this.content = this.querySelector('.card-content');

      // Event Listener binden
      this.querySelector('#btn-chlor').onclick = () => this._handleAdd(hass, 'chlor');
      this.querySelector('#btn-ph').onclick = () => {
        if (this.querySelector('#input-ph_plus').value) this._handleAdd(hass, 'ph_plus');
        if (this.querySelector('#input-ph_minus').value) this._handleAdd(hass, 'ph_minus');
      };
    }

    // Aktualisiere nur die dynamischen Inhalte
    const statusBox = this.querySelector('#status-box');
    statusBox.className = `status-box ${isShock ? 'warning' : 'ok'}`;
    statusBox.textContent = isShock ? '⚠️ Stoßchlorung empfohlen' : '✅ Wasserqualität in Ordnung';

    this.querySelector('#chlor-rec').innerHTML = attr.chlor_dose > 0 
      ? `Bitte <b>${attr.chlor_dose}g</b> Chlor für den Zielwert hinzufügen (Vor Baden: ca. ${attr.chlor_pre}g).`
      : `Chlorwert ist optimal.`;
    
    this.querySelector('#chlor-hist').textContent = hist.chlor ? `Zuletzt: ${hist.chlor.amount}g (${hist.chlor.time})` : '';

    let phText = "pH-Wert ist optimal.";
    if (attr.ph_senker_total > 0) phText = `📉 PH-Minus: ca. <b>${attr.ph_senker_total}ml</b> hinzufügen.`;
    else if (attr.ph_erhoeher_total > 0) phText = `📈 PH-Plus: ca. <b>${attr.ph_erhoeher_total}g</b> hinzufügen.`;
    this.querySelector('#ph-rec').innerHTML = phText;

    const phPlusHist = hist.ph_plus ? `Zuletzt PH+: ${hist.ph_plus.amount}g (${hist.ph_plus.time})` : '';
    const phMinusHist = hist.ph_minus ? `Zuletzt PH-: ${hist.ph_minus.amount}ml (${hist.ph_minus.time})` : '';
    this.querySelector('#ph-hist').innerHTML = `${phPlusHist}${phPlusHist && phMinusHist ? ' | ' : ''}${phMinusHist}`;

    const maintenanceSection = this.querySelector('#maintenance-section');
    if (hist.last_action) {
      maintenanceSection.style.display = 'block';
      this.querySelector('#maintenance-info').innerHTML = `<div class="m-item">✅ ${hist.last_action}</div>`;
    } else {
      maintenanceSection.style.display = 'none';
    }

    this.querySelector('#measurements-grid').innerHTML = `
      <div class="m-item"><b>Chlor:</b> ${attr.chlor_ist} mg/l <small>(Ziel: ${attr.chlor_target})</small></div>
      <div class="m-item"><b>pH-Wert:</b> ${attr.ph_ist} <small>(Ziel: ${attr.ph_target})</small></div>
      <div class="m-item">🌡️ <b>Temperatur:</b> ${attr.temp_ist}°C</div>
    `;

    this.querySelector('#footer-info').textContent = `Berechnet: ${attr.last_calculation} | Messung: ${attr.last_measurement}`;
  }

  _handleAdd(hass, type) {
    const input = this.querySelector(`#input-${type}`);
    const val = parseFloat(input.value);
    if (val > 0) {
      hass.callService("smart_pool_assistant", "log_maintenance", {
        entity_id: this.config.recommendation_entity,
        type: type,
        amount: val
      });
      input.value = "";
    }
  }

  getCardSize() {
    return 3;
  }
}

if (!customElements.get('pool-chemistry-card')) {
    customElements.define('pool-chemistry-card', PoolChemistryCard);
    console.info("%c SMART-POOL-ASSISTANT %c 0.1.0 ", "color: white; background: #03a9f4; font-weight: 700;", "color: #03a9f4; background: white; font-weight: 700;");
}