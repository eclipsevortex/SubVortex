import threading
from http.server import HTTPServer
from socketserver import ThreadingMixIn

from subnet.sse.sse_handler import SSEHandler

class SSEServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    """Handle requests in a separate thread."""

    def __init__(self, port: int = 5000):
        super().__init__(("", port), SSEHandler)
        self._lock = threading.Lock()
        self.shutdown_event = threading.Event()
        self.streams = {}

    def add_stream(self, name: str):
        self.streams[name] = []

    def has_new_subscribers(self, path):
        clients = list(self.streams.get(path, []))
        return any(x.no_events_sent for x in clients)

    def broadcast(self, path, event, restore=False):
        clients = list(self.streams.get(path, []))
        for client in clients:
            if restore and not client.no_events_sent:
                continue

            client.send_event(event)

    def shutdown_server(self):
        self.shutdown_event.set()
        self.shutdown()

    def handle_request(self):
        if self.shutdown_event.is_set():
            return False
        super().handle_request()
