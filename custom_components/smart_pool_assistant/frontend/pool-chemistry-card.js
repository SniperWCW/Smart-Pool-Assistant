class PoolChemistryCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    if (!this.config || !hass) return;

    const chlor = hass.states[this.config.chlor_entity];
    const ph = hass.states[this.config.ph_entity];
    const rec = hass.states[this.config.recommendation_entity];
    const lastCalc = rec?.attributes.last_calculation || '-';
    const lastMeasure = rec?.attributes.last_measurement || '-';

    this.innerHTML = `
      <ha-card header="💧 Smart Pool Assistant">
        <div class="card-content">
          <div class="pool-row">
            <ha-icon icon="mdi:pill"></ha-icon>
            <span><b>Chlor:</b> ${chlor ? chlor.state : '-'} ${chlor?.attributes.unit_of_measurement || 'mg/l'}</span>
          </div>
          <div class="pool-row">
            <ha-icon icon="mdi:test-tube"></ha-icon>
            <span><b>pH-Wert:</b> ${ph ? ph.state : '-'}</span>
          </div>
          <div class="pool-status" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--divider-color);">
            <ha-icon icon="mdi:information-outline"></ha-icon>
            <span>${rec ? rec.state : 'Keine Empfehlung verfügbar'}</span>
          </div>
          <div class="pool-ts">
            <div>Berechnet: ${lastCalc}</div>
            <div>Messwerte von: ${lastMeasure}</div>
          </div>
        </div>
        <style>
          .pool-row { display: flex; align-items: center; margin-bottom: 8px; gap: 12px; }
          .pool-status { display: flex; align-items: center; gap: 12px; font-style: italic; }
          .pool-ts { margin-top: 12px; font-size: 0.8em; color: var(--secondary-text-color); display: flex; justify-content: space-between; }
          ha-icon { color: var(--primary-color); }
        </style>
      </ha-card>
    `;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('pool-chemistry-card', PoolChemistryCard);

console.info("%c SMART-POOL-ASSISTANT %c 0.1.1 ", "color: white; background: #03a9f4; font-weight: 700;", "color: #03a9f4; background: white; font-weight: 700;");