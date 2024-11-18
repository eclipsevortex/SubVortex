# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
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
