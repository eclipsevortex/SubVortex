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
import bittensor.utils.btlogging as btul

from subvortex.core.sse.sse_server import SSEServer
from subvortex.core.firewall.firewall_factory import create_firewall_tool


LOGGER_NAME = "SSE Server"


class SSEThread(threading.Thread):
    def __init__(self, ip: str = None, port: int = 5000) -> None:
        super().__init__(daemon=True)
        self.ip = ip
        self.port = port

        # Create the server
        self._server = SSEServer(port=port)

        # Create the firewall rule
        self.tool = create_firewall_tool()
        self.tool.create_allow_rule(ip=ip, dport=port, protocol="tcp")

    @property
    def server(self):
        return self._server

    def stop(self) -> None:
        btul.logging.debug(f"[{LOGGER_NAME}] stopping...")

        # Remove the firewall rule
        self.tool.remove_rule(ip=self.ip, dport=self.port, protocol="tcp")

        # Shutdown the server
        self._server.shutdown()

        # Wait the thread to finish
        super().join()

        btul.logging.debug(f"[{LOGGER_NAME}] stopped")

    def run(self) -> None:
        self._server.serve_forever()
