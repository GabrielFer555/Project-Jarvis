import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler
from typing import TypeAlias

from .routers.health import health

Response: TypeAlias = tuple[int, dict[str, str]]
RouteHandler: TypeAlias = Callable[[], Response]

ROUTES: dict[tuple[str, str], RouteHandler] = {
    ("GET", "/health"): health,
}


class ApiRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._dispatch()

    def _dispatch(self) -> None:
        handler = ROUTES.get((self.command, self.path))
        status, payload = (
            handler() if handler is not None else (404, {"status": "not_found"})
        )
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return
