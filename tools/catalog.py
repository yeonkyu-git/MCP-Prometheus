from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.runtime import resolve_prom_url
from core.server import ENV_URLS, mcp
from domain.checks import CHECKS
from infra.prom_client import prom_label_values, prom_query_range


@mcp.tool()
def list_checks() -> Dict[str, Any]:
    """
    Return all allowlisted monitoring checks available to the MCP server.

    Response:
    - checks[].id: stable check id
    - checks[].name: display name
    - checks[].description: human-readable check description
    """
    checks: List[Dict[str, str]] = []
    for c in CHECKS.values():
        checks.append({"id": c.id, "name": c.name, "description": c.description})
    return {"checks": checks}


@mcp.tool()
def list_environments() -> Dict[str, Any]:
    """
    Return configured Prometheus environments and their base URLs.

    Response:
    - environments[].key: environment key (for example `prod`, `dev_test`, `dr`)
    - environments[].prom_url: Prometheus URL for that environment
    """
    envs = [{"key": k, "prom_url": v} for k, v in sorted(ENV_URLS.items(), key=lambda x: x[0])]
    return {"environments": envs}


@mcp.tool()
def list_servers(
    environment: Optional[str] = None,
    env_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List monitored servers detected from recent `up{server_name!=""}` series.

    Inputs:
    - environment: explicit environment key (highest priority).
    - env_hint: fallback environment hint when `environment` is not provided.

    Behavior:
    - Queries last 10 minutes of `up{server_name!=""}`.
    - Returns unique targets by `(instance, job)` with `server_name`.
    """
    env_key, prom_url = resolve_prom_url(environment, env_hint)
    now = datetime.now(timezone.utc)
    result = prom_query_range(
        prom_url,
        'up{server_name!=""}',
        start=now - timedelta(minutes=10),
        end=now,
        step="5m",
    )
    series = result.get("data", {}).get("result", [])
    servers: List[Dict[str, Optional[str]]] = []
    for s in series:
        m = s.get("metric", {})
        server_name = m.get("server_name")
        if not server_name:
            continue
        servers.append(
            {
                "instance": m.get("instance"),
                "job": m.get("job"),
                "server_name": server_name,
            }
        )

    uniq: List[Dict[str, Optional[str]]] = []
    seen = set()
    for s in servers:
        key = (s.get("instance"), s.get("job"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    return {"environment": env_key, "prom_url": prom_url, "servers": uniq}


@mcp.tool()
def list_process_groups(
    environment: Optional[str] = None,
    env_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return process group names from process monitoring metrics.

    Source metric:
    - `namedprocess_namegroup_cpu_seconds_total{job="process_monitoring"}`
    - label queried: `groupname`
    """
    env_key, prom_url = resolve_prom_url(environment, env_hint)
    groups = prom_label_values(
        prom_url,
        label="groupname",
        match='namedprocess_namegroup_cpu_seconds_total{job="process_monitoring"}',
    )
    groups = sorted(set([g for g in groups if g]))
    return {"environment": env_key, "prom_url": prom_url, "groups": groups}
