import asyncio
import traceback

import bittensor.utils.btlogging as btul
import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas

import subvortex.core.country.country as sccc
import subvortex.core.core_bittensor.subtensor as scbs
import subvortex.core.model.neuron.neuron as scmm
import subvortex.core.metagraph.database as scmd
import subvortex.core.metagraph.settings as scms


class MetagraphObserver:
    """
    Periodically observes the metagraph and updates local neuron storage in Redis
    whenever neurons register, change IP/hotkey or weights/vtrust changed
    """

    def __init__(
        self,
        settings: scms.Settings,
        database: scmd.NeuronDatabase,
        subtensor: btcas.AsyncSubtensor,
        metagraph: btcm.AsyncMetagraph,
    ):
        self.settings = settings
        self.database = database
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

        btul.logging.info(
            "🚀 MetagraphObserver service starting...",
            prefix=self.settings.logging_name,
        )
        btul.logging.debug(f"Settings: {self.settings}")

        try:
            while not self.should_exit.is_set():
                try:
                    # Wait for next block to proceed
                    if not await scbs.wait_for_block(subtensor=self.subtensor):
                        continue

                    block = await self.subtensor.get_current_block()
                    btul.logging.info(
                        f"📦 Block #{block} detected", prefix=self.settings.logging_name
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

                    if not must_resync:
                        btul.logging.debug(
                            "No changes detected; skipping sync.",
                            prefix=self.settings.logging_name,
                        )
                        continue

                    if has_axons_changed:
                        reason = "hotkey/IP changes detected"
                    elif time_to_resync:
                        reason = "periodic sync interval reached"
                    elif has_new_registration:
                        reason = "new neuron registration detected"
                    else:
                        reason = "no relevant changes"

                    btul.logging.info(
                        f"🔄 Syncing neurons due to {reason}.",
                        prefix=self.settings.logging_name,
                    )

                    # Sync from chain and update Redis
                    axons = await self._resync()
                    last_synced_block = block
                    ready = await self._notify_if_needed(ready)
                    axons = new_axons

                except Exception as e:
                    btul.logging.error(
                        f"❌ Unhandled error in loop: {e}",
                        prefix=self.settings.logging_name,
                    )
                    btul.logging.debug(
                        traceback.format_exc(), prefix=self.settings.logging_name
                    )

        finally:
            self.finished.set()
            btul.logging.info(
                "🛑 MetagraphObserver service exiting...",
                prefix=self.settings.logging_name,
            )

    async def stop(self):
        """
        Signals the observer to stop and waits for the loop to exit cleanly.
        """
        self.should_exit.set()
        await self.finished.wait()
        btul.logging.info(
            f"✅ MetagraphObserver service stopped", prefix=self.settings.logging_name
        )

    async def _resync(self) -> dict[str, str]:
        await self.metagraph.sync(subtensor=self.subtensor, lite=False)
        btul.logging.debug(
            "📡 Full metagraph sync complete", prefix=self.settings.logging_name
        )

        new_axons: dict[str, str] = {}
        updated_neurons: list[scmm.Neuron] = []
        neurons_to_delete: list[str] = []

        stored_neurons = await self.database.get_neurons()
        btul.logging.debug(
            f"💾 Neurons loaded from Redis: {len(stored_neurons)}",
            prefix=self.settings.logging_name,
        )

        for mneuron in self.metagraph.neurons:
            new_axons[mneuron.hotkey] = mneuron.axon_info.ip
            new_neuron = scmm.Neuron.from_proto(mneuron)
            current_neuron = next(
                (n for n in stored_neurons.values() if n.uid == new_neuron.uid), None
            )

            if new_neuron == current_neuron:
                btul.logging.trace(
                    f"🔍 Neuron {mneuron.hotkey} (uid={mneuron.uid}) unchanged",
                    prefix=self.settings.logging_name,
                )
                continue

            hotkey_changed = False
            ip_changed = False

            if current_neuron and current_neuron.hotkey != mneuron.hotkey:
                hotkey_changed = True
                btul.logging.debug(
                    f"🔁 Neuron UID={mneuron.uid} hotkey changed: {current_neuron.hotkey} -> {mneuron.hotkey}",
                    prefix=self.settings.logging_name,
                )
                neurons_to_delete.append(current_neuron)

            if current_neuron and current_neuron.ip != mneuron.axon_info.ip:
                ip_changed = True
                btul.logging.debug(
                    f"🌍 Neuron {mneuron.hotkey} IP changed: {current_neuron.ip} -> {mneuron.axon_info.ip}",
                    prefix=self.settings.logging_name,
                )

            if current_neuron and not hotkey_changed and not ip_changed:
                btul.logging.debug(
                    f"⚙️ Neuron {new_neuron.hotkey} (uid={new_neuron.uid}) changed",
                    prefix=self.settings.logging_name,
                )

            country = (
                new_neuron.country
                if current_neuron and current_neuron.ip == new_neuron.ip
                else (
                    sccc.get_country(mneuron.axon_info.ip)
                    if mneuron.axon_info.ip != "0.0.0.0"
                    else None
                )
            )
            new_neuron.country = country

            updated_neurons.append(new_neuron)

        if neurons_to_delete:
            btul.logging.debug(
                f"🗑️ Removing old hotkeys: {[n.hotkey for n in neurons_to_delete]}",
                prefix=self.settings.logging_name,
            )
            not self.settings.dry_run and await self.database.remove_neurons(
                neurons_to_delete
            )

        if updated_neurons:
            btul.logging.info(
                f"🧠 Neurons updated: {len(updated_neurons)}",
                prefix=self.settings.logging_name,
            )
            not self.settings.dry_run and await self.database.update_neurons(
                updated_neurons
            )

        if updated_neurons or neurons_to_delete:
            block = await self.subtensor.get_current_block()
            not self.settings.dry_run and await self.database.set_last_updated(block)
            btul.logging.debug(
                f"📅 Last updated block recorded: #{block}",
                prefix=self.settings.logging_name,
            )

        return new_axons

    async def _notify_if_needed(self, ready):
        if ready:
            return ready

        btul.logging.debug(
            "🔔 Metagraph marked ready", prefix=self.settings.logging_name
        )
        not self.settings.dry_run and await self.database.mark_as_ready()
        btul.logging.debug(
            "📣 Broadcasting metagraph ready state", prefix=self.settings.logging_name
        )
        not self.settings.dry_run and await self.database.notify_state()

        return True

    async def _has_new_neuron_registered(
        self, registration_count, block
    ) -> tuple[bool, int]:
        new_count = await scbs.get_number_of_registration(
            subtensor=self.subtensor, netuid=self.settings.netuid
        )

        if new_count == registration_count:
            if registration_count == 0:
                return False, registration_count

            next_block = await scbs.get_next_adjustment_block(
                subtensor=self.subtensor, netuid=self.settings.netuid
            )

            if block == next_block:
                btul.logging.debug(
                    f"🔄 Adjustment block #{block}; reset registration count",
                    prefix=self.settings.logging_name,
                )
                return False, 0

            return False, registration_count

        btul.logging.debug(
            f"🆕 Neuron registration count changed: {registration_count} -> {new_count}",
            prefix=self.settings.logging_name,
        )
        return True, new_count

    async def _has_neuron_ip_changed(
        self, axons: dict[str, str]
    ) -> tuple[bool, dict[str, str]]:
        if not axons:
            return False, {}

        latest_axons = await scbs.get_axons(
            subtensor=self.subtensor, netuid=self.settings.netuid, hotkeys=axons.keys()
        )

        for hotkey, ip in latest_axons.items():
            if axons.get(hotkey) != ip:
                btul.logging.debug(
                    f"📡 IP changed for {hotkey}: {axons[hotkey]} -> {ip}",
                    prefix=self.settings.logging_name,
                )
                return True, latest_axons

        btul.logging.debug(
            "✅ No IP changes detected among tracked axons",
            prefix=self.settings.logging_name,
        )
        return False, latest_axons
