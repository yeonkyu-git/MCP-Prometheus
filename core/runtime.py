from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from domain.checks import Check
from core.config import DEFAULT_PROM_URL, MAX_SAMPLES_PER_SERIES, normalize_env
from core.server import ENV_URLS
from core.time_utils import step_to_seconds


def resolve_prom_url(environment: Optional[str], env_hint: Optional[str]) -> Tuple[str, str]:
    if environment:
        key = normalize_env(environment)
        if key in ENV_URLS:
            return key, ENV_URLS[key]
        raise ValueError(f"Unknown environment: {environment}")

    if env_hint:
        key = normalize_env(env_hint)
        if key in ENV_URLS:
            return key, ENV_URLS[key]

    if DEFAULT_PROM_URL:
        return "default", DEFAULT_PROM_URL

    raise ValueError("No environment selected and PROM_URL is not set")


def should_apply_alerts(c: Optional[Check]) -> bool:
    if not c:
        return False
    if "%" in c.name:
        return True
    return c.id.endswith("_pct")


def validate_sample_volume(
    *,
    include_samples: bool,
    start: datetime,
    end: datetime,
    step: str,
) -> None:
    if not include_samples:
        return
    points = int(max(0.0, (end - start).total_seconds()) // step_to_seconds(step)) + 1
    if points > MAX_SAMPLES_PER_SERIES:
        raise ValueError(
            f"Too many samples per series ({points}). "
            f"Reduce range/increase step or disable include_samples "
            f"(limit={MAX_SAMPLES_PER_SERIES})."
        )
