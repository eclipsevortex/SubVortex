import json
import time
import socket
import select
import bittensor as bt

from http.server import BaseHTTPRequestHandler


class SSEHandler(BaseHTTPRequestHandler):
    no_events_sent = True
    timeout = 5
    heartbeat_interval = 30
    max_missed_heartbeats = 3

    def log_message(self, format, *args):
        # Override to suppress logging
        pass

    def handle(self):
        try:
            super().handle()
        except ConnectionResetError:
            pass

    def do_GET(self):
        path = self.path.strip("/")
        if path not in self.server.streams:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.server.streams[path].append(self)
        self.no_events_sent = True
        bt.logging.debug(
            f"[SSE][{path}] New connection - {len(self.server.streams[path])} connection(s) active"
        )

        missed_heartbeats = 0
        last_heartbeat = time.time()

        try:
            while not self.server.shutdown_event.is_set():
                # Use select to check if the client is still connected
                r, _, _ = select.select([self.rfile], [], [], 0.5)
                if r:
                    # Client has disconnected
                    break

                current_time = time.time()
                if current_time - last_heartbeat >= self.heartbeat_interval:
                    if not self.send_heartbeat():
                        missed_heartbeats += 1
                        if missed_heartbeats >= self.max_missed_heartbeats:
                            # Assume the client is in sleep mode or disconnected
                            break
                    else:
                        missed_heartbeats = 0
                    last_heartbeat = current_time
        finally:
            self._remove_client()

    def send_event(self, event):
        try:
            self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
            self.no_events_sent = False
            self.wfile.flush()
        except (
            Exception,
            TimeoutError,
            ConnectionResetError,
            socket.timeout,
            socket.error,
        ):
            pass

    def send_heartbeat(self):
        try:
            self.wfile.write('data: { "type": "ping" }\n\n'.encode("utf-8"))
            self.wfile.flush()
            return True
        except (
            Exception,
            TimeoutError,
            ConnectionResetError,
            socket.timeout,
            socket.error,
        ):
            return False

    def _remove_client(self):
        path = self.path.strip("/")
        clients = self.server.streams.get(path, [])
        if self in clients:
            self.server.streams[path].remove(self)
            self.no_events_sent = True
            bt.logging.debug(
                f"[SSE][{path}] Connection removed - {len(self.server.streams[path])} connection(s) remaining"
            )
