from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import LOKI_ENV_URLS
from core.runtime import resolve_loki_url
from core.server import mcp
from core.time_utils import iso, iso_jakarta, resolve_time_range
from infra.loki_client import build_loki_selector, loki_label_values, loki_query_range

DEFAULT_DISCOVERY_HOURS = 1
DEFAULT_LOG_LIMIT = 200
MAX_LOG_LIMIT = 1000


def _resolve_log_range(
    *,
    hours: Optional[int],
    minutes: Optional[int],
    days: Optional[int],
    start_time_utc_iso: Optional[str],
    end_time_utc_iso: Optional[str],
    end_offset_minutes: Optional[int],
    end_offset_hours: Optional[int],
    end_offset_days: Optional[int],
    default_hours: int,
) -> tuple[datetime, datetime]:
    return resolve_time_range(
        hours=hours if hours is not None else default_hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
    )


def _dedupe_sorted(values: List[str], limit: int) -> List[str]:
    return sorted(set(v for v in values if v))[:limit]


def _format_logql(selector: str, contains: Optional[str], level: Optional[str]) -> str:
    query = selector
    for filter_value in (level, contains):
        if filter_value and filter_value.strip():
            escaped = filter_value.replace("\\", "\\\\").replace('"', '\\"')
            query += f' |= "{escaped}"'
    return query


def _ns_to_datetime(value: str) -> datetime:
    return datetime.fromtimestamp(int(value) / 1_000_000_000, tz=timezone.utc)


@mcp.tool()
def list_loki_environments() -> Dict[str, Any]:
    environments = [{"key": key, "loki_url": value} for key, value in sorted(LOKI_ENV_URLS.items())]
    return {"environments": environments}


@mcp.tool()
def list_loki_hosts(
    loki_environment: str,
    log_env: Optional[str] = None,
    app: Optional[str] = None,
    hours: Optional[int] = DEFAULT_DISCOVERY_HOURS,
    minutes: Optional[int] = None,
    days: Optional[int] = None,
    start_time_utc_iso: Optional[str] = None,
    end_time_utc_iso: Optional[str] = None,
    end_offset_minutes: Optional[int] = None,
    end_offset_hours: Optional[int] = None,
    end_offset_days: Optional[int] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    env_key, loki_url = resolve_loki_url(loki_environment)
    start, end = _resolve_log_range(
        hours=hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
        default_hours=DEFAULT_DISCOVERY_HOURS,
    )
    selector = build_loki_selector(env=log_env, app=app)
    hosts = _dedupe_sorted(list(loki_label_values(loki_url, "host", selectors=[selector], start=start, end=end)), limit)
    return {
        "loki_environment": env_key,
        "loki_url": loki_url,
        "filters": {"log_env": log_env, "app": app},
        "range": {"start": iso(start), "end": iso(end)},
        "count": len(hosts),
        "hosts": hosts,
    }


@mcp.tool()
def list_loki_apps(
    loki_environment: str,
    log_env: Optional[str] = None,
    host: Optional[str] = None,
    hours: Optional[int] = DEFAULT_DISCOVERY_HOURS,
    minutes: Optional[int] = None,
    days: Optional[int] = None,
    start_time_utc_iso: Optional[str] = None,
    end_time_utc_iso: Optional[str] = None,
    end_offset_minutes: Optional[int] = None,
    end_offset_hours: Optional[int] = None,
    end_offset_days: Optional[int] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    env_key, loki_url = resolve_loki_url(loki_environment)
    start, end = _resolve_log_range(
        hours=hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
        default_hours=DEFAULT_DISCOVERY_HOURS,
    )
    selector = build_loki_selector(env=log_env, host=host)
    apps = _dedupe_sorted(list(loki_label_values(loki_url, "app", selectors=[selector], start=start, end=end)), limit)
    return {
        "loki_environment": env_key,
        "loki_url": loki_url,
        "filters": {"log_env": log_env, "host": host},
        "range": {"start": iso(start), "end": iso(end)},
        "count": len(apps),
        "apps": apps,
    }


@mcp.tool()
def find_logs(
    loki_environment: str,
    log_env: str,
    host: str,
    app: str,
    hours: Optional[int] = 1,
    minutes: Optional[int] = None,
    days: Optional[int] = None,
    start_time_utc_iso: Optional[str] = None,
    end_time_utc_iso: Optional[str] = None,
    end_offset_minutes: Optional[int] = None,
    end_offset_hours: Optional[int] = None,
    end_offset_days: Optional[int] = None,
    limit: int = DEFAULT_LOG_LIMIT,
    contains: Optional[str] = None,
    level: Optional[str] = None,
) -> Dict[str, Any]:
    if limit <= 0 or limit > MAX_LOG_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LOG_LIMIT}")

    env_key, loki_url = resolve_loki_url(loki_environment)
    start, end = _resolve_log_range(
        hours=hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
        default_hours=1,
    )
    selector = build_loki_selector(env=log_env, host=host, app=app)
    query = _format_logql(selector, contains=contains, level=level)
    data = loki_query_range(
        loki_url,
        query,
        start=start,
        end=end,
        limit=limit,
        direction="backward",
    )

    logs: List[Dict[str, Any]] = []
    for stream in data.get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for raw_ts, line in stream.get("values", []):
            dt = _ns_to_datetime(raw_ts)
            logs.append(
                {
                    "timestamp": iso(dt),
                    "timestamp_jakarta": iso_jakarta(dt),
                    "labels": labels,
                    "line": line,
                }
            )

    return {
        "loki_environment": env_key,
        "loki_url": loki_url,
        "query": query,
        "range": {"start": iso(start), "end": iso(end)},
        "line_count": len(logs),
        "logs": logs,
    }
