"""Schedule logic for medication times."""

from datetime import datetime, time, timedelta
from typing import Any

from .const import DAY_NAMES, SCHEDULE_TYPE_DAILY, SCHEDULE_TYPE_WEEKLY


def parse_time_str(time_str: str) -> time:
    """Parse a time string like '08:00' or '14:30' into a time object."""
    parts = time_str.strip().split(":")
    return time(int(parts[0]), int(parts[1]))


def get_next_dose_time(schedule: dict[str, Any], from_time: datetime | None = None) -> datetime | None:
    """Calculate the next dose time from a schedule.

    Args:
        schedule: Dict with 'schedule_type', 'times' (daily) or 'days' (weekly).
        from_time: Reference datetime. Defaults to now.

    Returns:
        Next dose datetime, or None if no upcoming dose.
    """
    if from_time is None:
        from_time = datetime.now()

    schedule_type = schedule.get("schedule_type", SCHEDULE_TYPE_DAILY)

    if schedule_type == SCHEDULE_TYPE_DAILY:
        return _next_daily_dose(schedule.get("times", []), from_time)
    else:
        return _next_weekly_dose(schedule.get("days", {}), from_time)


def _next_daily_dose(times: list[str], from_time: datetime) -> datetime | None:
    """Find next dose from a daily schedule."""
    if not times:
        return None

    current_time = from_time.time()
    today = from_time.date()

    sorted_times = sorted(parse_time_str(t) for t in times)

    for t in sorted_times:
        if t > current_time:
            return datetime.combine(today, t)

    tomorrow = today + timedelta(days=1)
    return datetime.combine(tomorrow, sorted_times[0])


def _next_weekly_dose(days: dict[str, list[str]], from_time: datetime) -> datetime | None:
    """Find next dose from a weekly schedule."""
    if not days:
        return None

    current_time = from_time.time()
    current_weekday = from_time.weekday()

    for offset in range(7):
        check_date = from_time.date() + timedelta(days=offset)
        check_weekday = check_date.weekday()
        day_name = DAY_NAMES[check_weekday]

        if day_name not in days:
            continue

        day_times = sorted(parse_time_str(t) for t in days[day_name] if t)

        if not day_times:
            continue

        if offset == 0:
            for t in day_times:
                if t > current_time:
                    return datetime.combine(check_date, t)
        else:
            return datetime.combine(check_date, day_times[0])

    return None


def get_todays_doses(schedule: dict[str, Any], date_override: datetime | None = None) -> list[time]:
    """Get all dose times for today.

    Args:
        schedule: Schedule dict.
        date_override: Override 'today' for testing.

    Returns:
        Sorted list of time objects.
    """
    if date_override is None:
        date_override = datetime.now()

    schedule_type = schedule.get("schedule_type", SCHEDULE_TYPE_DAILY)
    weekday = date_override.weekday()
    day_name = DAY_NAMES[weekday]

    if schedule_type == SCHEDULE_TYPE_DAILY:
        times = schedule.get("times", [])
    else:
        times = schedule.get("days", {}).get(day_name, [])

    return sorted(parse_time_str(t) for t in times if t)


def get_schedule_summary(schedule: dict[str, Any]) -> str:
    """Return a human-readable schedule summary."""
    schedule_type = schedule.get("schedule_type", SCHEDULE_TYPE_DAILY)

    if schedule_type == SCHEDULE_TYPE_DAILY:
        times = schedule.get("times", [])
        if not times:
            return "No times set"
        return f"Daily at {', '.join(sorted(times))}"
    else:
        days_dict = schedule.get("days", {})
        if not days_dict:
            return "No schedule set"
        parts = []
        for day in DAY_NAMES:
            if day in days_dict and days_dict[day]:
                parts.append(f"{day[:3].capitalize()} {', '.join(sorted(days_dict[day]))}")
        return " · ".join(parts) if parts else "No schedule set"
