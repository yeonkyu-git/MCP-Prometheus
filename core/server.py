from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from core.config import load_env_urls

logger = logging.getLogger("prom-mcp")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)

mcp = FastMCP("prometheus-health-mcp")
ENV_URLS = load_env_urls(logger)
