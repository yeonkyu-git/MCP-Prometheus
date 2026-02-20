from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.runtime import resolve_prom_url
from core.server import mcp
from core.time_utils import iso, iso_jakarta, parse_iso_utc
from infra.prom_client import prom_alerts


def _top(counter: Counter[str], n: int = 10) -> List[Dict[str, Any]]:
    return [{"key": k, "count": v} for k, v in counter.most_common(n)]


@mcp.tool()
def get_alerts(
    severity: Optional[str] = None,
    state: Optional[str] = None,
    alertname: Optional[str] = None,
    job: Optional[str] = None,
    server_name: Optional[str] = None,
    instance: Optional[str] = None,
    include_alerts: bool = True,
    environment: Optional[str] = None,
    env_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch active alerts from Prometheus `/api/v1/alerts`.

    Filters (exact-match):
    - severity/state/alertname/job/server_name/instance
    """
    env_key, prom_url = resolve_prom_url(environment, env_hint)
    raw = prom_alerts(prom_url)
    alerts = raw.get("data", {}).get("alerts", []) or []

    out_alerts: List[Dict[str, Any]] = []
    sev_counter: Counter[str] = Counter()
    state_counter: Counter[str] = Counter()
    alertname_counter: Counter[str] = Counter()
    job_counter: Counter[str] = Counter()
    server_counter: Counter[str] = Counter()

    for a in alerts:
        labels = a.get("labels", {}) or {}
        annotations = a.get("annotations", {}) or {}

        if severity and labels.get("severity") != severity:
            continue
        if state and a.get("state") != state:
            continue
        if alertname and labels.get("alertname") != alertname:
            continue
        if job and labels.get("job") != job:
            continue
        if server_name and labels.get("server_name") != server_name:
            continue
        if instance and labels.get("instance") != instance:
            continue

        sev_counter[str(labels.get("severity") or "unknown")] += 1
        state_counter[str(a.get("state") or "unknown")] += 1
        alertname_counter[str(labels.get("alertname") or "unknown")] += 1
        job_counter[str(labels.get("job") or "unknown")] += 1
        server_counter[str(labels.get("server_name") or "unknown")] += 1

        if not include_alerts:
            continue

        active_at_raw = a.get("activeAt")
        active_at_utc = None
        active_at_jakarta = None
        if isinstance(active_at_raw, str) and active_at_raw.strip():
            try:
                active_at_utc_dt = parse_iso_utc(active_at_raw)
                active_at_utc = iso(active_at_utc_dt)
                active_at_jakarta = iso_jakarta(active_at_utc_dt)
            except Exception:
                active_at_utc = None
                active_at_jakarta = None

        out_alerts.append(
            {
                "labels": labels,
                "annotations": annotations,
                "state": a.get("state"),
                "activeAt_raw": active_at_raw,
                "activeAt_utc": active_at_utc,
                "activeAt_jakarta": active_at_jakarta,
                "value": a.get("value"),
            }
        )

    now = datetime.now(timezone.utc)
    return {
        "environment": env_key,
        "prom_url": prom_url,
        "retrieved_at_utc": iso(now),
        "retrieved_at_jakarta": iso_jakarta(now),
        "filters": {
            "severity": severity,
            "state": state,
            "alertname": alertname,
            "job": job,
            "server_name": server_name,
            "instance": instance,
            "include_alerts": include_alerts,
        },
        "summary": {
            "total_alerts": len(out_alerts) if include_alerts else int(sum(sev_counter.values())),
            "severity": _top(sev_counter, n=20),
            "state": _top(state_counter, n=20),
            "alertname": _top(alertname_counter, n=20),
            "job": _top(job_counter, n=20),
            "server_name": _top(server_counter, n=20),
        },
        "alerts": out_alerts if include_alerts else [],
    }

