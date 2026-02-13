from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.config import ALERT_CRIT_PCT, ALERT_SUSTAIN_MINUTES, ALERT_WARN_PCT
from core.runtime import resolve_prom_url, validate_sample_volume
from core.server import mcp
from core.time_utils import iso, parse_step, resolve_time_range, step_to_seconds
from infra.prom_client import prom_query_instant, prom_query_range
from utils.query_utils import apply_target_filter
from utils.summarize import stats_from_values, summarize_matrix


@mcp.tool()
def run_promql(
    promql: str,
    approved: bool = False,
    instant: bool = False,
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
    alert_pct: bool = False,
) -> Dict[str, Any]:
    """
    Run custom PromQL.

    Guardrail:
    - `approved` must be True before execution.

    Modes:
    - `instant=True`: use `/api/v1/query` at a single timestamp.
    - `instant=False`: use `/api/v1/query_range` for a time window.
    """
    if not promql or not promql.strip():
        raise ValueError("promql is required")

    promql_text = promql.strip()

    if not approved:
        return {
            "approved": False,
            "executed": False,
            "promql": promql_text,
            "instant": instant,
            "message": "Set approved=True to execute this custom PromQL.",
        }

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
    validate_sample_volume(include_samples=include_samples and not instant, start=start, end=end, step=step)
    filtered_promql = apply_target_filter(promql_text, server_name=server_name, instance=instance)

    warnings: List[str] = []
    alert_config = None
    if alert_pct and not instant:
        alert_config = {
            "warn_pct": ALERT_WARN_PCT,
            "crit_pct": ALERT_CRIT_PCT,
            "sustain_seconds": ALERT_SUSTAIN_MINUTES * 60,
            "step_seconds": step_to_seconds(step),
        }
    if alert_pct and instant:
        warnings.append("alert_pct is ignored in instant mode.")

    t0 = time.time()
    if instant:
        data = prom_query_instant(prom_url, filtered_promql, at=end)
    else:
        data = prom_query_range(prom_url, filtered_promql, start=start, end=end, step=step)
    elapsed_ms = int((time.time() - t0) * 1000)

    result_type = data.get("data", {}).get("resultType")
    result = data.get("data", {}).get("result", [])

    if instant:
        summarized: List[Dict[str, Any]] = []
        if result_type == "vector":
            for series in result:
                metric = series.get("metric", {})
                value = series.get("value", [])
                samples = [value] if isinstance(value, list) and len(value) == 2 else []
                item = {"metric": metric, "summary": stats_from_values(samples)}
                if include_samples and samples:
                    item["value"] = value
                summarized.append(item)
        elif result_type == "scalar":
            samples = [result] if isinstance(result, list) and len(result) == 2 else []
            item = {"metric": {}, "summary": stats_from_values(samples)}
            if include_samples and samples:
                item["value"] = result
            summarized.append(item)
        else:
            summarized.append(
                {
                    "metric": {},
                    "summary": {"count": 0},
                    "raw_result_type": result_type,
                    "raw_result": result,
                }
            )
        return {
            "approved": True,
            "executed": True,
            "promql": promql_text,
            "instant": True,
            "result_type": result_type,
            "warnings": warnings,
            "filter": {"server_name": server_name, "instance": instance},
            "alert_config": None,
            "environment": env_key,
            "prom_url": prom_url,
            "time": iso(end),
            "series_count": len(summarized),
            "elapsed_ms": elapsed_ms,
            "results": summarized,
        }

    summarized = summarize_matrix(result, include_samples=include_samples, alert_config=alert_config)
    return {
        "approved": True,
        "executed": True,
        "promql": promql_text,
        "instant": False,
        "warnings": warnings,
        "filter": {"server_name": server_name, "instance": instance},
        "alert_config": alert_config,
        "environment": env_key,
        "prom_url": prom_url,
        "range": {"start": iso(start), "end": iso(end), "step": step},
        "series_count": len(summarized),
        "elapsed_ms": elapsed_ms,
        "results": summarized,
    }
