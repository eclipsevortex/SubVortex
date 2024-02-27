import json
import websockets

class SubVortexApi:
    def __init__(self):
        self.uri = "ws://localhost:8000/ws"

    async def send(self, payload):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(json.dumps(payload))