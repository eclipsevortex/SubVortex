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
import json
import fcntl
import queue
import threading


class FirewallMonitor(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)

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
                try:
                    fcntl.flock(file, fcntl.LOCK_EX)

                    file.write(json.dumps(event) + "\n")
                    file.flush()
                finally:
                    fcntl.flock(file, fcntl.LOCK_UN)

    def emit(self, event):
        """
        Add in the queue any event received for the emitter
        """
        # Store the new event in the queue
        self._queue.put(event)

    def clean(self, sources={}):
        """
        Remove the request ids from the firewall json file
        """
        # Extract request IDs
        request_ids = {x.id for source in sources.values() for x in source}

        # Read and process the file content
        with open("firewall-events.json", "r+") as file:
            try:
                # Acquire an exclusive lock for both reading and writing
                fcntl.flock(file, fcntl.LOCK_EX)

                lines = [
                    line
                    for line in file
                    if all(
                        f'"request_id": "{request_id}"' not in line
                        for request_id in request_ids
                    )
                ]

                # Move the file pointer to the beginning and truncate the file
                file.seek(0)
                file.truncate()

                # Write the filtered lines back to the file
                file.writelines(lines)
                file.flush()

            finally:
                # Release the lock
                fcntl.flock(file, fcntl.LOCK_UN)
