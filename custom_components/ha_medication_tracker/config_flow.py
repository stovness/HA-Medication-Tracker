"""Config flow for HA Medication Tracker."""

from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TimeSelector,
    TextSelector,
    TextSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    ColorRGBSelector,
    IconSelector,
)

from .const import (
    CONF_COLOR,
    CONF_DOSAGE,
    CONF_DOSAGE_UNIT,
    CONF_ICON,
    CONF_INITIAL_STOCK,
    CONF_LOW_STOCK_THRESHOLD,
    CONF_LOW_STOCK_UNIT,
    CONF_NAME,
    CONF_NOTES,
    CONF_SCHEDULE,
    CONF_SCHEDULE_TYPE,
    CONF_STOCK_PER_DOSE,
    CONF_SUPPLY_TRACKING,
    CONF_TIMES,
    DAY_NAMES,
    DOMAIN,
    SCHEDULE_TYPE_DAILY,
    SCHEDULE_TYPE_WEEKLY,
)


class MedicationTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for adding medications."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MedicationTrackerOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """First step: basic medication info."""
        errors = {}

        if user_input is not None:
            self._name = user_input[CONF_NAME]
            self._dosage = user_input.get(CONF_DOSAGE, "")
            self._dosage_unit = user_input.get(CONF_DOSAGE_UNIT, "tablet(s)")
            self._notes = user_input.get(CONF_NOTES, "")
            self._icon = user_input.get(CONF_ICON, "mdi:pill")
            self._color = user_input.get(CONF_COLOR, [0, 150, 136])
            return await self.async_step_schedule_type()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=""): TextSelector(
                    TextSelectorConfig()
                ),
                vol.Optional(CONF_DOSAGE, default=""): TextSelector(
                    TextSelectorConfig()
                ),
                vol.Optional(CONF_DOSAGE_UNIT, default="tablet(s)"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": "tablet(s)", "label": "Tablet(s)"},
                            {"value": "capsule(s)", "label": "Capsule(s)"},
                            {"value": "ml", "label": "Millilitres (ml)"},
                            {"value": "mg", "label": "Milligrams (mg)"},
                            {"value": "drop(s)", "label": "Drop(s)"},
                            {"value": "puff(s)", "label": "Puff(s)"},
                            {"value": "injection", "label": "Injection"},
                            {"value": "sachet(s)", "label": "Sachet(s)"},
                            {"value": "other", "label": "Other"},
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_ICON, default="mdi:pill"): IconSelector(),
                vol.Optional(CONF_COLOR, default=[0, 150, 136]): ColorRGBSelector(),
                vol.Optional(CONF_NOTES, default=""): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_schedule_type(self, user_input=None):
        """Choose schedule type: daily or weekly."""
        errors = {}

        if user_input is not None:
            self._schedule_type = user_input[CONF_SCHEDULE_TYPE]
            if self._schedule_type == SCHEDULE_TYPE_DAILY:
                return await self.async_step_schedule_daily()
            else:
                return await self.async_step_schedule_weekly()

        schema = vol.Schema(
            {
                vol.Required(CONF_SCHEDULE_TYPE, default=SCHEDULE_TYPE_DAILY): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": SCHEDULE_TYPE_DAILY, "label": "Same times every day"},
                            {"value": SCHEDULE_TYPE_WEEKLY, "label": "Different times per day"},
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="schedule_type", data_schema=schema, errors=errors
        )

    async def async_step_schedule_daily(self, user_input=None):
        """Set the same times every day."""
        errors = {}

        if user_input is not None:
            self._times = user_input.get(CONF_TIMES, ["08:00"])
            self._schedule = {
                "schedule_type": SCHEDULE_TYPE_DAILY,
                "times": self._times,
            }
            return await self.async_step_supply()

        schema = vol.Schema(
            {
                vol.Required(CONF_TIMES, default=["08:00"]): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": "06:00", "label": "06:00"},
                            {"value": "06:30", "label": "06:30"},
                            {"value": "07:00", "label": "07:00"},
                            {"value": "07:30", "label": "07:30"},
                            {"value": "08:00", "label": "08:00"},
                            {"value": "08:30", "label": "08:30"},
                            {"value": "09:00", "label": "09:00"},
                            {"value": "10:00", "label": "10:00"},
                            {"value": "12:00", "label": "12:00 (noon)"},
                            {"value": "14:00", "label": "14:00"},
                            {"value": "16:00", "label": "16:00"},
                            {"value": "18:00", "label": "18:00"},
                            {"value": "20:00", "label": "20:00"},
                            {"value": "21:00", "label": "21:00"},
                            {"value": "22:00", "label": "22:00"},
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="schedule_daily", data_schema=schema, errors=errors
        )

    async def async_step_schedule_weekly(self, user_input=None):
        """Set per-day times."""
        errors = {}

        if user_input is not None:
            self._schedule = {
                "schedule_type": SCHEDULE_TYPE_WEEKLY,
                "days": {},
            }
            for day in DAY_NAMES:
                day_times = user_input.get(day, [])
                if day_times:
                    self._schedule["days"][day] = day_times

            if not self._schedule["days"]:
                errors["base"] = "no_days_selected"
            else:
                return await self.async_step_supply()

        time_options = [
            {"value": "06:00", "label": "06:00"},
            {"value": "06:30", "label": "06:30"},
            {"value": "07:00", "label": "07:00"},
            {"value": "07:30", "label": "07:30"},
            {"value": "08:00", "label": "08:00"},
            {"value": "08:30", "label": "08:30"},
            {"value": "09:00", "label": "09:00"},
            {"value": "10:00", "label": "10:00"},
            {"value": "12:00", "label": "12:00 (noon)"},
            {"value": "14:00", "label": "14:00"},
            {"value": "16:00", "label": "16:00"},
            {"value": "18:00", "label": "18:00"},
            {"value": "20:00", "label": "20:00"},
            {"value": "21:00", "label": "21:00"},
            {"value": "22:00", "label": "22:00"},
        ]

        day_fields = {}
        for day in DAY_NAMES:
            day_fields[vol.Optional(day, default=[])] = SelectSelector(
                SelectSelectorConfig(
                    options=time_options,
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        schema = vol.Schema(day_fields)

        return self.async_show_form(
            step_id="schedule_weekly", data_schema=schema, errors=errors
        )

    async def async_step_supply(self, user_input=None):
        """Configure supply tracking."""
        errors = {}

        if user_input is not None:
            self._supply_tracking = user_input.get(CONF_SUPPLY_TRACKING, True)

            if self._supply_tracking:
                self._initial_stock = user_input.get(CONF_INITIAL_STOCK, 30)
                self._stock_per_dose = user_input.get(CONF_STOCK_PER_DOSE, 1)
                self._low_stock_threshold = user_input.get(CONF_LOW_STOCK_THRESHOLD, 7)
                self._low_stock_unit = user_input.get(CONF_LOW_STOCK_UNIT, "days")
            else:
                self._initial_stock = 0
                self._stock_per_dose = 0
                self._low_stock_threshold = 0
                self._low_stock_unit = "days"

            return await self._create_entry()

        schema = vol.Schema(
            {
                vol.Optional(CONF_SUPPLY_TRACKING, default=True): bool,
                vol.Optional(CONF_INITIAL_STOCK, default=30): NumberSelector(
                    NumberSelectorConfig(min=0, max=9999, step=1, mode="box")
                ),
                vol.Optional(CONF_STOCK_PER_DOSE, default=1): NumberSelector(
                    NumberSelectorConfig(min=1, max=100, step=1, mode="box")
                ),
                vol.Optional(CONF_LOW_STOCK_THRESHOLD, default=7): NumberSelector(
                    NumberSelectorConfig(min=1, max=365, step=1, mode="box")
                ),
                vol.Optional(CONF_LOW_STOCK_UNIT, default="days"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            {"value": "days", "label": "Days remaining"},
                            {"value": "doses", "label": "Doses remaining"},
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="supply", data_schema=schema, errors=errors
        )

    async def _create_entry(self):
        """Finalize and create the config entry."""
        med_id = uuid.uuid4().hex[:12]

        data = {
            "medication_id": med_id,
            CONF_NAME: self._name,
            CONF_DOSAGE: self._dosage,
            CONF_DOSAGE_UNIT: self._dosage_unit,
            CONF_SCHEDULE: self._schedule,
            CONF_ICON: self._icon,
            CONF_COLOR: self._color,
            CONF_NOTES: self._notes,
            CONF_SUPPLY_TRACKING: self._supply_tracking,
            CONF_INITIAL_STOCK: self._initial_stock,
            CONF_STOCK_PER_DOSE: self._stock_per_dose,
            CONF_LOW_STOCK_THRESHOLD: self._low_stock_threshold,
            CONF_LOW_STOCK_UNIT: self._low_stock_unit,
            "current_stock": self._initial_stock,
        }

        title = self._name if self._dosage else self._name
        if self._dosage and self._dosage_unit:
            title = f"{self._name} ({self._dosage} {self._dosage_unit})"

        return self.async_create_entry(title=title, data=data)


class MedicationTrackerOptionsFlow(config_entries.OptionsFlow):
    """Options flow to edit an existing medication."""

    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage medication options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        data = self.config_entry.data
        schema = vol.Schema(
            {
                vol.Optional(CONF_DOSAGE, default=data.get(CONF_DOSAGE, "")): TextSelector(
                    TextSelectorConfig()
                ),
                vol.Optional(CONF_NOTES, default=data.get(CONF_NOTES, "")): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
