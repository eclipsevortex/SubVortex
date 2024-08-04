import threading
import bittensor as bt

from subnet.sse.sse_server import SSEServer
from subnet.firewall.firewall_factory import create_firewall_tool


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
        # Remove the firewall rule
        bt.logging.warning(f"Shutting down SSE Server {self.ip}:{self.port}")
        self.tool.remove_rule(ip=self.ip, dport=self.port, protocol="tcp")

        # Shutdown the server
        self._server.shutdown()

        super().join()

    def run(self) -> None:
        self._server.serve_forever()
