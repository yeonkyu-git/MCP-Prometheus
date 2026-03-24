from __future__ import annotations

import importlib
import json
import logging
import unittest
from unittest import mock

import core.config as config
import core.runtime as runtime


class LokiRuntimeTests(unittest.TestCase):
    def test_loki_config_reads_separate_environment_variables(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "LOKI_URL": "http://loki.default:3100/",
                "LOKI_ENV_URLS": json.dumps(
                    {"prod": "http://loki.prod:3100/", "dev-test": "http://loki.dev:3100/"}
                ),
                "LOKI_BEARER_TOKEN": "secret",
                "LOKI_TIMEOUT_SEC": "7.5",
            },
            clear=False,
        ):
            reloaded = importlib.reload(config)

        self.assertEqual(reloaded.DEFAULT_LOKI_URL, "http://loki.default:3100")
        self.assertEqual(reloaded.LOKI_BEARER_TOKEN, "secret")
        self.assertEqual(reloaded.LOKI_TIMEOUT_SEC, 7.5)
        self.assertEqual(
            reloaded.LOKI_ENV_URLS,
            {"prod": "http://loki.prod:3100/", "dev_test": "http://loki.dev:3100/"},
        )

    def test_normalize_loki_environment_maps_supported_aliases(self) -> None:
        self.assertEqual(runtime.normalize_loki_environment("prod"), "prod")
        self.assertEqual(runtime.normalize_loki_environment("production"), "prod")
        self.assertEqual(runtime.normalize_loki_environment("dev-test"), "dev_test")
        self.assertEqual(runtime.normalize_loki_environment("dev_test"), "dev_test")

    def test_load_loki_env_urls_normalizes_keys(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {
                "LOKI_ENV_URLS": json.dumps(
                    {"prod": "http://loki.prod:3100", "dev-test": "http://loki.dev:3100"}
                )
            },
            clear=False,
        ):
            reloaded = importlib.reload(config)
            urls = reloaded.load_loki_env_urls(logging.getLogger("test"))

        self.assertEqual(urls, {"prod": "http://loki.prod:3100", "dev_test": "http://loki.dev:3100"})

    def test_resolve_loki_url_uses_explicit_environment(self) -> None:
        with mock.patch.object(
            runtime,
            "LOKI_ENV_URLS",
            {"prod": "http://loki.prod:3100", "dev_test": "http://loki.dev:3100"},
        ), mock.patch.object(runtime, "DEFAULT_LOKI_URL", "http://loki.default:3100"):
            env, url = runtime.resolve_loki_url("dev-test")

        self.assertEqual(env, "dev_test")
        self.assertEqual(url, "http://loki.dev:3100")

    def test_resolve_loki_url_rejects_unknown_environment(self) -> None:
        with mock.patch.object(
            runtime,
            "LOKI_ENV_URLS",
            {"prod": "http://loki.prod:3100", "dev_test": "http://loki.dev:3100"},
        ):
            with self.assertRaisesRegex(ValueError, "Unknown Loki environment"):
                runtime.resolve_loki_url("dr")


if __name__ == "__main__":
    unittest.main()
