"""Shared device info and entity helpers for medication entities."""

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def build_device_info(config_entry, name: str, med_id: str) -> DeviceInfo:
    """Build DeviceInfo for a medication, grouping all its entities under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, med_id)},
        name=f"Medication: {name}",
        manufacturer="HA Medication Tracker",
        model=config_entry.data.get("dosage", "") or "Medication",
        configuration_url="/ha-medication-tracker",
        suggested_area="Medicine Cabinet",
    )
