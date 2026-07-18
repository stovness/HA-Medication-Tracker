"""Calendar entities for medication schedules."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .schedule import get_next_dose_time, get_todays_doses, get_schedule_summary


def _ensure_tz(dt_value: datetime) -> datetime:
    """Ensure a datetime is timezone-aware using HA's timezone."""
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return dt_value


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up medication calendar entities."""
    med_id = config_entry.data["medication_id"]
    entity = MedicationCalendarEntity(config_entry, med_id)
    entity.update()
    async_add_entities([entity])


class MedicationCalendarEntity(CalendarEntity):
    """Calendar entity showing medication schedule."""

    _attr_has_entity_name = True

    def __init__(self, config_entry, med_id: str) -> None:
        """Initialize the calendar."""
        super().__init__()
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_calendar"
        self._attr_event = None

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
        now = dt_util.now()
        next_dose = get_next_dose_time(schedule, now)

        if next_dose is None:
            self._attr_event = None
            return

        next_dose = _ensure_tz(next_dose)
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
                event_dt = _ensure_tz(event_dt)
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
