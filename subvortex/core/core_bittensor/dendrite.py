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
import aiohttp
import asyncio
import traceback

import bittensor.utils.btlogging as btul

import bittensor.core.axon as btca
import bittensor.core.dendrite as btcd
import bittensor.core.settings as btcs

from subvortex.core.core_bittensor.synapse import TerminalInfo, Synapse


class SubVortexDendrite(btcd.Dendrite):
    def __init__(self, version, wallet=None):
        super().__init__(wallet=wallet)
        self.version = version

    def _get_endpoint_url(self, target_axon, request_name):
        """
        Constructs the endpoint URL for a network request to a target axon.

        This internal method generates the full HTTP URL for sending a request to the specified axon. The
        URL includes the IP address and port of the target axon, along with the specific request name. It
        differentiates between requests to the local system (using '0.0.0.0') and external systems.

        Args:
            target_axon: The target axon object containing IP and port information.
            request_name: The specific name of the request being made.

        Returns:
            str: A string representing the complete HTTP URL for the request.
        """
        endpoint = (
            f"0.0.0.0:{target_axon.port}"
            if target_axon.ip == str(self.external_ip)
            else f"{target_axon.ip}:{target_axon.port}"
        )
        return f"http://{endpoint}/{request_name}"

    def preprocess_synapse_for_request(
        self,
        target_axon_info: btca.AxonInfo,
        synapse: Synapse,
        timeout: float = 12.0,
    ) -> btca.Synapse:
        """
        Pre process the synapse before sending the request to the miner
        """
        # Set the timeout for the synapse
        synapse.timeout = timeout

        # Build the Dendrite headers using the local system's details
        synapse.dendrite = TerminalInfo(
            ip=self.external_ip,
            version=btcs.version_as_int,
            neuron_version=self.version,
            nonce=time.time_ns(),
            uuid=self.uuid,
            hotkey=self.keypair.ss58_address,
        )

        # Build the Axon headers using the target axon's details
        synapse.axon = btca.TerminalInfo(
            ip=target_axon_info.ip,
            port=target_axon_info.port,
            hotkey=target_axon_info.hotkey,
        )

        # Sign the request using the dendrite, axon info, and the synapse body hash
        message = f"{synapse.dendrite.nonce}.{synapse.dendrite.hotkey}.{synapse.axon.hotkey}.{synapse.dendrite.uuid}.{synapse.body_hash}"
        synapse.dendrite.signature = f"0x{self.keypair.sign(message).hex()}"

        return synapse


import asyncio
import traceback
import aiohttp


async def close_dendrite(dendrite: btcd.Dendrite):
    try:
        session: aiohttp.ClientSession = await dendrite.session
        connector = getattr(session, "_connector", None)

        if session.closed:
            btul.logging.debug("Session is already closed.")
            return

        # Step 1: Attempt to release all connection handlers (aggressive cleanup)
        if connector and hasattr(connector, "_conns"):
            try:
                btul.logging.debug(
                    "Releasing all idle connections from connector._conns..."
                )
                for key, handlers in connector._conns.items():
                    for handler in handlers:
                        try:
                            transport = getattr(handler, "transport", None)
                            if transport:
                                transport.close()
                        except Exception as h_ex:
                            btul.logging.debug(
                                f"Failed to close handler transport: {h_ex}"
                            )
            except Exception as ex:
                btul.logging.warning(f"Error while releasing idle connections: {ex}")

        # Step 2: Cancel any tasks using this session (helps unblock .close())
        cancelled = 0
        for task in asyncio.all_tasks():
            coro = getattr(task, "_coro", None)
            if coro and session in getattr(coro, "cr_frame", {}).f_locals.values():
                task.cancel()
                cancelled += 1
        btul.logging.debug(f"Cancelled {cancelled} tasks using session.")

        # Step 3: Forcibly close the connector FIRST (prevent future hangs)
        if connector:
            try:
                btul.logging.debug(
                    "Forcibly closing connector before session.close()..."
                )
                connector.close()
                btul.logging.debug("Connector forcibly closed.")
            except Exception as conn_ex:
                btul.logging.error(f"Failed to forcibly close connector: {conn_ex}")

        # Step 4: Close session with timeout — will never hang
        try:
            btul.logging.debug("Attempting session.close() with timeout...")
            await session.close()
            btul.logging.debug("Session.close() finished successfully.")
        except asyncio.TimeoutError:
            btul.logging.error("session.close() timed out after 3 seconds.")
        except Exception as close_ex:
            btul.logging.error(f"Exception during session.close(): {close_ex}")
            btul.logging.debug(traceback.format_exc())

    except Exception as ex:
        btul.logging.error(f"Unexpected error in close_dendrite(): {ex}")
        btul.logging.debug(traceback.format_exc())
