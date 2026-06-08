class PoolChemistryCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    if (!this.config || !hass) return;

    const rec = hass.states[this.config.recommendation_entity];
    if (!rec) return;

    const attr = rec.attributes;
    const isShock = attr.chlor_ist < 0.5;
    
    // Dynamische Texte für Chlor
    const chlorText = attr.chlor_dose > 0 
      ? `Bitte <b>${attr.chlor_dose}g</b> Chlor für den Zielwert hinzufügen (Vor Baden: ca. ${attr.chlor_pre}g).`
      : `Chlorwert ist optimal.`;

    // Dynamische Texte für pH
    let phText = "pH-Wert ist optimal.";
    if (attr.ph_senker_total > 0) {
      phText = `📉 pH senken: ca. <b>${attr.ph_senker_total}ml</b> pH-Senker hinzufügen.`;
    } else if (attr.ph_erhoeher_total > 0) {
      phText = `📈 pH erhöhen: ca. <b>${attr.ph_erhoeher_total}g</b> pH-Heber hinzufügen.`;
    }

    this.innerHTML = `
      <ha-card header="💧 Smart Pool Assistant">
        <div class="card-content">
          <div class="status-box ${isShock ? 'warning' : 'ok'}">
             ${isShock ? '⚠️ Stoßchlorung empfohlen' : '✅ Wasserqualität in Ordnung'}
          </div>

          <div class="recommendation-section">
            <div class="rec-row">
              <ha-icon icon="mdi:pill"></ha-icon>
              <span>${chlorText}</span>
            </div>
            <div class="rec-row">
              <ha-icon icon="mdi:test-tube"></ha-icon>
              <span>${phText}</span>
            </div>
          </div>

          <div class="measurements-section">
            <div class="section-title">📅 Aktuelle Messwerte:</div>
            <div class="m-grid">
              <div class="m-item"><b>Chlor:</b> ${attr.chlor_ist} mg/l <small>(Ziel: ${attr.chlor_target})</small></div>
              <div class="m-item"><b>pH-Wert:</b> ${attr.ph_ist} <small>(Ziel: ${attr.ph_target})</small></div>
              <div class="m-item">🌡️ <b>Temperatur:</b> ${attr.temp_ist}°C</div>
            </div>
          </div>

          <div class="footer">
            Berechnet: ${attr.last_calculation} | Messung: ${attr.last_measurement}
          </div>
        </div>
        <style>
          .status-box { padding: 10px; border-radius: 8px; margin-bottom: 16px; font-weight: bold; text-align: center; }
          .status-box.warning { background: rgba(255, 152, 0, 0.1); color: #ff9800; border: 1px solid #ff9800; }
          .status-box.ok { background: rgba(76, 175, 80, 0.1); color: #4caf50; border: 1px solid #4caf50; }
          
          .recommendation-section { margin-bottom: 16px; line-height: 1.4; }
          .rec-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
          ha-icon { color: var(--primary-color); }

          .measurements-section { background: var(--secondary-background-color); padding: 12px; border-radius: 8px; }
          .section-title { font-size: 0.9em; font-weight: bold; margin-bottom: 8px; opacity: 0.8; }
          .m-grid { display: grid; grid-template-columns: 1fr; gap: 4px; font-size: 0.95em; }
          .m-item small { opacity: 0.6; margin-left: 5px; }

          .footer { margin-top: 12px; font-size: 0.75em; color: var(--secondary-text-color); text-align: center; }
        </style>
      </ha-card>
    `;
  }

  getCardSize() {
    return 3;
  }
}

if (!customElements.get('pool-chemistry-card')) {
    customElements.define('pool-chemistry-card', PoolChemistryCard);
    console.info("%c SMART-POOL-ASSISTANT %c 0.1.0 ", "color: white; background: #03a9f4; font-weight: 700;", "color: #03a9f4; background: white; font-weight: 700;");
}