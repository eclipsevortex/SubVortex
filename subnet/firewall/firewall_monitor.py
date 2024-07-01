import json
import queue
import threading

from subnet.firewall.storage.firewall_storage import FileStorage


class FirewallMonitor(threading.Thread):
    def __init__(self, storage: FileStorage) -> None:
        super().__init__(daemon=True)

        self._storage = storage
        self._queue = queue.Queue()

    def run(self):
        """
        Save all the events received in the event log file
        """
        with open("firewall-events.json", "a") as file:
            while True:
                event = self._queue.get()
                if event is None:
                    break

                # Write event to file
                file.write(json.dumps(event) + "\n")
                file.flush()

    def emit(self, event):
        """
        Add in the queue any event received for the emitter
        """
        # Store the new event in the queue
        self._queue.put(event)
