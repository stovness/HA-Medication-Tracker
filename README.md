# HA Medication Tracker

[![GitHub Release](https://img.shields.io/github/v/release/stovness/HA-Medication-Tracker?style=flat-square)](https://github.com/stovness/HA-Medication-Tracker/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

A complete Home Assistant custom integration for medication tracking. Schedule doses, sync to your calendar, track supply levels, and get restock reminders, all with a polished Lovelace card.

## Features

- **Schedule Management**: Set daily or per-day-of-week medication times
- **Calendar Sync**: Medication doses appear as events in your HA calendar
- **One-Tap Tracking**: Mark doses as taken with a button press
- **Undo Support**: Undo a mistakenly recorded dose
- **Supply Tracking**: Track stock levels, doses remaining, and estimated days of supply
- **Low Stock Alerts**: Configurable threshold alerts (by days or doses remaining)
- **Services**: Full automation support via `mark_taken`, `undo_taken`, `add_stock`, `set_stock`
- **Lovelace Card**: Beautiful custom UI card with colour-coded status and quick actions
- **HACS Ready**: Install directly via HACS custom repositories

## How It's Different

Existing medication trackers are good but each misses something:

| Feature | HA Medication Tracker | ha-medication-reminder | medication_tracker |
|---|---|---|---|
| Calendar integration | Yes | No | No |
| Per-day scheduling | Yes | Yes | No |
| Supply tracking | Yes | Yes | Yes |
| Undo taken dose | Yes | Partial | No |
| Custom Lovelace card | Yes | Dashboards only | Mushroom templates |
| Services for automation | Yes | Yes | Yes |
| UI config flow | Yes | Yes | Yes |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots (top right) > **Custom repositories**
3. Paste: `https://github.com/stovness/HA-Medication-Tracker`
4. Category: **Integration**
5. Click **Add**, then find "HA Medication Tracker" and install it
6. Restart Home Assistant

### Manual

```bash
cd /path/to/your/config
git clone https://github.com/stovness/HA-Medication-Tracker.git
cp -r HA-Medication-Tracker/custom_components/ha_medication_tracker custom_components/
```

Then restart Home Assistant.

### Lovelace Card (Optional)

The card is served automatically by the integration. No manual file copying needed.

1. Go to **Settings > Dashboards > three dots > Resources**
2. Click **Add Resource**
3. URL: `/local/ha_medication_tracker/medication-tracker-card.js`
4. Resource type: **JavaScript Module**

> The integration registers this path automatically on startup. If the resource 404s, restart Home Assistant once after installing the integration.

## Configuration

### Adding a Medication

1. Go to **Settings > Devices & Services**
2. Click **Add Integration** and search for "HA Medication Tracker"
3. Follow the setup wizard:

**Step 1 - Medication Info:**
- Medication name (e.g. "Metformin", "Ibuprofen")
- Dosage (e.g. "500mg", "2 tablets")
- Dosage unit (tablets, capsules, ml, etc.)
- Icon and colour for the dashboard
- Optional notes

**Step 2 - Schedule Type:**
- **Same times every day**: Quick setup for daily medications
- **Different times per day**: Set unique times for Monday through Sunday

**Step 3 - Times:**
- Select one or more times per day (daily mode)
- Or pick times per specific day (weekly mode)

**Step 4 - Supply Tracking:**
- Initial stock level
- Units consumed per dose
- Low stock threshold (in days or doses)

### Dashboard Card

Add this to any Lovelace dashboard:

```yaml
type: custom:medication-tracker-card
entity: sensor.your_medication_stock
```

Or track multiple medications:

```yaml
type: custom:medication-tracker-card
entities:
  - sensor.metformin_stock
  - sensor.ibuprofen_stock
name: Today's Medications
show_stock: true
show_schedule: true
```

#### Card Options

| Option | Type | Default | Description |
|---|---|---|---|
| `entity` | string | required | The stock entity ID for a single medication |
| `entities` | list | required | List of entities for multiple medications |
| `name` | string | "" | Card title override |
| `show_stock` | boolean | true | Show stock level and days remaining |
| `show_schedule` | boolean | true | Show schedule summary |
| `show_notes` | boolean | false | Show medication notes |

### YAML Dashboard Example (No Custom Card Needed)

If you prefer a pure YAML setup, you can use built-in cards with button entities:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Metformin
    entities:
      - entity: sensor.metformin_stock
        name: Stock
      - entity: sensor.metformin_days_remaining
        name: Days Remaining
      - entity: sensor.metformin_next_dose
        name: Next Dose

  - type: horizontal-stack
    cards:
      - type: button
        entity: button.metformin_take
        name: Mark Taken
        icon: mdi:check-circle
        icon_height: 24px
        show_state: false
        tap_action:
          action: call-service
          service: ha_medication_tracker.mark_taken
          service_data:
            medication_id: "your_medication_id"

      - type: button
        entity: button.metformin_undo
        name: Undo
        icon: mdi:undo
        icon_height: 24px
        show_state: false
        tap_action:
          action: call-service
          service: ha_medication_tracker.undo_taken
          service_data:
            medication_id: "your_medication_id"
```

## Automations

### Medication Reminder

Use the calendar entity to trigger reminders:

```yaml
alias: Medication Reminder
trigger:
  - platform: calendar
    entity_id: calendar.metformin
    event: start
action:
  - service: notify.mobile_app
    data:
      title: "Time for Medication"
      message: "Take your Metformin now"
```

### Low Stock Alert

```yaml
alias: Low Stock Alert
trigger:
  - platform: numeric_state
    entity_id: sensor.metformin_days_remaining
    below: 7
action:
  - service: notify.mobile_app
    data:
      title: "Low Medication Stock"
      message: "Metformin is running low. Only {{ states('sensor.metformin_days_remaining') }} days remaining."
```

### Daily Summary

```yaml
alias: Daily Medication Summary
trigger:
  - platform: time
    at: "21:00:00"
action:
  - service: notify.mobile_app
    data:
      title: "Medication Summary"
      message: >
        Metformin: {{ states('sensor.metformin_stock') }} tablets left.
        {% if states('sensor.metformin_days_remaining') | float < 7 %}
        ⚠ Running low!
        {% endif %}
```

## Services

| Service | Description | Parameters |
|---|---|---|
| `ha_medication_tracker.mark_taken` | Record a dose as taken | `medication_id` (required) |
| `ha_medication_tracker.undo_taken` | Undo the last taken dose | `medication_id` (required) |
| `ha_medication_tracker.add_stock` | Add to current stock | `medication_id`, `amount` (default: 1) |
| `ha_medication_tracker.set_stock` | Set absolute stock level | `medication_id`, `amount` |

All services decrement/increment stock automatically when supply tracking is enabled.

## Entities Created

For each medication, the integration creates:

| Entity | Type | Purpose |
|---|---|---|
| `calendar.<name>` | Calendar | Scheduled doses as calendar events |
| `sensor.<name>_stock` | Sensor | Current stock level |
| `sensor.<name>_days_remaining` | Sensor | Estimated days of supply (if supply tracking enabled) |
| `sensor.<name>_next_dose` | Sensor | Next scheduled dose datetime |
| `button.<name>_take` | Button | Mark a dose as taken |
| `button.<name>_undo` | Button | Undo the last taken dose |

## Ideas for the Future

- Daily/weekly adherence stats
- Multi-user support (family medications)
- Barcode scanning for stock refills
- Integration with pharmacy APIs
- Voice assistant support ("Hey Home, I took my pills")

## Contributing

Issues and PRs welcome. If you find a bug or have a feature request, open an issue.

## License

MIT © stovness
