"""Sensor entities for medication tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.config_entries import ConfigEntry

from .const import (
    ATTR_DAYS_REMAINING,
    ATTR_DOSES_REMAINING,
    ATTR_HISTORY,
    ATTR_LAST_TAKEN,
    ATTR_LOW_STOCK,
    ATTR_NEXT_DOSE,
    ATTR_SCHEDULE,
    ATTR_STOCK_LEVEL,
    DOMAIN,
)
from .schedule import get_next_dose_time, get_schedule_summary

SCAN_INTERVAL = 60  # seconds


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up medication sensor entities."""
    store = hass.data[DOMAIN]
    data = config_entry.data
    med_id = data["medication_id"]

    entities = [
        MedicationStockSensor(store, config_entry, med_id),
    ]

    if data.get("supply_tracking", False):
        entities.append(MedicationDaysRemainingSensor(store, config_entry, med_id))

    entities.append(MedicationNextDoseSensor(store, config_entry, med_id))

    async_add_entities(entities)


class MedicationStockSensor(SensorEntity):
    """Sensor showing current stock level."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "units"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, store, config_entry, med_id: str) -> None:
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        unit = config_entry.data.get("dosage_unit", "tablet(s)")
        self._attr_unique_id = f"{med_id}_stock"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = "mdi:counter"

    @property
    def name(self) -> str:
        return f"{self._config_entry.data['name']} Stock"

    @property
    def native_value(self) -> int:
        return self._store.get_stock(self._med_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._config_entry.data
        last_taken = self._store.get_last_taken(self._med_id)
        history = self._store.get_history(self._med_id)

        attrs: dict[str, Any] = {
            ATTR_LAST_TAKEN: last_taken.isoformat() if last_taken else None,
            ATTR_LOW_STOCK: self._is_low_stock(),
        }

        return attrs

    def _is_low_stock(self) -> bool:
        data = self._config_entry.data
        if not data.get("supply_tracking", False):
            return False

        threshold = data.get("low_stock_threshold", 0)
        threshold_unit = data.get("low_stock_unit", "days")
        stock = self._store.get_stock(self._med_id)

        if threshold_unit == "doses":
            return stock <= threshold

        stock_per_dose = data.get("stock_per_dose", 1)
        if stock_per_dose == 0:
            return False
        doses_remaining = stock / stock_per_dose
        doses_per_day = self._doses_per_day()
        if doses_per_day == 0:
            return False
        days_remaining = doses_remaining / doses_per_day
        return days_remaining <= threshold

    def _doses_per_day(self) -> float:
        data = self._config_entry.data
        schedule = data.get("schedule", {})
        schedule_type = schedule.get("schedule_type", "daily")

        if schedule_type == "daily":
            return len(schedule.get("times", []))
        else:
            days_data = schedule.get("days", {})
            total_doses = sum(len(t) for t in days_data.values())
            active_days = len([d for d in days_data if days_data[d]])
            if active_days == 0:
                return 0
            return total_doses / 7


class MedicationDaysRemainingSensor(SensorEntity):
    """Sensor showing estimated days of supply remaining."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, store, config_entry, med_id: str) -> None:
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_days_remaining"

    @property
    def name(self) -> str:
        return f"{self._config_entry.data['name']} Days Remaining"

    @property
    def native_value(self) -> float | None:
        data = self._config_entry.data
        stock = self._store.get_stock(self._med_id)
        stock_per_dose = data.get("stock_per_dose", 1)
        if stock_per_dose == 0:
            return None

        doses_remaining = stock / stock_per_dose

        schedule = data.get("schedule", {})
        schedule_type = schedule.get("schedule_type", "daily")
        if schedule_type == "daily":
            doses_per_day = len(schedule.get("times", []))
        else:
            days_data = schedule.get("days", {})
            total = sum(len(t) for t in days_data.values())
            doses_per_day = total / 7 if total else 0

        if doses_per_day == 0:
            return None

        return round(doses_remaining / doses_per_day, 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._config_entry.data
        stock = self._store.get_stock(self._med_id)
        stock_per_dose = data.get("stock_per_dose", 1)
        doses_remaining = stock / stock_per_dose if stock_per_dose else 0
        return {
            ATTR_DOSES_REMAINING: int(doses_remaining),
            "low_stock_threshold": data.get("low_stock_threshold", 0),
            "low_stock_unit": data.get("low_stock_unit", "days"),
        }


class MedicationNextDoseSensor(SensorEntity):
    """Sensor showing next dose time."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alarm"

    def __init__(self, store, config_entry, med_id: str) -> None:
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_next_dose"

    @property
    def name(self) -> str:
        return f"{self._config_entry.data['name']} Next Dose"

    @property
    def native_value(self) -> str | None:
        schedule = self._config_entry.data.get("schedule", {})
        next_dose = get_next_dose_time(schedule)
        return next_dose.isoformat() if next_dose else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._config_entry.data
        schedule = data.get("schedule", {})
        return {
            ATTR_SCHEDULE: get_schedule_summary(schedule),
            "taken_today": self._store.get_taken_today(self._med_id),
        }
