"""HA Medication Tracker - Main integration module."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigEntry
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

WWW_SOURCE = Path(__file__).parent / "www"
WWW_DEST_DIR = "community/ha_medication_tracker"
PANEL_URL = "/ha-medication-tracker"
PANEL_TITLE = "Medication Tracker"
PANEL_ICON = "mdi:pill"
_FRONTEND_DEPLOYED = False
_PANEL_REGISTERED = False


async def _deploy_frontend(hass: HomeAssistant) -> None:
    """Copy frontend assets to /config/www/ so they're served at /local/.

    Idempotent - only runs once per HA start.
    """
    global _FRONTEND_DEPLOYED
    if _FRONTEND_DEPLOYED:
        return

    if not WWW_SOURCE.is_dir():
        return

    dest_dir = Path(hass.config.path("www")) / WWW_DEST_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    for src_file in WWW_SOURCE.glob("*.*"):
        dest_file = dest_dir / src_file.name
        if not dest_file.exists() or src_file.stat().st_mtime > dest_file.stat().st_mtime:
            shutil.copy2(src_file, dest_file)
            dest_file.chmod(0o644)
            _LOGGER.info("Deployed %s to %s", src_file.name, dest_file)

    _FRONTEND_DEPLOYED = True


async def _register_panel(hass: HomeAssistant) -> None:
    """Register the management panel in the sidebar.

    Idempotent - panel is only registered once.
    """
    global _PANEL_REGISTERED
    if _PANEL_REGISTERED:
        return

    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        config={"url": f"/local/{WWW_DEST_DIR}/panel.html?v=1.0.0"},
        require_admin=False,
    )

    _LOGGER.info("Registered Medication Tracker sidebar panel")
    _PANEL_REGISTERED = True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Deploy frontend and register panel on integration discovery."""
    await _deploy_frontend(hass)
    await _register_panel(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Medication Tracker from a config entry."""
    if DOMAIN not in hass.data:
        store = MedicationStore(hass)
        await store.async_load()
        hass.data[DOMAIN] = store

    store = hass.data[DOMAIN]
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
        med_id = call.data.get(ATTR_MEDICATION_ID)
        amount = call.data.get("amount", 1)
        await hass.data[DOMAIN].async_adjust_stock(med_id, amount)

    async def _set_stock(call: ServiceCall) -> None:
        med_id = call.data.get(ATTR_MEDICATION_ID)
        amount = call.data.get("amount", 0)
        await hass.data[DOMAIN].async_set_stock(med_id, amount)

    if not hass.services.has_service(DOMAIN, SERVICE_MARK_TAKEN):
        hass.services.async_register(DOMAIN, SERVICE_MARK_TAKEN, _mark_taken)
        hass.services.async_register(DOMAIN, SERVICE_UNDO_TAKEN, _undo_taken)
        hass.services.async_register(DOMAIN, SERVICE_ADD_STOCK, _add_stock)
        hass.services.async_register(DOMAIN, SERVICE_SET_STOCK, _set_stock)
