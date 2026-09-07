import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.app import ApiRequestHandler
from api.routers.health import health


class HealthTests(unittest.TestCase):
    def test_both_dependencies_up_returns_ok(self) -> None:
        with patch("api.routers.health.ping") as ping:
            with patch("api.routers.health.ping_groq") as ping_groq:
                status, payload = health()

        self.assertEqual(status, 200)
        self.assertEqual(
            payload,
            {"status": "ok", "postgres": "up", "groq": "up"},
        )
        ping.assert_called_once_with()
        ping_groq.assert_called_once_with()

    def test_each_single_failure_is_reported_and_both_pings_run(self) -> None:
        cases = (
            ("postgres", RuntimeError("DATABASE_URL=secret"), None, "down", "up"),
            ("groq", None, RuntimeError("GROQ_API_KEY=secret"), "up", "down"),
        )
        for name, postgres_error, groq_error, postgres, groq in cases:
            with self.subTest(name=name):
                with patch(
                    "api.routers.health.ping", side_effect=postgres_error
                ) as ping:
                    with patch(
                        "api.routers.health.ping_groq", side_effect=groq_error
                    ) as ping_groq:
                        status, payload = health()

                self.assertEqual(status, 503)
                self.assertEqual(
                    payload,
                    {
                        "status": "unavailable",
                        "postgres": postgres,
                        "groq": groq,
                    },
                )
                ping.assert_called_once_with()
                ping_groq.assert_called_once_with()

    def test_both_dependencies_down_returns_sanitized_payload(self) -> None:
        with patch(
            "api.routers.health.ping",
            side_effect=RuntimeError("postgres_password=secret DATABASE_URL=url"),
        ):
            with patch(
                "api.routers.health.ping_groq",
                side_effect=RuntimeError("GROQ_API_KEY=secret traceback"),
            ):
                status, payload = health()

        body = json.dumps(payload)
        self.assertEqual(status, 503)
        self.assertEqual(
            payload,
            {"status": "unavailable", "postgres": "down", "groq": "down"},
        )
        for secret in (
            "postgres_password",
            "GROQ_API_KEY",
            "DATABASE_URL",
            "traceback",
        ):
            self.assertNotIn(secret, body)


class ApiRequestHandlerTests(unittest.TestCase):
    def test_unknown_path_returns_json_404(self) -> None:
        handler = ApiRequestHandler.__new__(ApiRequestHandler)
        handler.command = "GET"
        handler.path = "/unknown"
        handler.wfile = io.BytesIO()

        with patch.object(handler, "send_response") as send_response:
            with patch.object(handler, "send_header") as send_header:
                with patch.object(handler, "end_headers") as end_headers:
                    handler._dispatch()

        send_response.assert_called_once_with(404)
        send_header.assert_any_call("Content-Type", "application/json")
        end_headers.assert_called_once_with()
        self.assertEqual(
            json.loads(handler.wfile.getvalue()),
            {"status": "not_found"},
        )


if __name__ == "__main__":
    unittest.main()
