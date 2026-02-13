from __future__ import annotations

import json
import logging
import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROM_URL = os.environ.get("PROM_URL", "").rstrip("/")
PROM_BEARER_TOKEN = os.environ.get("PROM_BEARER_TOKEN", "")
HTTP_TIMEOUT_SEC = float(os.environ.get("PROM_TIMEOUT_SEC", "15"))
ALERT_WARN_PCT = float(os.environ.get("ALERT_WARN_PCT", "85"))
ALERT_CRIT_PCT = float(os.environ.get("ALERT_CRIT_PCT", "95"))
ALERT_SUSTAIN_MINUTES = int(os.environ.get("ALERT_SUSTAIN_MINUTES", "5"))
MAX_SAMPLES_PER_SERIES = int(os.environ.get("PROM_MAX_SAMPLES_PER_SERIES", "5000"))
MAX_PARALLEL_CHECKS = int(os.environ.get("PROM_MAX_PARALLEL_CHECKS", "6"))


def normalize_env(value: str) -> str:
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    if v in ("prod", "production", "운영"):
        return "prod"
    if v in ("dev", "develop", "development", "개발"):
        return "dev"
    if v in ("test", "testing", "qa", "테스트"):
        return "test"
    if v in ("dr", "disaster_recovery", "재해복구"):
        return "dr"
    if v in ("dev_test", "devtest", "dev_and_test"):
        return "dev_test"
    return v


def load_env_urls(logger: logging.Logger) -> Dict[str, str]:
    env_urls: Dict[str, str] = {}
    raw = os.environ.get("PROM_ENV_URLS", "").strip()
    if not raw:
        logger.warning("PROM_ENV_URLS is not set; ENV_URLS is empty.")
        return env_urls

    try:
        parsed = json.loads(raw)
    except Exception:
        logger.warning("Failed to parse PROM_ENV_URLS; ignoring.")
        return env_urls

    if not isinstance(parsed, dict):
        logger.warning("PROM_ENV_URLS must be a JSON object; ignoring.")
        return env_urls

    for key, value in parsed.items():
        env_urls[normalize_env(str(key))] = str(value)
    return env_urls
