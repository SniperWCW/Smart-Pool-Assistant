class PoolChemistryCard extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    const chlor = hass.states[this.config.chlor_entity];
    const ph = hass.states[this.config.ph_entity];
    const recommendation = hass.states[this.config.recommendation_entity];

    this.innerHTML = `
      <ha-card>
        <div style="padding:16px;">
          <h2>💧 Smart Pool Assistant</h2>

          <div style="margin-top:12px;">
            <b>Chlor:</b> ${chlor?.state || '-'} mg/l
          </div>

          <div>
            <b>pH:</b> ${ph?.state || '-'}
          </div>

          <div style="margin-top:16px;">
            ${recommendation?.state || 'Keine Empfehlung'}
          </div>
        </div>
      </ha-card>
    `;
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('pool-chemistry-card', PoolChemistryCard);
