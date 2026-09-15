from http.server import ThreadingHTTPServer
from threading import Thread

from agent.settings import load_settings

from .app import ApiRequestHandler

API_HOST = "127.0.0.1"


def start_api() -> None:
    """Liga o servidor antes de delegar somente o atendimento à daemon."""
    port = load_settings().api_port
    server = ThreadingHTTPServer((API_HOST, port), ApiRequestHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"API ligada em {API_HOST}:{port}")
