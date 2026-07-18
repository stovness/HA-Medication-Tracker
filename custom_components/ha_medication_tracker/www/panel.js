/**
 * HA Medication Tracker - Management Panel
 *
 * Full-page sidebar panel for managing medications.
 * Registered at /local/community/ha_medication_tracker/panel.js
 */

class MedicationTrackerPanel extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._build();
    }
    this._render();
  }

  set panel(panel) {
    this._panel = panel;
  }

  _build() {
    this._rendered = true;
    this.innerHTML = `
      <style>
        :host {
          display: block;
          height: 100%;
          overflow-y: auto;
          background: var(--primary-background-color, #fafafa);
        }
        .panel-container {
          max-width: 960px;
          margin: 0 auto;
          padding: 24px 16px;
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          flex-wrap: wrap;
          gap: 12px;
        }
        .panel-title {
          font-size: 1.6em;
          font-weight: 600;
          color: var(--primary-text-color);
        }
        .btn-add {
          background: var(--primary-color, #03a9f4);
          color: white;
          border: none;
          border-radius: 8px;
          padding: 10px 20px;
          font-size: 0.95em;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
        }
        .btn-add:hover { opacity: 0.9; }

        .med-card {
          background: var(--card-background-color, white);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 16px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }
        .med-card-header {
          display: flex;
          align-items: center;
          gap: 14px;
          margin-bottom: 14px;
        }
        .med-icon-circle {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;
          flex-shrink: 0;
        }
        .med-info { flex: 1; }
        .med-name {
          font-size: 1.15em;
          font-weight: 600;
          color: var(--primary-text-color);
        }
        .med-dosage {
          font-size: 0.85em;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }
        .med-schedule {
          font-size: 0.8em;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }

        .stock-bar {
          display: flex;
          gap: 12px;
          margin-bottom: 12px;
          flex-wrap: wrap;
        }
        .stock-item {
          flex: 1;
          min-width: 100px;
          background: var(--primary-background-color, #f5f5f5);
          border-radius: 8px;
          padding: 12px;
          text-align: center;
        }
        .stock-value {
          font-size: 1.4em;
          font-weight: 700;
        }
        .stock-label {
          font-size: 0.75em;
          color: var(--secondary-text-color);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .stock-low .stock-value { color: var(--error-color, #e53935); }
        .stock-warn .stock-value { color: var(--warning-color, #ff9800); }
        .stock-ok .stock-value { color: var(--success-color, #43a047); }

        .action-row {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }
        .btn {
          border: none;
          border-radius: 8px;
          padding: 10px 18px;
          font-size: 0.9em;
          cursor: pointer;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: opacity 0.15s;
        }
        .btn:hover { opacity: 0.85; }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .btn-take { background: #43a047; color: white; }
        .btn-undo { background: #ff9800; color: white; }
        .btn-delete { background: transparent; color: var(--error-color); border: 1px solid var(--error-color); }

        .last-taken {
          font-size: 0.8em;
          color: var(--secondary-text-color);
          margin-top: 10px;
        }
        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: var(--secondary-text-color);
        }
        .empty-state ha-icon {
          display: block;
          margin-bottom: 16px;
        }
        .empty-state h3 {
          font-size: 1.2em;
          margin-bottom: 8px;
        }
        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 20px;
          border-bottom: 2px solid var(--divider-color, #e0e0e0);
        }
        .tab {
          padding: 10px 20px;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
          font-weight: 500;
          color: var(--secondary-text-color);
          background: none;
          border-top: none;
          border-left: none;
          border-right: none;
          font-size: 0.95em;
        }
        .tab.active {
          color: var(--primary-color);
          border-bottom-color: var(--primary-color);
        }
        .med-notes {
          font-size: 0.8em;
          color: var(--secondary-text-color);
          margin-top: 8px;
          font-style: italic;
        }
      </style>
      <div class="panel-container" id="panel-content"></div>
    `;
  }

  _render() {
    const content = this.querySelector("#panel-content");
    if (!content || !this._hass) return;

    const domain = "ha_medication_tracker";
    const hass = this._hass;

    // Find all medication sensors
    const stockEntities = Object.keys(hass.states).filter(
      (eid) => eid.startsWith("sensor.") && eid.endsWith("_stock")
    );

    if (stockEntities.length === 0) {
      content.innerHTML = `
        <div class="panel-header">
          <div class="panel-title">Medication Tracker</div>
        </div>
        <div class="empty-state">
          <ha-icon icon="mdi:pill" style="font-size: 64px; color: var(--secondary-text-color);"></ha-icon>
          <h3>No Medications Yet</h3>
          <p>Add your first medication to start tracking doses, schedules, and stock levels.</p>
          <br/>
          <button class="btn-add" onclick="document.querySelector('medication-tracker-panel')._startConfigFlow()">
            <ha-icon icon="mdi:plus"></ha-icon>
            Add Medication
          </button>
        </div>
      `;
      return;
    }

    let html = `
      <div class="panel-header">
        <div class="panel-title">Medication Tracker</div>
        <button class="btn-add" id="add-med-btn">
          <ha-icon icon="mdi:plus"></ha-icon>
          Add Medication
        </button>
      </div>
    `;

    for (const entityId of stockEntities) {
      const state = hass.states[entityId];
      if (!state) continue;

      const baseId = entityId.replace("sensor.", "").replace("_stock", "");
      const daysEntity = `sensor.${baseId}_days_remaining`;
      const nextDoseEntity = `sensor.${baseId}_next_dose`;
      const takeButton = `button.${baseId}_take`;
      const undoButton = `button.${baseId}_undo`;

      const name = state.attributes?.friendly_name?.replace(" Stock", "") || baseId;
      const stock = state.state || "0";
      const unit = state.attributes?.unit_of_measurement || "";
      const isLow = state.attributes?.low_stock || false;
      const lastTaken = state.attributes?.last_taken;
      const color = state.attributes?.color || "#009688";
      const icon = "mdi:pill";

      const daysState = hass.states[daysEntity];
      const daysRemaining = daysState ? daysState.state : null;

      const nextState = hass.states[nextDoseEntity];
      const schedule = nextState?.attributes?.schedule || "";
      const takenToday = nextState?.attributes?.taken_today || 0;

      const takeState = hass.states[takeButton];
      const undoState = hass.states[undoButton];
      const canTake = takeState?.state !== "unavailable";
      const canUndo = undoState?.state !== "unavailable";

      // Stock level class
      let stockClass = "stock-ok";
      if (isLow) stockClass = "stock-low";
      else if (daysRemaining && parseFloat(daysRemaining) < 14) stockClass = "stock-warn";

      let lastTakenHtml = "";
      if (lastTaken) {
        try {
          const lt = new Date(lastTaken);
          lastTakenHtml = `<div class="last-taken">Last taken: ${lt.toLocaleString()}</div>`;
        } catch (e) {}
      }

      html += `
        <div class="med-card">
          <div class="med-card-header">
            <div class="med-icon-circle" style="background: ${color};">
              <ha-icon icon="${icon}"></ha-icon>
            </div>
            <div class="med-info">
              <div class="med-name">${name}</div>
              ${schedule ? `<div class="med-schedule">${schedule}</div>` : ""}
            </div>
          </div>

          <div class="stock-bar">
            <div class="stock-item ${stockClass}">
              <div class="stock-value">${stock}</div>
              <div class="stock-label">${unit || "Stock"}</div>
            </div>
            ${daysRemaining ? `
            <div class="stock-item">
              <div class="stock-value">~${daysRemaining}</div>
              <div class="stock-label">Days Left</div>
            </div>` : ""}
            <div class="stock-item">
              <div class="stock-value">${takenToday}</div>
              <div class="stock-label">Taken Today</div>
            </div>
          </div>

          <div class="action-row">
            <button class="btn btn-take" data-action="take" data-base="${baseId}" ${canTake ? "" : "disabled"}>
              Mark Taken
            </button>
            <button class="btn btn-undo" data-action="undo" data-base="${baseId}" ${canUndo ? "" : "disabled"}>
              Undo
            </button>
          </div>
          ${lastTakenHtml}
        </div>
      `;
    }

    content.innerHTML = html;

    // Attach event listeners
    this._attachListeners(content);
  }

  _attachListeners(root) {
    // Take/Undo buttons
    root.querySelectorAll("button[data-action]").forEach((btn) => {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        const baseId = btn.dataset.base;
        if (action === "take") {
          this._hass.callService("ha_medication_tracker", "mark_taken", {
            medication_id: baseId,
          });
        } else if (action === "undo") {
          this._hass.callService("ha_medication_tracker", "undo_taken", {
            medication_id: baseId,
          });
        }
      });
    });

    // Add Medication button
    const addBtn = root.querySelector("#add-med-btn");
    if (addBtn && !addBtn._bound) {
      addBtn._bound = true;
      addBtn.addEventListener("click", () => this._startConfigFlow());
    }
  }

  _startConfigFlow() {
    // Navigate to the HA-Medication-Tracker config flow wizard
    // This opens the "Add Medication" setup directly
    window.location.href = "/config/integrations/integration/ha_medication_tracker";
  }
}

customElements.define("medication-tracker-panel", MedicationTrackerPanel);
