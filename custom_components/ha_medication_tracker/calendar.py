"""Calendar entities for medication schedules."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .schedule import get_next_dose_time, get_todays_doses, get_schedule_summary


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up medication calendar entities."""
    store = hass.data[DOMAIN]
    data = config_entry.data
    med_id = data["medication_id"]
    entity = MedicationCalendarEntity(store, config_entry, med_id)
    entity.update()
    async_add_entities([entity])


class MedicationCalendarEntity(CalendarEntity):
    """Calendar entity showing medication schedule."""

    _attr_has_entity_name = True
    _attr_translation_key = "medication_calendar"

    def __init__(self, store, config_entry, med_id: str) -> None:
        """Initialize the calendar."""
        super().__init__()
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_calendar"

    @property
    def name(self) -> str:
        """Calendar name."""
        return self._config_entry.data.get("name", "Medication")

    @property
    def icon(self) -> str:
        """Icon from config."""
        return self._config_entry.data.get("icon", "mdi:pill")

    def update(self) -> None:
        """Update the calendar event."""
        data = self._config_entry.data
        schedule = data.get("schedule", {})
        next_dose = get_next_dose_time(schedule)

        if next_dose is None:
            self._attr_event = None
            return

        dosage = data.get("dosage", "")
        dosage_unit = data.get("dosage_unit", "")
        desc = f"{dosage} {dosage_unit}".strip()

        self._attr_event = CalendarEvent(
            start=next_dose,
            end=next_dose + timedelta(minutes=15),
            summary=f"Take {data['name']}",
            description=desc if desc else None,
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get events within a date range."""
        data = self._config_entry.data
        schedule = data.get("schedule", {})
        dosage = data.get("dosage", "")
        dosage_unit = data.get("dosage_unit", "")
        desc = f"{dosage} {dosage_unit}".strip()
        name = data["name"]
        events = []

        current = start_date
        while current <= end_date:
            day_times = get_todays_doses(schedule, current)
            for t in day_times:
                event_dt = datetime.combine(current.date(), t)
                if start_date <= event_dt <= end_date:
                    events.append(
                        CalendarEvent(
                            start=event_dt,
                            end=event_dt + timedelta(minutes=15),
                            summary=f"Take {name}",
                            description=desc if desc else None,
                        )
                    )
            current += timedelta(days=1)

        return events

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra attributes for the calendar."""
        data = self._config_entry.data
        schedule = data.get("schedule", {})
        return {
            "schedule_type": schedule.get("schedule_type", "daily"),
            "schedule_summary": get_schedule_summary(schedule),
            "medication_id": self._med_id,
        }
