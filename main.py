from __future__ import annotations

from core.server import mcp

# Import tools for side-effect registration on `mcp`
from tools import catalog as _catalog  # noqa: F401
from tools import checks_runner as _checks_runner  # noqa: F401
from tools import promql as _promql  # noqa: F401


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
