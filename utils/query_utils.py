from __future__ import annotations

from typing import List, Optional

from domain.checks import Check

def render_promql(c: Check, range_str: str) -> str:
    if "{range}" in c.promql:
        return c.promql.replace("{range}", range_str)
    return c.promql


def _escape_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def apply_target_filter(
    promql: str,
    *,
    server_name: Optional[str],
    instance: Optional[str],
) -> str:
    if not server_name and not instance:
        return promql

    matchers: List[str] = []
    on_labels: List[str] = []
    if instance:
        matchers.append(f'instance="{_escape_label_value(instance)}"')
        on_labels.append("instance")
    if server_name:
        matchers.append(f'server_name="{_escape_label_value(server_name)}"')
        on_labels.append("server_name")

    matcher_str = ",".join(matchers)
    on_str = ",".join(on_labels)
    return f"({promql}) and on ({on_str}) up{{{matcher_str}}}"
