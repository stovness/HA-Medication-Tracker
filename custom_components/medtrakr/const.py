"""Constants for MedTrakr."""

DOMAIN = "medtrakr"
PLATFORMS = ["calendar", "sensor", "button"]

CONF_MEDICATIONS = "medications"
CONF_NAME = "name"
CONF_DOSAGE = "dosage"
CONF_DOSAGE_UNIT = "dosage_unit"
CONF_SCHEDULE = "schedule"
CONF_SCHEDULE_TYPE = "schedule_type"
CONF_TIMES = "times"
CONF_DAYS = "days"
CONF_SUPPLY_TRACKING = "supply_tracking"
CONF_INITIAL_STOCK = "initial_stock"
CONF_STOCK_PER_DOSE = "stock_per_dose"
CONF_LOW_STOCK_THRESHOLD = "low_stock_threshold"
CONF_LOW_STOCK_UNIT = "low_stock_unit"
CONF_NOTES = "notes"
CONF_COLOR = "color"
CONF_ICON = "icon"

SCHEDULE_TYPE_DAILY = "daily"
SCHEDULE_TYPE_WEEKLY = "weekly"

DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

ATTR_MEDICATION_ID = "medication_id"
ATTR_LAST_TAKEN = "last_taken"
ATTR_NEXT_DOSE = "next_dose"
ATTR_STOCK_LEVEL = "stock_level"
ATTR_DAYS_REMAINING = "days_remaining"
ATTR_DOSES_REMAINING = "doses_remaining"
ATTR_LOW_STOCK = "low_stock"
ATTR_DOSAGE = "dosage"
ATTR_SCHEDULE = "schedule"
ATTR_HISTORY = "history"

SERVICE_MARK_TAKEN = "mark_taken"
SERVICE_UNDO_TAKEN = "undo_taken"
SERVICE_ADD_STOCK = "add_stock"
SERVICE_SET_STOCK = "set_stock"

STORAGE_VERSION = 1
STORAGE_KEY = "medtrakr_data"
