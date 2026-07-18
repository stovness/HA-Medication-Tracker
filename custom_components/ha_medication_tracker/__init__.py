"""HA Medication Tracker - Main integration module."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    ATTR_MEDICATION_ID,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_STOCK,
    SERVICE_MARK_TAKEN,
    SERVICE_SET_STOCK,
    SERVICE_UNDO_TAKEN,
)
from .store import MedicationStore

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register static paths for Lovelace card."""
    www_path = Path(__file__).parent / "www"
    if www_path.is_dir():
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/ha_medication_tracker",
                str(www_path),
                cache_headers=True,
            ),
        ])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Medication Tracker from a config entry."""
    store = MedicationStore(hass)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = store
        await store.async_load()

    data = dict(entry.data)
    med_id = data["medication_id"]

    await store.async_add_medication(med_id, data)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        store = hass.data.get(DOMAIN)
        if store:
            med_id = entry.data.get("medication_id")
            if med_id:
                await store.async_remove_medication(med_id)

    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    """Register medication services."""

    async def _mark_taken(call: ServiceCall) -> None:
        """Mark a dose as taken by medication ID."""
        med_id = call.data.get(ATTR_MEDICATION_ID)
        store = hass.data[DOMAIN]
        medication = store.get_medication(med_id)
        if not medication:
            _LOGGER.warning("Medication %s not found", med_id)
            return

        await store.async_record_dose(med_id)

        if medication.get("supply_tracking", False):
            stock_per_dose = medication.get("stock_per_dose", 1)
            await store.async_adjust_stock(med_id, -stock_per_dose)

    async def _undo_taken(call: ServiceCall) -> None:
        """Undo the last taken dose by medication ID."""
        med_id = call.data.get(ATTR_MEDICATION_ID)
        store = hass.data[DOMAIN]
        medication = store.get_medication(med_id)
        if not medication:
            _LOGGER.warning("Medication %s not found", med_id)
            return

        removed = await store.async_undo_last_dose(med_id)
        if removed and medication.get("supply_tracking", False):
            stock_per_dose = medication.get("stock_per_dose", 1)
            await store.async_adjust_stock(med_id, stock_per_dose)

    async def _add_stock(call: ServiceCall) -> None:
        """Add stock to a medication."""
        med_id = call.data.get(ATTR_MEDICATION_ID)
        amount = call.data.get("amount", 1)
        store = hass.data[DOMAIN]
        await store.async_adjust_stock(med_id, amount)

    async def _set_stock(call: ServiceCall) -> None:
        """Set absolute stock level."""
        med_id = call.data.get(ATTR_MEDICATION_ID)
        amount = call.data.get("amount", 0)
        store = hass.data[DOMAIN]
        await store.async_set_stock(med_id, amount)

    if not hass.services.has_service(DOMAIN, SERVICE_MARK_TAKEN):
        hass.services.async_register(DOMAIN, SERVICE_MARK_TAKEN, _mark_taken)
        hass.services.async_register(DOMAIN, SERVICE_UNDO_TAKEN, _undo_taken)
        hass.services.async_register(DOMAIN, SERVICE_ADD_STOCK, _add_stock)
        hass.services.async_register(DOMAIN, SERVICE_SET_STOCK, _set_stock)
