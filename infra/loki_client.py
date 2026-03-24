from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Sequence

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import LOKI_BEARER_TOKEN, LOKI_TIMEOUT_SEC
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


def _loki_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if LOKI_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {LOKI_BEARER_TOKEN}"
    return headers


def _loki_get_json(loki_url: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not loki_url:
        raise ValueError("loki_url is empty")

    url = f"{loki_url.rstrip('/')}{path}"
    response = _session.get(url, params=params, headers=_loki_headers(), timeout=LOKI_TIMEOUT_SEC)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Loki error: {data}")
    return data


def _escape_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_loki_selector(
    *,
    env: Optional[str] = None,
    host: Optional[str] = None,
    app: Optional[str] = None,
    labels: Optional[Mapping[str, str]] = None,
) -> str:
    matchers = []
    for key, value in (("env", env), ("host", host), ("app", app)):
        if value:
            matchers.append(f'{key}="{_escape_label_value(value)}"')

    if labels:
        for key in sorted(labels):
            value = labels[key]
            if value:
                matchers.append(f'{key}="{_escape_label_value(value)}"')

    return "{" + ",".join(matchers) + "}"


def loki_query_range(
    loki_url: str,
    query: str,
    *,
    start: datetime,
    end: datetime,
    step: Optional[str] = None,
    limit: Optional[int] = None,
    direction: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "query": query,
        "start": to_unix(start),
        "end": to_unix(end),
    }
    if step:
        params["step"] = step
    if limit is not None:
        params["limit"] = limit
    if direction:
        params["direction"] = direction
    return _loki_get_json(loki_url, "/loki/api/v1/query_range", params=params)


def loki_label_values(
    loki_url: str,
    label: str,
    *,
    selectors: Optional[Sequence[str]] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Sequence[str]:
    params: Dict[str, Any] = {}
    if selectors:
        params["match[]"] = [selector for selector in selectors if selector]
    if start is not None:
        params["start"] = to_unix(start)
    if end is not None:
        params["end"] = to_unix(end)

    data = _loki_get_json(loki_url, f"/loki/api/v1/label/{label}/values", params=params or None)
    return data.get("data", [])


def loki_series(
    loki_url: str,
    *,
    selectors: Optional[Sequence[str]] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Sequence[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if selectors:
        params["match[]"] = [selector for selector in selectors if selector]
    if start is not None:
        params["start"] = to_unix(start)
    if end is not None:
        params["end"] = to_unix(end)

    data = _loki_get_json(loki_url, "/loki/api/v1/series", params=params or None)
    return data.get("data", [])
