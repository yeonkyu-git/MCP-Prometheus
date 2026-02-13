from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


def stats_from_values(values: List[List[Any]]) -> Dict[str, Any]:
    nums: List[float] = []
    last_ts: Optional[float] = None
    last_val: Optional[float] = None

    for ts, v in values:
        try:
            fv = float(v)
            if math.isfinite(fv):
                nums.append(fv)
                last_ts = float(ts)
                last_val = fv
        except Exception:
            continue

    if not nums:
        return {"count": 0}

    return {
        "count": len(nums),
        "min": min(nums),
        "max": max(nums),
        "avg": sum(nums) / len(nums),
        "last": last_val,
        "last_ts": last_ts,
    }


def max_sustain_duration(
    values: List[List[Any]],
    *,
    threshold: float,
    step_seconds: int,
) -> float:
    max_dur = 0.0
    active_start: Optional[float] = None
    last_ts: Optional[float] = None
    gap_reset = max(1, int(step_seconds * 1.5))

    for ts, v in values:
        try:
            t = float(ts)
            fv = float(v)
            if not math.isfinite(fv):
                raise ValueError()
        except Exception:
            last_ts = None
            active_start = None
            continue

        if last_ts is not None and (t - last_ts) > gap_reset:
            active_start = None

        if fv >= threshold:
            if active_start is None:
                active_start = t
            dur = t - active_start
            if dur > max_dur:
                max_dur = dur
        else:
            active_start = None

        last_ts = t

    return max_dur


def summarize_matrix(
    result_matrix: List[Dict[str, Any]],
    include_samples: bool,
    *,
    alert_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for series in result_matrix:
        metric = series.get("metric", {})
        values = series.get("values", [])
        summary = stats_from_values(values)
        if alert_config and summary.get("count", 0) > 0:
            step_seconds = int(alert_config["step_seconds"])
            sustain_seconds = int(alert_config["sustain_seconds"])
            warn_pct = float(alert_config["warn_pct"])
            crit_pct = float(alert_config["crit_pct"])
            warn_max = max_sustain_duration(values, threshold=warn_pct, step_seconds=step_seconds)
            crit_max = max_sustain_duration(values, threshold=crit_pct, step_seconds=step_seconds)
            summary["sustain"] = {
                "warning": {
                    "threshold_pct": warn_pct,
                    "min_duration_sec": sustain_seconds,
                    "max_duration_sec": warn_max,
                    "breached": warn_max >= sustain_seconds,
                },
                "critical": {
                    "threshold_pct": crit_pct,
                    "min_duration_sec": sustain_seconds,
                    "max_duration_sec": crit_max,
                    "breached": crit_max >= sustain_seconds,
                },
            }
        item = {"metric": metric, "summary": summary}
        if include_samples:
            item["values"] = values
        out.append(item)
    return out
