class PoolChemistryCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    if (!this.config || !hass) return;

    const chlor = hass.states[this.config.chlor_entity];
    const ph = hass.states[this.config.ph_entity];
    const rec = hass.states[this.config.recommendation_entity];

    this.innerHTML = `
      <ha-card header="💧 Smart Pool Assistant">
        <div class="card-content">
          <div class="pool-row">
            <ha-icon icon="mdi:pill"></ha-icon>
            <span><b>Chlor:</b> ${chlor ? chlor.state : '-'} ${chlor?.attributes.unit_of_measurement || 'mg/l'}</span>
          </div>
          <div class="pool-row">
            <ha-icon icon="mdi:ph"></ha-icon>
            <span><b>pH-Wert:</b> ${ph ? ph.state : '-'}</span>
          </div>
          <div class="pool-status" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--divider-color);">
            <ha-icon icon="mdi:information-outline"></ha-icon>
            <span>${rec ? rec.state : 'Keine Empfehlung verfügbar'}</span>
          </div>
        </div>
        <style>
          .pool-row { display: flex; align-items: center; margin-bottom: 8px; gap: 12px; }
          .pool-status { display: flex; align-items: center; gap: 12px; font-style: italic; }
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
