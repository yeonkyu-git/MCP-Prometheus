from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

_STEP_RE = re.compile(r"^\d+[smhd]$")


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def to_unix(dt: datetime) -> float:
    return dt.timestamp()


def parse_step(step: str) -> str:
    s = (step or "").strip().lower()
    if not s:
        return "5m"
    if not _STEP_RE.match(s):
        raise ValueError(f"Invalid step format: {step}. Use formats like 30s, 5m, 1h, 1d.")
    return s


def step_to_seconds(step: str) -> int:
    s = parse_step(step)
    unit = s[-1]
    val = int(s[:-1])
    if unit == "s":
        return val
    if unit == "m":
        return val * 60
    if unit == "h":
        return val * 3600
    return val * 86400


def parse_iso_utc(value: str) -> datetime:
    s = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_range(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total <= 0:
        return "0s"
    if total % 86400 == 0:
        return f"{total // 86400}d"
    if total % 3600 == 0:
        return f"{total // 3600}h"
    if total % 60 == 0:
        return f"{total // 60}m"
    return f"{total}s"


def resolve_time_range(
    *,
    hours: Optional[int],
    minutes: Optional[int],
    days: Optional[int],
    start_time_utc_iso: Optional[str],
    end_time_utc_iso: Optional[str],
    end_offset_minutes: Optional[int],
    end_offset_hours: Optional[int],
    end_offset_days: Optional[int],
) -> Tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)

    if end_time_utc_iso:
        end = parse_iso_utc(end_time_utc_iso)
    elif end_offset_minutes or end_offset_hours or end_offset_days:
        delta = timedelta(
            minutes=int(end_offset_minutes or 0),
            hours=int(end_offset_hours or 0),
            days=int(end_offset_days or 0),
        )
        end = now - delta
    else:
        end = now

    if start_time_utc_iso:
        start = parse_iso_utc(start_time_utc_iso)
    else:
        if minutes or days:
            hours_val = int(hours) if hours is not None else 0
            days_val = int(days) if days is not None else 0
            delta = timedelta(
                minutes=int(minutes or 0),
                hours=hours_val,
                days=days_val,
            )
        else:
            delta = timedelta(hours=int(hours or 24))
        start = end - delta

    if start > end:
        raise ValueError("start_time must be <= end_time")
    return start, end
