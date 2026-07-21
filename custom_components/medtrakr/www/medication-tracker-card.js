/**
 * MedTrakr - Lovelace Card
 *
 * A custom card that displays medication schedule, stock status,
 * and quick-action buttons for tracking doses.
 *
 * Installation: Add as a module resource in HA:
 *   /local/community/medtrakr/medication-tracker-card.js
 */

class MedicationTrackerCard extends HTMLElement {
  static getStubConfig() {
    return {
      entity: "",
      name: "",
      show_stock: true,
      show_schedule: true,
      show_notes: false,
    };
  }

  setConfig(config) {
    if (!config.entity && !config.entities) {
      throw new Error("You must define an entity or entities.");
    }

    this._config = config;
    this._entities = config.entities || [config.entity];
    this._name = config.name || "";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._card) {
      this._buildCard();
    }
    this._render();
  }

  _buildCard() {
    this.innerHTML = `
      <ha-card>
        <div class="card-content" id="content"></div>
      </ha-card>
    `;

    const style = document.createElement("style");
    style.textContent = `
      ha-card {
        padding: 16px;
        font-family: var(--paper-font-body1_-_font-family, Roboto);
      }
      .med-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }
      .med-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
      }
      .med-name {
        font-size: 1.1em;
        font-weight: 500;
      }
      .med-schedule {
        color: var(--secondary-text-color);
        font-size: 0.85em;
      }
      .stock-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 8px 0;
        padding: 8px;
        background: var(--card-background-color, rgba(0,0,0,0.05));
        border-radius: 8px;
      }
      .stock-label {
        font-size: 0.85em;
        color: var(--secondary-text-color);
      }
      .stock-value {
        font-weight: 600;
        font-size: 1.1em;
      }
      .stock-low {
        color: var(--error-color, #e53935);
      }
      .stock-ok {
        color: var(--success-color, #43a047);
      }
      .button-row {
        display: flex;
        gap: 8px;
        margin-top: 12px;
      }
      .btn-take {
        flex: 2;
        background: var(--success-color, #43a047);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.95em;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }
      .btn-take:hover {
        opacity: 0.9;
      }
      .btn-undo {
        flex: 1;
        background: var(--warning-color, #ff9800);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 0.85em;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
      }
      .btn-undo:hover {
        opacity: 0.9;
      }
      .btn-take:disabled, .btn-undo:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      .history-item {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        font-size: 0.8em;
      }
      .notes {
        margin-top: 8px;
        padding: 8px;
        background: var(--card-background-color, rgba(0,0,0,0.03));
        border-radius: 6px;
        font-size: 0.85em;
        color: var(--secondary-text-color);
        font-style: italic;
      }
      .last-taken {
        font-size: 0.8em;
        color: var(--secondary-text-color);
        margin-top: 8px;
      }
    `;
    this.appendChild(style);
  }

  _render() {
    const content = this.querySelector("#content");
    if (!content || !this._hass) return;

    let html = "";

    for (const entityId of this._entities) {
      html += this._renderMedication(entityId);
    }

    content.innerHTML = html;

    this._attachListeners();
  }

  _renderMedication(entityId) {
    const hass = this._hass;
    const config = this._config;

    const baseId = entityId.replace(/_stock$|_next_dose$|_days_remaining$|_take$|_undo$/, "");
    const stockEntity = `${baseId}_stock`;
    const nextDoseEntity = `${baseId}_next_dose`;
    const daysEntity = `${baseId}_days_remaining`;
    const takeButton = `${baseId}_take`;
    const undoButton = `${baseId}_undo`;

    const stockState = hass.states[stockEntity];
    const nextDoseState = hass.states[nextDoseEntity];
    const daysState = hass.states[daysEntity];
    const takeState = hass.states[takeButton];
    const undoState = hass.states[undoButton];

    if (!stockState && !nextDoseState) {
      return `<p style="color: var(--error-color);">Entity "${entityId}" not found.</p>`;
    }

    const name = stockState?.attributes?.friendly_name?.replace(" Stock", "") || "Medication";
    const color = stockState?.attributes?.color || "#009688";
    const icon = stockState?.attributes?.icon || "mdi:pill";
    const lastTaken = stockState?.attributes?.last_taken;
    const schedule = nextDoseState?.attributes?.schedule || "";
    const takenToday = nextDoseState?.attributes?.taken_today || 0;
    const isLowStock = stockState?.attributes?.low_stock || false;

    let stockHtml = "";
    if (config.show_stock !== false && stockState) {
      const stock = stockState.state;
      const unit = stockState.attributes?.unit_of_measurement || "";
      const daysRemaining = daysState ? daysState.state : null;

      stockHtml = `
        <div class="stock-row">
          <div>
            <div class="stock-label">Stock Level</div>
            <div class="stock-value ${isLowStock ? 'stock-low' : 'stock-ok'}">
              ${stock} ${unit}
              ${isLowStock ? ' ⚠ Low' : ''}
            </div>
          </div>
          ${daysRemaining ? `
          <div style="text-align: right;">
            <div class="stock-label">Days Remaining</div>
            <div class="stock-value">~${daysRemaining} days</div>
          </div>` : ''}
        </div>
      `;
    }

    let scheduleHtml = "";
    if (config.show_schedule !== false && schedule) {
      scheduleHtml = `<div class="med-schedule">${schedule}</div>`;
    }

    const isAvailable = takeState?.state !== "unavailable";
    const canUndo = undoState?.state !== "unavailable";

    let lastTakenHtml = "";
    if (lastTaken) {
      const lt = new Date(lastTaken);
      const formatted = lt.toLocaleString();
      lastTakenHtml = `<div class="last-taken">Last taken: ${formatted}</div>`;
    }

    let notesHtml = "";
    if (config.show_notes && stockState?.attributes?.notes) {
      notesHtml = `<div class="notes">${stockState.attributes.notes}</div>`;
    }

    return `
      <div class="med-block" data-base-id="${baseId}">
        <div class="med-header">
          <div class="med-icon" style="background: ${color};">
            <ha-icon icon="${icon}"></ha-icon>
          </div>
          <div>
            <div class="med-name">${this._name || name}</div>
            ${scheduleHtml}
          </div>
        </div>

        ${stockHtml}

        <div class="button-row">
          <button class="btn-take" data-action="take" data-base-id="${baseId}"
            ${!isAvailable ? 'disabled' : ''}>
            <ha-icon icon="mdi:check"></ha-icon>
            Mark Taken
          </button>
          <button class="btn-undo" data-action="undo" data-base-id="${baseId}"
            ${!canUndo ? 'disabled' : ''}>
            <ha-icon icon="mdi:undo"></ha-icon>
            Undo
          </button>
        </div>

        ${lastTakenHtml}
        ${notesHtml}
      </div>
    `;
  }

  _attachListeners() {
    const buttons = this.querySelectorAll("button[data-action]");
    buttons.forEach((btn) => {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", (e) => {
        const action = btn.dataset.action;
        const baseId = btn.dataset.baseId;

        if (action === "take") {
          this._hass.callService("medtrakr", "mark_taken", {
            medication_id: baseId,
          });
        } else if (action === "undo") {
          this._hass.callService("medtrakr", "undo_taken", {
            medication_id: baseId,
          });
        }
      });
    });
  }

  // Card size hint for HA layout
  getCardSize() {
    return 3 + (this._config.show_stock !== false ? 1 : 0);
  }
}

customElements.define("medication-tracker-card", MedicationTrackerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "medication-tracker-card",
  name: "Medication Tracker Card",
  description: "Track medication doses, stock levels, and schedules.",
  preview: true,
});
