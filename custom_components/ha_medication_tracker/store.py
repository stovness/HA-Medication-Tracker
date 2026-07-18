"""Persistent storage for medication data."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


class MedicationStore:
    """Manage persistent storage for medications and history."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        self._data = stored or {"medications": {}, "history": {}}

    async def _async_save(self) -> None:
        """Persist to disk."""
        await self._store.async_save(self._data)

    # ---------- Medications ----------

    def get_medications(self) -> dict[str, Any]:
        """Return all medications dict keyed by ID."""
        return self._data.get("medications", {})

    def get_medication(self, med_id: str) -> dict[str, Any] | None:
        """Return a single medication or None."""
        return self._data.get("medications", {}).get(med_id)

    async def async_add_medication(self, med_id: str, config: dict[str, Any]) -> None:
        """Add or update a medication."""
        async with self._lock:
            self._data.setdefault("medications", {})[med_id] = config
            self._data.setdefault("history", {}).setdefault(med_id, [])
            await self._async_save()

    async def async_update_medication(self, med_id: str, updates: dict[str, Any]) -> None:
        """Update fields on a medication."""
        async with self._lock:
            if med_id in self._data.get("medications", {}):
                self._data["medications"][med_id].update(updates)
                await self._async_save()

    async def async_remove_medication(self, med_id: str) -> None:
        """Remove a medication and its history."""
        async with self._lock:
            self._data.get("medications", {}).pop(med_id, None)
            self._data.get("history", {}).pop(med_id, None)
            await self._async_save()

    # ---------- Supply tracking ----------

    def get_stock(self, med_id: str) -> int:
        """Get current stock level for a medication."""
        return self._data.get("medications", {}).get(med_id, {}).get("current_stock", 0)

    async def async_set_stock(self, med_id: str, amount: int) -> None:
        """Set absolute stock level."""
        async with self._lock:
            if med_id in self._data.get("medications", {}):
                self._data["medications"][med_id]["current_stock"] = max(0, amount)
                await self._async_save()

    async def async_adjust_stock(self, med_id: str, delta: int) -> int:
        """Adjust stock by delta (negative to consume, positive to add).

        Returns new stock level.
        """
        async with self._lock:
            med = self._data.get("medications", {}).get(med_id)
            if not med:
                return 0
            current = med.get("current_stock", 0)
            new_stock = max(0, current + delta)
            med["current_stock"] = new_stock
            await self._async_save()
            return new_stock

    # ---------- History (taken doses) ----------

    def get_history(self, med_id: str) -> list[dict[str, Any]]:
        """Get dose history for a medication (newest first)."""
        return list(self._data.get("history", {}).get(med_id, []))

    async def async_record_dose(self, med_id: str) -> str:
        """Record a dose as taken. Returns the history entry ID."""
        async with self._lock:
            entry = {
                "id": _make_id(),
                "timestamp": datetime.now().isoformat(),
                "action": "taken",
            }
            self._data.setdefault("history", {}).setdefault(med_id, []).insert(0, entry)
            await self._async_save()
            return entry["id"]

    async def async_undo_last_dose(self, med_id: str) -> dict[str, Any] | None:
        """Remove the most recent 'taken' entry. Returns the removed entry or None."""
        async with self._lock:
            history = self._data.get("history", {}).get(med_id, [])
            for i, entry in enumerate(history):
                if entry.get("action") == "taken":
                    removed = history.pop(i)
                    await self._async_save()
                    return removed
            return None

    async def async_undo_dose_by_id(self, med_id: str, dose_id: str) -> dict[str, Any] | None:
        """Remove a specific dose entry by ID."""
        async with self._lock:
            history = self._data.get("history", {}).get(med_id, [])
            for i, entry in enumerate(history):
                if entry.get("id") == dose_id:
                    removed = history.pop(i)
                    await self._async_save()
                    return removed
            return None

    def get_last_taken(self, med_id: str) -> datetime | None:
        """Return the last taken datetime or None."""
        history = self._data.get("history", {}).get(med_id, [])
        for entry in history:
            if entry.get("action") == "taken":
                return datetime.fromisoformat(entry["timestamp"])
        return None

    def get_taken_today(self, med_id: str) -> int:
        """Count doses taken today."""
        today = datetime.now().date()
        count = 0
        for entry in self._data.get("history", {}).get(med_id, []):
            if entry.get("action") == "taken":
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts.date() == today:
                    count += 1
        return count


def _make_id() -> str:
    """Generate a short unique ID."""
    import uuid

    return uuid.uuid4().hex[:12]
