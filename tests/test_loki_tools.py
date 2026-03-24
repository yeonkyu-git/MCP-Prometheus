from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timezone
from unittest import mock


class LokiToolsTests(unittest.TestCase):
    def test_loki_tool_module_exists(self) -> None:
        module = importlib.import_module("tools.loki_query")
        self.assertTrue(hasattr(module, "list_loki_environments"))

    def test_list_loki_environments_returns_configured_backends(self) -> None:
        module = importlib.import_module("tools.loki_query")
        with mock.patch.object(
            module,
            "LOKI_ENV_URLS",
            {"dev_test": "http://loki.dev:3100", "prod": "http://loki.prod:3100"},
        ):
            result = module.list_loki_environments()

        self.assertEqual(
            result,
            {
                "environments": [
                    {"key": "dev_test", "loki_url": "http://loki.dev:3100"},
                    {"key": "prod", "loki_url": "http://loki.prod:3100"},
                ]
            },
        )

    def test_find_logs_formats_stream_results_with_jakarta_timestamps(self) -> None:
        module = importlib.import_module("tools.loki_query")
        payload = {
            "data": {
                "result": [
                    {
                        "stream": {"env": "prod", "host": "cms-01", "app": "cms"},
                        "values": [["1711249200000000000", "timeout error"]],
                    }
                ]
            }
        }

        with (
            mock.patch.object(module, "resolve_loki_url", return_value=("prod", "http://loki.prod:3100")),
            mock.patch.object(
                module,
                "resolve_time_range",
                return_value=(
                    datetime(2026, 3, 24, 1, 0, tzinfo=timezone.utc),
                    datetime(2026, 3, 24, 2, 0, tzinfo=timezone.utc),
                ),
            ),
            mock.patch.object(module, "loki_query_range", return_value=payload),
        ):
            result = module.find_logs(
                loki_environment="prod",
                log_env="prod",
                host="cms-01",
                app="cms",
                hours=1,
                contains="timeout",
            )

        self.assertEqual(result["line_count"], 1)
        self.assertIn('{env="prod",host="cms-01",app="cms"} |= "timeout"', result["query"])
        self.assertEqual(result["logs"][0]["labels"]["host"], "cms-01")
        self.assertTrue(result["logs"][0]["timestamp"].endswith("Z"))
        self.assertIn("+07:00", result["logs"][0]["timestamp_jakarta"])

    def test_list_loki_hosts_uses_one_hour_default_window(self) -> None:
        module = importlib.import_module("tools.loki_query")

        with (
            mock.patch.object(module, "resolve_loki_url", return_value=("prod", "http://loki.prod:3100")),
            mock.patch.object(
                module,
                "resolve_time_range",
                return_value=(
                    datetime(2026, 3, 24, 1, 0, tzinfo=timezone.utc),
                    datetime(2026, 3, 24, 2, 0, tzinfo=timezone.utc),
                ),
            ) as resolve_range,
            mock.patch.object(module, "loki_label_values", return_value=["cms-02", "cms-01", "cms-01"]),
        ):
            result = module.list_loki_hosts(loki_environment="prod", log_env="prod", app="cms")

        self.assertEqual(result["hosts"], ["cms-01", "cms-02"])
        self.assertEqual(resolve_range.call_args.kwargs["hours"], module.DEFAULT_DISCOVERY_HOURS)

    def test_list_loki_apps_uses_label_filters(self) -> None:
        module = importlib.import_module("tools.loki_query")

        with (
            mock.patch.object(module, "resolve_loki_url", return_value=("prod", "http://loki.prod:3100")),
            mock.patch.object(
                module,
                "resolve_time_range",
                return_value=(
                    datetime(2026, 3, 24, 1, 0, tzinfo=timezone.utc),
                    datetime(2026, 3, 24, 2, 0, tzinfo=timezone.utc),
                ),
            ),
            mock.patch.object(module, "loki_label_values", return_value=["api", "web"]),
        ):
            result = module.list_loki_apps(loki_environment="prod", log_env="prod", host="cms-01")

        self.assertEqual(result["apps"], ["api", "web"])
        self.assertEqual(result["filters"], {"log_env": "prod", "host": "cms-01"})


if __name__ == "__main__":
    unittest.main()
