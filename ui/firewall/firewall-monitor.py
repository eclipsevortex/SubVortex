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
import os
import io
import sys
import signal
import argparse
import http.server
import urllib.parse
import socketserver

from subnet.firewall.firewall_factory import create_firewall_tool

PORT = 8080

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
EVENT_SOURCE_URL = "http://localhost:5000"

server_instance = None


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL and query parameters
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/":
            path = "/firewall-monitor.html"

        self.path = path

        return super().do_GET()

    def translate_path(self, path):
        return os.path.join(BASE_DIR, path[1:])

    def send_head(self):
        path = self.translate_path(self.path)
        if path.endswith(".html"):
            f = open(path, "rb")
            content = f.read().decode("utf-8")
            f.close()
            # Inject the EventSource URL
            content = content.replace("{{EVENT_SOURCE_URL}}", EVENT_SOURCE_URL)
            encoded = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            return io.BytesIO(encoded)
        elif path.endswith(".css"):
            f = open(path, "rb")
            content = f.read()
            f.close()
            self.send_response(200)
            self.send_header("Content-type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            return io.BytesIO(content)
        else:
            return super().send_head()


class CustomTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def server_activate(self):
        super().server_activate()
        self.on_startup()

    def server_close(self):
        self.on_shutdown()
        super().server_close()

    def on_startup(self):
        print("Server is starting...")

    def on_shutdown(self):
        print("Server is shutting down...")


def run_server(event_source_url: str, consumer_ip: str = None):
    global server_instance, EVENT_SOURCE_URL
    EVENT_SOURCE_URL = event_source_url

    with CustomTCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        try:
            server_instance = httpd

            # Add the rule
            tool = create_firewall_tool()
            tool.create_allow_rule(ip=consumer_ip, dport=8080, protocol="tcp")

            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()

            # Remove the rule
            tool = create_firewall_tool()
            tool.remove_rule(ip=consumer_ip, dport=8080, protocol="tcp", allow=True)


def signal_handler(sig, frame):
    global server_instance
    print("Interrupt received, shutting down server...")
    if server_instance:
        server_instance.server_close()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signals

    parser = argparse.ArgumentParser(
        description="Run the SSE server with custom EventSource URL"
    )
    parser.add_argument(
        "--event-source-url",
        type=str,
        default="http://localhost:5000",
        help="The EventSource URL to use in the HTML (format: http://<ip>:<port>)",
    )
    parser.add_argument(
        "--consumer-ip",
        type=str,
        default=None,
        help="Ip of the machine that will display the UI via a browser",
    )

    args = parser.parse_args()
    run_server(args.event_source_url, args.consumer_ip)
