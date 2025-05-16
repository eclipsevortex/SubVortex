import asyncio
import traceback

import bittensor.utils.btlogging as btul
import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas

import subvortex.core.country.country as sccc
import subvortex.core.core_bittensor.subtensor as scbs
import subvortex.core.metagraph.models as scmm
import subvortex.core.metagraph.metagraph_storage as scms
import subvortex.miner.metagraph.src.settings as smms


class MetagraphObserver:
    """
    Periodically observes the metagraph and updates local neuron storage in Redis
    whenever neurons register, change IP/hotkey or weights/vtrust changed
    """

    def __init__(
        self,
        settings: smms.Settings,
        storage: scms.MetagraphStorage,
        subtensor: btcas.AsyncSubtensor,
        metagraph: btcm.AsyncMetagraph,
    ):
        self.settings = settings
        self.storage = storage
        self.subtensor = subtensor
        self.metagraph = metagraph

        self.should_exit = asyncio.Event()
        self.finished = asyncio.Event()

    async def start(self):
        """
        Starts the metagraph observer loop.
        Continuously checks for neuron changes and updates local storage accordingly.
        """
        registration_count = 0
        axons = {}
        ready = False
        last_synced_block = 0
        sync_interval = self.settings.sync_interval

        btul.logging.info("Service starting...", prefix=self.settings.logging_name)

        try:
            while not self.should_exit.is_set():
                try:
                    # Wait for next block to proceed
                    if not await scbs.wait_for_block(subtensor=self.subtensor):
                        continue

                    block = await self.subtensor.get_current_block()
                    btul.logging.info(
                        f"Block: #{block}", prefix=self.settings.logging_name
                    )

                    # Detect any new neuron registration
                    has_new_registration, registration_count = (
                        await self._has_new_neuron_registered(registration_count, block)
                    )

                    # Detect if any neuron IP has changed
                    has_axons_changed, new_axons = (
                        await self._has_neuron_ip_changed(axons)
                        if axons
                        else (False, {})
                    )

                    # Determine whether a resync is needed
                    time_to_resync = block - last_synced_block >= sync_interval
                    must_resync = (
                        not ready
                        or has_new_registration
                        or has_axons_changed
                        or time_to_resync
                    )

                    # Nothing changed, so we do nothing
                    if not must_resync:
                        continue

                    # Sync from chain and update Redis
                    axons = await self._resync()

                    # Update the last synced block
                    last_synced_block = block

                    # Notify listeners if this is the first successful sync
                    ready = await self._notify_if_needed(ready)

                    # Update known axons to track future IP changes
                    axons = new_axons

                except Exception as e:
                    # Catch and log any unexpected runtime errors
                    btul.logging.error(
                        f"Unhandled error: {e}", prefix=self.settings.logging_name
                    )
                    btul.logging.debug(
                        traceback.format_exc(), prefix=self.settings.logging_name
                    )

        finally:
            self.finished.set()
            btul.logging.info("Service exiting...", prefix=self.settings.logging_name)

    async def stop(self):
        """
        Signals the observer to stop and waits for the loop to exit cleanly.
        """
        self.should_exit.set()
        await self.finished.wait()
        btul.logging.info(f"Service stopped", prefix=self.settings.logging_name)

    async def _resync(self) -> dict[str, str]:
        """
        Fully resyncs the metagraph and updates the Redis neuron storage.
        - Updates changed or new neurons
        - Deletes outdated neurons (e.g., when hotkey has changed)
        - Returns a map of {hotkey: ip} to track IPs for change detection
        """
        await self.metagraph.sync(lite=False)
        btul.logging.debug("Metagraph synced", prefix=self.settings.logging_name)

        new_axons: dict[str, str] = {}
        updated_neurons: list[scmm.Neuron] = []
        neurons_to_delete: list[str] = []

        stored_neurons = await self.storage.get_neurons()

        for mneuron in self.metagraph.neurons:
            new_axons[mneuron.hotkey] = mneuron.axon_info.ip

            # Create the new neuron
            new_neuron = scmm.Neuron.from_proto(mneuron)

            # Find matching stored neuron by UID
            current_neuron = next(
                (n for n in stored_neurons if n.uid == new_neuron.uid), None
            )

            # Check if the neuron has changed
            if new_neuron == current_neuron:
                btul.logging.debug(
                    f"Unchanged neuron {mneuron.hotkey} (uid={mneuron.uid}), skipping",
                    prefix=self.settings.logging_name,
                )
                continue

            # If hotkey changed (same UID but different owner), remove old record
            if current_neuron and current_neuron.hotkey != mneuron.hotkey:
                btul.logging.debug(
                    f"Neuron uid={mneuron.uid} changed hotkey from {current_neuron.hotkey} to {mneuron.hotkey}",
                    prefix=self.settings.logging_name,
                )
                neurons_to_delete.append(current_neuron.hotkey)

            # Log if IP changed and we're about to fetch a new country
            if current_neuron and current_neuron.ip != mneuron.axon_info.ip:
                btul.logging.debug(
                    f"Neuron {mneuron.hotkey} IP changed from {current_neuron.ip} to {mneuron.axon_info.ip}, refetching country",
                    prefix=self.settings.logging_name,
                )

            # Update country only if IP changed
            country = (
                current_neuron.country
                if current_neuron and current_neuron.ip == mneuron.axon_info.ip
                else (
                    sccc.get_country(mneuron.axon_info.ip)
                    if mneuron.axon_info.ip != "0.0.0.0"
                    else None
                )
            )

            # Update the country of the new neuron
            new_neuron.country = country

            # Add the new neuron to the list of neuron to update
            updated_neurons.append(new_neuron)

        # Delete old records if needed
        if neurons_to_delete:
            btul.logging.debug(
                f"Deleting old neuron hotkeys: {neurons_to_delete}",
                prefix=self.settings.logging_name,
            )
            await self.storage.delete_neurons(neurons_to_delete)

        # Persist updated neurons
        if updated_neurons:
            btul.logging.info(
                f"# of changed neurons: {len(updated_neurons)}",
                prefix=self.settings.logging_name,
            )
            await self.storage.set_neurons(updated_neurons)

        return new_axons

    async def _notify_if_needed(self, ready):
        """
        If metagraph has not been marked ready yet, mark it and notify listeners.
        """
        if ready:
            return ready

        btul.logging.debug("Mark metagraph as ready", prefix=self.settings.logging_name)
        await self.storage.mark_as_ready()

        btul.logging.debug("Notify metagraph state", prefix=self.settings.logging_name)
        await self.storage.notify_state()

        return True

    async def _has_new_neuron_registered(
        self, registration_count, block
    ) -> tuple[bool, int]:
        """
        Checks if the registration count has increased,
        or if we're at the next adjustment block (in which case registration may have reset).
        """
        new_count = await scbs.get_number_of_registration(
            subtensor=self.subtensor, netuid=self.settings.netuid
        )

        if new_count == registration_count:
            next_block = await scbs.get_next_adjustment_block(
                subtensor=self.subtensor, netuid=self.settings.netuid
            )
            if block == next_block:
                btul.logging.debug(
                    f"At adjustment block #{block}; resetting registration count to 0",
                    prefix=self.settings.logging_name,
                )
                return False, 0
            return False, registration_count

        btul.logging.debug(
            f"New neuron registered: count changed from {registration_count} to {new_count}",
            prefix=self.settings.logging_name,
        )
        return True, new_count

    async def _has_neuron_ip_changed(
        self, axons: dict[str, str]
    ) -> tuple[bool, dict[str, str]]:
        """
        Detects whether any IP addresses have changed for the tracked axons.
        """
        if not axons:
            return False, {}

        latest_axons = await scbs.get_axons(
            subtensor=self.subtensor,
            netuid=self.settings.netuid,
            hotkeys=axons.keys(),
        )

        for hotkey, ip in latest_axons.items():
            if axons.get(hotkey) != ip:
                btul.logging.debug(
                    f"Axon IP changed for {hotkey}: {axons[hotkey]} -> {ip}",
                    prefix=self.settings.logging_name,
                )
                return True, latest_axons

        return False, latest_axons
