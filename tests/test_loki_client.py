from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest import mock

from infra.loki_client import (
    build_loki_selector,
    loki_label_values,
    loki_query_range,
    loki_series,
)


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


class LokiClientTests(unittest.TestCase):
    def test_build_loki_selector_escapes_values_and_skips_missing_labels(self) -> None:
        selector = build_loki_selector(
            env="prod",
            host='app-01\\east"',
            app="cms",
        )

        self.assertEqual(selector, '{env="prod",host="app-01\\\\east\\"",app="cms"}')

    def test_loki_query_range_sends_expected_request(self) -> None:
        captured = {}

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            captured["timeout"] = timeout
            return _FakeResponse({"status": "success", "data": {"resultType": "streams", "result": []}})

        start = datetime(2026, 3, 24, 1, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 24, 2, 0, tzinfo=timezone.utc)
        with mock.patch("infra.loki_client._session.get", side_effect=fake_get):
            result = loki_query_range(
                "http://loki.example",
                '{app="cms"} |= "error"',
                start=start,
                end=end,
                step="5m",
                limit=250,
            )

        self.assertEqual(result["data"]["resultType"], "streams")
        self.assertEqual(captured["url"], "http://loki.example/loki/api/v1/query_range")
        self.assertEqual(captured["params"]["query"], '{app="cms"} |= "error"')
        self.assertEqual(captured["params"]["step"], "5m")
        self.assertEqual(captured["params"]["limit"], 250)
        self.assertAlmostEqual(captured["params"]["start"], start.timestamp())
        self.assertAlmostEqual(captured["params"]["end"], end.timestamp())

    def test_loki_label_values_supports_selector_filters(self) -> None:
        captured = {}

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            return _FakeResponse({"status": "success", "data": ["api", "web"]})

        with mock.patch("infra.loki_client._session.get", side_effect=fake_get):
            values = loki_label_values(
                "http://loki.example",
                "app",
                selectors=['{env="prod"}', '{host="cms-01"}'],
            )

        self.assertEqual(values, ["api", "web"])
        self.assertEqual(captured["url"], "http://loki.example/loki/api/v1/label/app/values")
        self.assertEqual(
            captured["params"],
            {
                "match[]": ['{env="prod"}', '{host="cms-01"}'],
            },
        )

    def test_loki_series_supports_time_window_and_selectors(self) -> None:
        captured = {}

        def fake_get(url, params=None, headers=None, timeout=None):
            captured["url"] = url
            captured["params"] = params
            return _FakeResponse({"status": "success", "data": [{"stream": {"env": "prod"}}]})

        start = datetime(2026, 3, 24, 1, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 24, 2, 0, tzinfo=timezone.utc)
        with mock.patch("infra.loki_client._session.get", side_effect=fake_get):
            series = loki_series(
                "http://loki.example",
                selectors=['{env="prod"}'],
                start=start,
                end=end,
            )

        self.assertEqual(series, [{"stream": {"env": "prod"}}])
        self.assertEqual(captured["url"], "http://loki.example/loki/api/v1/series")
        self.assertAlmostEqual(captured["params"]["start"], start.timestamp())
        self.assertAlmostEqual(captured["params"]["end"], end.timestamp())
        self.assertEqual(captured["params"]["match[]"], ['{env="prod"}'])


if __name__ == "__main__":
    unittest.main()
