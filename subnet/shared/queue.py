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
import time
import queue
import threading
import bittensor.utils.btlogging as btul

MAX_QUEUE_SIZE = 50000


class DynamicQueueManager:
    def __init__(self, maxsize=MAX_QUEUE_SIZE):
        self.queues = [queue.PriorityQueue(maxsize=maxsize)]
        self.lock = threading.Lock()
        self.maxsize = maxsize
        self.sequence = 0
        self.queue_count = 1
        self.previous_count = 1

    def put(self, item):
        with self.lock:
            # Attach the sequence number to the item
            try:
                self.queues[-1].put_nowait((self.sequence, item))
                self.sequence += 1
            except queue.Full:
                self._add_queue()
                self.queues[-1].put_nowait((self.sequence, item))
                self.sequence += 1

    def get(self, timeout=None):
        """
        Get the next element from the queues
        """
        while True:
            with self.lock:
                for q in self.queues:
                    if not q.empty():
                        try:
                            # Return only the item, not the sequence number
                            return q.get(timeout=timeout)[1]
                        except queue.Empty:
                            pass

            # Avoid busy-waiting
            time.sleep(timeout if timeout else 0.001)

    def cleanup(self):
        """
        Remove the queues empty and ensure at least one is available
        """
        with self.lock:
            queues = [q for q in self.queues if not q.empty()]

            # Ensure at least one queue exists
            self.queues = queues if len(queues) > 0 else [self.queues[0]]

            # Log if the number of queues has changed
            new_count = len(self.queues)
            if new_count != self.queue_count:
                self.queue_count = new_count
                self._log_queue_count()

    def clear_all_queues(self):
        with self.lock:
            for q in self.queues:
                while not q.empty():
                    try:
                        q.get_nowait()
                    except queue.Empty:
                        break

    def _add_queue(self):
        self.queues.append(queue.PriorityQueue(maxsize=self.maxsize))
        self.queue_count += 1
        self._log_queue_count()

    def _log_queue_count(self):
        if self.queue_count == self.previous_count:
            return

        details = [(index, queue.qsize()) for index, queue in enumerate(self.queues)]
        btul.logging.debug(f"# of queues: {self.queue_count} - {details}")
        self.previous_count = self.queue_count
