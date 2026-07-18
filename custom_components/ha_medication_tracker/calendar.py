"""Calendar entities showing taken medication doses as history events."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from .const import DOMAIN


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
    store = hass.data[DOMAIN]
    med_id = config_entry.data["medication_id"]
    entity = MedicationCalendarEntity(store, config_entry, med_id)
    entity.update()
    async_add_entities([entity])


class MedicationCalendarEntity(CalendarEntity):
    """Calendar entity showing taken medication doses as events.

    Only shows doses that have actually been taken (via Mark Taken).
    No predicted/scheduled events - just real history.
    """

    _attr_has_entity_name = True

    def __init__(self, store, config_entry, med_id: str) -> None:
        """Initialize the calendar."""
        super().__init__()
        self._store = store
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

    @property
    def event(self) -> CalendarEvent | None:
        """Return the most recent taken dose."""
        return self._attr_event

    def update(self) -> None:
        """Update the calendar with the most recent taken dose."""
        data = self._config_entry.data
        name = data["name"]
        dosage = data.get("dosage", "")
        dosage_unit = data.get("dosage_unit", "")
        desc = f"{dosage} {dosage_unit}".strip()

        last_taken = self._store.get_last_taken(self._med_id)

        if last_taken is None:
            self._attr_event = None
            return

        last_taken = _ensure_tz(last_taken)

        self._attr_event = CalendarEvent(
            start=last_taken,
            end=last_taken + timedelta(minutes=5),
            summary=f"Took {name}",
            description=desc if desc else None,
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return taken dose events within a date range."""
        data = self._config_entry.data
        name = data["name"]
        dosage = data.get("dosage", "")
        dosage_unit = data.get("dosage_unit", "")
        desc = f"{dosage} {dosage_unit}".strip()

        history = self._store.get_history(self._med_id)
        events = []

        for entry in history:
            if entry.get("action") != "taken":
                continue

            ts = datetime.fromisoformat(entry["timestamp"])
            ts = _ensure_tz(ts)

            if start_date <= ts <= end_date:
                events.append(
                    CalendarEvent(
                        start=ts,
                        end=ts + timedelta(minutes=5),
                        summary=f"Took {name}",
                        description=desc if desc else None,
                    )
                )

        return events

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra attributes."""
        data = self._config_entry.data
        return {
            "medication_id": self._med_id,
            "dosage": data.get("dosage", ""),
            "dosage_unit": data.get("dosage_unit", ""),
            "total_taken": len([e for e in self._store.get_history(self._med_id) if e.get("action") == "taken"]),
        }
