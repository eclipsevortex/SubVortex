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
import time
import json
import queue
import threading
import traceback
import bittensor.utils.btlogging as btuli
from typing import Dict, List
from datetime import timedelta

from subvortex.core.shared.queue import DynamicQueueManager
from subvortex.core.sse.sse_server import SSEServer

FILENAME = "firewall-events.json"


def load_events():
    events = []
    if not os.path.exists("firewall-events.json"):
        return events

    content = None
    with open("firewall-events.json", "r") as file:
        content = file.read()

    lines = content.split("\n")
    for line in lines:
        if not line.strip():
            continue

        events.append(json.loads(line))

    return events


class FirewallMonitor(threading.Thread):
    def __init__(self, sse: SSEServer = None, batch_size=500, poll_interval=1) -> None:
        super().__init__(daemon=True)

        self._stop = threading.Event()

        self._queue_manager = DynamicQueueManager()
        self._sse = sse

        self.batch_size = batch_size
        self.poll_interval = poll_interval

        self.packet_emit = 0
        self.packet_emit_start = None

        self.packet_consume = 0
        self.packet_consume_start = None

    def stop(self):
        # Signal the thread to stop
        self._stop.set()
        # Clean all queues
        self._queue_manager.clear_all_queues()
        # Clean sse
        self._sse.shutdown_server()
        # Wait for the thread to complete
        self.join()

    def run(self):
        """
        Process all events received in the queue and handle them appropriately.
        """
        try:
            # Ensure the file exists
            if not os.path.exists(FILENAME):
                with open(FILENAME, "a"):
                    pass

            # Initialise the timers
            self.packet_consume_start = time.time()
            self.packet_emit_start = time.time()

            while not self._stop.is_set():
                events = []

                while len(events) < self.batch_size:
                    try:
                        # Get next event, wait self.poll_interval if none
                        event = self._queue_manager.get(timeout=self.poll_interval)
                        if event is None:
                            break

                        # Send the event to the streamed queue
                        self._broadcast(event)

                        # Log the number of packets consumed
                        self._log_packets_consumed()

                        # Append the new even to the batch
                        events.append(event)
                    except queue.Empty:
                        break

                if len(events) == 0:
                    continue

                # Process all events in a single file operation
                self._process_events(events)

                # Clean the queues
                self._queue_manager.cleanup()
        except Exception as e:
            btuli.logging.error(f"[Firewall] Error in FirewallMonitor thread: {e}")
            btuli.logging.error(traceback.format_exc())

    def emit(self, event: dict):
        self._log_packets_emitted()
        self._queue_manager.put({"type": "log", "data": event})

    def clean(self, sources: Dict[str, List]):
        self._log_packets_emitted()
        self._queue_manager.put({"type": "clean", "data": sources})

    def _broadcast(self, event):
        try:
            # Send the stored events when new client
            if self._sse.has_new_subscribers("firewall"):
                events = load_events()
                self._sse.broadcast("firewall", {"type": "log", "data": events}, True)

            # Broadcast the event to the firewall stream
            self._sse.broadcast("firewall", event)
        except Exception as err:
            btuli.logging.error(f"[Firewall] Broadcasting failed {err}")
            btuli.logging.error(traceback.format_exc())
            pass

    def _process_events(self, events: List[dict]):
        """
        Process multiple log and clean events in one file operation.
        """
        log_events = [e["data"] for e in events if e.get("type") == "log"]
        request_ids = [x for e in events for x in e["data"] if e.get("type") == "clean"]

        with open(FILENAME, "a+") as file:
            try:
                content = None

                if len(request_ids) > 0:
                    # Read current file content
                    file.seek(0)
                    lines = file.readlines()

                    # Filter out lines with request IDs to be cleaned
                    filtered_lines = [
                        line
                        for line in lines
                        if self._should_keep_line(line, request_ids)
                    ]

                    # Convert filtered lines back to a single string
                    content = "".join(filtered_lines)

                    # Convert log_events to NDJSON format if there are any
                    if len(log_events) > 0:
                        filtered_log_events = [
                            x for x in log_events if x["request_id"] not in request_ids
                        ]
                        data = json.dumps(filtered_log_events)
                        ndjson_data = data[1:-1].replace("}, {", "}\n{") + "\n"
                        content += ndjson_data

                    # Move the file pointer to the beginning and truncate the file
                    file.seek(0)
                    file.truncate()
                elif len(log_events) > 0:
                    data = json.dumps(log_events)
                    content = data[1:-1].replace("}, {", "}\n{") + "\n"

                if not content:
                    return

                # Write the filtered lines back to the file
                file.write(content)

                # Flush the buffer
                file.flush()
            finally:
                pass

    def _should_keep_line(self, line, request_ids):
        return not any(
            f'"request_id": "{request_id}"' in line for request_id in request_ids
        )

    def _is_difference_one_hour(self, time1=0):
        time_difference = time.time() - time1
        return timedelta(seconds=time_difference) >= timedelta(hours=1)

    def _log_packets_consumed(self):
        self.packet_consume += 1

        if self._is_difference_one_hour(self.packet_consume_start):
            btuli.logging.debug(
                f"[Firewall] {self.packet_consume} packets received in the last hour"
            )
            self.packet_consume_start = time.time()
            self.packet_consume = 0

    def _log_packets_emitted(self):
        self.packet_emit += 1
        self.packet_emit_start = self.packet_emit_start

        if self._is_difference_one_hour(self.packet_emit_start):
            btuli.logging.debug(
                f"[Firewall] {self.packet_emit} packets emitted in the last hour"
            )
            self.packet_emit_start = time.time()
            self.packet_emit = 0
