from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import ALERT_CRIT_PCT, ALERT_SUSTAIN_MINUTES, ALERT_WARN_PCT, MAX_PARALLEL_CHECKS
from core.runtime import resolve_prom_url, should_apply_alerts, validate_sample_volume
from core.server import mcp
from core.time_utils import format_range, iso, parse_step, resolve_time_range, step_to_seconds
from domain.checks import CHECKS, Check
from infra.prom_client import prom_query_range
from utils.query_utils import apply_target_filter, render_promql
from utils.summarize import summarize_matrix


@mcp.tool()
def run_check(
    check_id: str,
    hours: Optional[int] = None,
    minutes: Optional[int] = None,
    days: Optional[int] = None,
    step: str = "5m",
    include_samples: bool = False,
    start_time_utc_iso: Optional[str] = None,
    end_time_utc_iso: Optional[str] = None,
    end_offset_minutes: Optional[int] = None,
    end_offset_hours: Optional[int] = None,
    end_offset_days: Optional[int] = None,
    server_name: Optional[str] = None,
    instance: Optional[str] = None,
    environment: Optional[str] = None,
    env_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run one allowlisted check via Prometheus `query_range` and return summarized results.

    Inputs:
    - check_id: required check id from `domain.checks.CHECKS`.
    - hours/minutes/days: relative lookback window.
    - start_time_utc_iso/end_time_utc_iso: absolute UTC range (if provided, this is used).
    - end_offset_minutes/end_offset_hours/end_offset_days: shift end time to the past.
    - step: range-query step (example: `1m`, `5m`, `15m`).
    - include_samples: include raw samples in each series summary.
    - server_name: label filter for `server_name`.
    - instance: label filter for `instance` (example: `host-or-ip:9100`).
      Use this when targeting one exact exporter endpoint.
    - environment/env_hint: environment selector (`environment` has higher priority).

    Filter behavior:
    - If both `server_name` and `instance` are provided, both filters are applied.
    - If only one is provided, only that label is applied.
    """
    if check_id not in CHECKS:
        raise ValueError(f"Unknown check_id: {check_id}")

    c = CHECKS[check_id]
    step = parse_step(step)
    env_key, prom_url = resolve_prom_url(environment, env_hint)

    start, end = resolve_time_range(
        hours=hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
    )
    validate_sample_volume(include_samples=include_samples, start=start, end=end, step=step)

    range_str = format_range(end - start)
    promql = render_promql(c, range_str)
    promql = apply_target_filter(promql, server_name=server_name, instance=instance)

    alert_config = None
    if should_apply_alerts(c):
        alert_config = {
            "warn_pct": ALERT_WARN_PCT,
            "crit_pct": ALERT_CRIT_PCT,
            "sustain_seconds": ALERT_SUSTAIN_MINUTES * 60,
            "step_seconds": step_to_seconds(step),
        }

    t0 = time.time()
    data = prom_query_range(prom_url, promql, start=start, end=end, step=step)
    elapsed_ms = int((time.time() - t0) * 1000)

    result = data.get("data", {}).get("result", [])
    summarized = summarize_matrix(result, include_samples=include_samples, alert_config=alert_config)

    return {
        "check": {"id": c.id, "name": c.name, "description": c.description},
        "environment": env_key,
        "prom_url": prom_url,
        "filter": {"server_name": server_name, "instance": instance},
        "alert_config": alert_config,
        "range": {"start": iso(start), "end": iso(end), "step": step},
        "series_count": len(summarized),
        "elapsed_ms": elapsed_ms,
        "results": summarized,
    }


def _run_single_check(
    c: Check,
    *,
    prom_url: str,
    range_str: str,
    start: datetime,
    end: datetime,
    step: str,
    include_samples: bool,
    server_name: Optional[str],
    instance: Optional[str],
) -> Dict[str, Any]:
    """
    Internal helper for `run_all_checks`.

    This function is intentionally not decorated with `@mcp.tool()` because it is
    implementation detail used for parallel execution.
    """
    promql = render_promql(c, range_str)
    promql = apply_target_filter(promql, server_name=server_name, instance=instance)

    alert_config = None
    if should_apply_alerts(c):
        alert_config = {
            "warn_pct": ALERT_WARN_PCT,
            "crit_pct": ALERT_CRIT_PCT,
            "sustain_seconds": ALERT_SUSTAIN_MINUTES * 60,
            "step_seconds": step_to_seconds(step),
        }

    t0 = time.time()
    data = prom_query_range(prom_url, promql, start=start, end=end, step=step)
    elapsed_ms = int((time.time() - t0) * 1000)
    result = data.get("data", {}).get("result", [])
    summarized = summarize_matrix(result, include_samples=include_samples, alert_config=alert_config)
    return {
        "check": {"id": c.id, "name": c.name, "description": c.description},
        "series_count": len(summarized),
        "elapsed_ms": elapsed_ms,
        "alert_config": alert_config,
        "results": summarized,
    }


@mcp.tool()
def run_all_checks(
    hours: Optional[int] = None,
    minutes: Optional[int] = None,
    days: Optional[int] = None,
    step: str = "5m",
    include_samples: bool = False,
    start_time_utc_iso: Optional[str] = None,
    end_time_utc_iso: Optional[str] = None,
    end_offset_minutes: Optional[int] = None,
    end_offset_hours: Optional[int] = None,
    end_offset_days: Optional[int] = None,
    server_name: Optional[str] = None,
    instance: Optional[str] = None,
    environment: Optional[str] = None,
    env_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run all allowlisted checks in parallel for the same time range and filters.

    Inputs are equivalent to `run_check`, including:
    - `server_name`: filter by label `server_name`
    - `instance`: filter by label `instance` (single-target filter)

    Note:
    - `step` is fixed to `5m` in this tool to control payload size.
      Any provided `step` value is ignored.
    """
    step = "5m"
    env_key, prom_url = resolve_prom_url(environment, env_hint)
    start, end = resolve_time_range(
        hours=hours,
        minutes=minutes,
        days=days,
        start_time_utc_iso=start_time_utc_iso,
        end_time_utc_iso=end_time_utc_iso,
        end_offset_minutes=end_offset_minutes,
        end_offset_hours=end_offset_hours,
        end_offset_days=end_offset_days,
    )
    validate_sample_volume(include_samples=include_samples, start=start, end=end, step=step)
    range_str = format_range(end - start)

    check_ids: List[str] = list(CHECKS.keys())
    max_workers = max(1, min(MAX_PARALLEL_CHECKS, len(check_ids)))
    out_map: Dict[str, Dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            check_id: ex.submit(
                _run_single_check,
                CHECKS[check_id],
                prom_url=prom_url,
                range_str=range_str,
                start=start,
                end=end,
                step=step,
                include_samples=include_samples,
                server_name=server_name,
                instance=instance,
            )
            for check_id in check_ids
        }
        for check_id, fut in futures.items():
            c = CHECKS[check_id]
            try:
                out_map[check_id] = fut.result()
            except Exception as exc:
                out_map[check_id] = {
                    "check": {"id": c.id, "name": c.name, "description": c.description},
                    "error": str(exc),
                }

    out = [out_map[check_id] for check_id in check_ids]
    failed = sum(1 for item in out if "error" in item)
    return {
        "environment": env_key,
        "prom_url": prom_url,
        "filter": {"server_name": server_name, "instance": instance},
        "range": {"start": iso(start), "end": iso(end), "step": step},
        "parallel_workers": max_workers,
        "failed_checks": failed,
        "checks": out,
    }
