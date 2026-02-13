from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import HTTP_TIMEOUT_SEC, PROM_BEARER_TOKEN
from core.time_utils import to_unix

_session = requests.Session()
_retry = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.3,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET"]),
)
_adapter = HTTPAdapter(max_retries=_retry)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)


def _prom_headers() -> Dict[str, str]:
    h = {"Accept": "application/json"}
    if PROM_BEARER_TOKEN:
        h["Authorization"] = f"Bearer {PROM_BEARER_TOKEN}"
    return h


def prom_query_range(prom_url: str, query: str, start: datetime, end: datetime, step: str) -> Dict[str, Any]:
    if not prom_url:
        raise ValueError("prom_url is empty")

    url = f"{prom_url.rstrip('/')}/api/v1/query_range"
    params = {
        "query": query,
        "start": to_unix(start),
        "end": to_unix(end),
        "step": step,
    }
    r = _session.get(url, params=params, headers=_prom_headers(), timeout=HTTP_TIMEOUT_SEC)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Prometheus error: {data}")
    return data


def prom_query_instant(prom_url: str, query: str, at: datetime) -> Dict[str, Any]:
    if not prom_url:
        raise ValueError("prom_url is empty")

    url = f"{prom_url.rstrip('/')}/api/v1/query"
    params = {
        "query": query,
        "time": to_unix(at),
    }
    r = _session.get(url, params=params, headers=_prom_headers(), timeout=HTTP_TIMEOUT_SEC)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Prometheus error: {data}")
    return data


def prom_label_values(prom_url: str, label: str, match: Optional[str] = None) -> List[str]:
    if not prom_url:
        raise ValueError("prom_url is empty")

    url = f"{prom_url.rstrip('/')}/api/v1/label/{label}/values"
    params: Dict[str, Any] = {}
    if match:
        params["match[]"] = match
    r = _session.get(url, params=params, headers=_prom_headers(), timeout=HTTP_TIMEOUT_SEC)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Prometheus error: {data}")
    return data.get("data", [])
