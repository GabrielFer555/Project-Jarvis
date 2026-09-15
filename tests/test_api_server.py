import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from api.server import API_HOST, start_api


class ApiServerTests(unittest.TestCase):
    def test_server_is_bound_before_daemon_starts(self) -> None:
        events: list[str] = []
        settings = SimpleNamespace(api_port=8765)
        server = MagicMock()
        thread = MagicMock()

        def build_server(*_args, **_kwargs):
            events.append("server")
            return server

        def build_thread(*_args, **_kwargs):
            events.append("thread")
            return thread

        thread.start.side_effect = lambda: events.append("start")

        with patch("api.server.load_settings", return_value=settings):
            with patch(
                "api.server.ThreadingHTTPServer", side_effect=build_server
            ) as server_class:
                with patch("api.server.Thread", side_effect=build_thread) as thread_class:
                    result = start_api()

        self.assertIsNone(result)
        self.assertEqual(events, ["server", "thread", "start"])
        server_class.assert_called_once_with((API_HOST, 8765), unittest.mock.ANY)
        thread_class.assert_called_once_with(
            target=server.serve_forever,
            daemon=True,
        )
        thread.start.assert_called_once_with()

    def test_bind_failure_propagates_without_creating_thread(self) -> None:
        bind_error = OSError("address already in use")
        settings = SimpleNamespace(api_port=8765)

        with patch("api.server.load_settings", return_value=settings):
            with patch(
                "api.server.ThreadingHTTPServer", side_effect=bind_error
            ) as server_class:
                with patch("api.server.Thread") as thread_class:
                    with self.assertRaises(OSError) as ctx:
                        start_api()

        self.assertIs(ctx.exception, bind_error)
        server_class.assert_called_once_with((API_HOST, 8765), unittest.mock.ANY)
        thread_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
