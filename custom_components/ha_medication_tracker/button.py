"""Button entities for taking and undoing medication doses."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .device import build_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up medication button entities."""
    store = hass.data[DOMAIN]
    data = config_entry.data
    med_id = data["medication_id"]

    entities = [
        MedicationTakeButton(store, config_entry, med_id),
        MedicationUndoButton(store, config_entry, med_id),
    ]
    async_add_entities(entities)


class MedicationTakeButton(ButtonEntity):
    """Button to mark a dose as taken."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, store, config_entry, med_id: str) -> None:
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_take"
        self._attr_device_info = build_device_info(config_entry, config_entry.data["name"], med_id)

    @property
    def name(self) -> str:
        return f"{self._config_entry.data['name']} Take"

    async def async_press(self) -> None:
        """Handle button press: mark dose as taken."""
        data = self._config_entry.data

        await self._store.async_record_dose(self._med_id)

        if data.get("supply_tracking", False):
            stock_per_dose = data.get("stock_per_dose", 1)
            await self._store.async_adjust_stock(self._med_id, -stock_per_dose)


class MedicationUndoButton(ButtonEntity):
    """Button to undo the last taken dose."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:undo-variant"

    def __init__(self, store, config_entry, med_id: str) -> None:
        self._store = store
        self._config_entry = config_entry
        self._med_id = med_id
        self._attr_unique_id = f"{med_id}_undo"
        self._attr_device_info = build_device_info(config_entry, config_entry.data["name"], med_id)

    @property
    def name(self) -> str:
        return f"{self._config_entry.data['name']} Undo"

    async def async_press(self) -> None:
        """Handle button press: undo last dose."""
        data = self._config_entry.data
        removed = await self._store.async_undo_last_dose(self._med_id)

        if removed and data.get("supply_tracking", False):
            stock_per_dose = data.get("stock_per_dose", 1)
            await self._store.async_adjust_stock(self._med_id, stock_per_dose)
