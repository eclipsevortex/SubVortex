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
import subvortex.core.utils as scsu


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
        self.run_complete = asyncio.Event()

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
        has_missing_country = False

        btul.logging.info(
            "🚀 MetagraphObserver service starting...",
            prefix=self.settings.logging_name,
        )
        btul.logging.debug(f"Settings: {self.settings}")

        # Load the neurons
        neurons = await self.database.get_neurons()

        # Build the current axons
        axons = {x.hotkey: x.ip for x in neurons.values()}

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
                        await self._has_new_neuron_registered(registration_count)
                    )

                    # Detect if any neuron IP has changed
                    has_axons_changed, new_axons = await self._has_neuron_ip_changed(
                        axons
                    )

                    # Determine whether a resync is needed
                    time_to_resync = block - last_synced_block >= sync_interval
                    must_resync = (
                        not ready
                        or has_new_registration
                        or has_axons_changed
                        or has_missing_country
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
                    elif has_missing_country:
                        reason = "missing country"
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
                    axons, has_missing_country = await self._resync()

                    # Store the sync block
                    last_synced_block = block

                    # Notify listener the metagraph is ready
                    ready = await self._notify_if_needed(ready)

                    # Store the new axons
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
            # Flag metagraph as unready and notify
            if not self.settings.dry_run:
                await self.database.mark_as_unready()
                await self.database.notify_state()

            # Signal run completed
            self.run_complete.set()
            btul.logging.info(
                "🛑 MetagraphObserver service exiting...",
                prefix=self.settings.logging_name,
            )

    async def stop(self):
        """
        Signals the observer to stop and waits for the loop to exit cleanly.
        """
        # Signal the service to exit
        self.should_exit.set()

        # Wait until service has finished
        await self.run_complete.wait()

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
        has_missing_country = False

        stored_neurons = await self.database.get_neurons()
        btul.logging.debug(
            f"💾 Neurons loaded from Redis: {len(stored_neurons)}",
            prefix=self.settings.logging_name,
        )

        mhotkeys = set()
        for mneuron in self.metagraph.neurons:
            new_axons[mneuron.hotkey] = mneuron.axon_info.ip

            # Get the current neuron
            current_neuron = next(
                (n for n in stored_neurons.values() if n.uid == mneuron.uid), None
            )

            # Create teh new neuron from the metagraph
            new_neuron = scmm.Neuron.from_proto(mneuron)

            # Set the country for the new neuron
            country = (
                current_neuron.country
                # The is a country for an ip that has not changed
                if current_neuron
                and current_neuron.ip == new_neuron.ip
                and current_neuron.country is not None
                else (
                    # Get the country for the ip if provided
                    sccc.get_country(new_neuron.ip)
                    if new_neuron.ip != "0.0.0.0" and scsu.is_valid_ipv4(new_neuron.ip)
                    else None
                )
            )
            new_neuron.country = country

            # Add the hotkey of the neuron
            mhotkeys.add(new_neuron.hotkey)

            # True if the neuron should have a country set
            has_country_none = (
                current_neuron
                and current_neuron.country is None
                and current_neuron.ip != "0.0.0.0"
                and scsu.is_valid_ipv4(new_neuron.ip)
            )

            if new_neuron == current_neuron and not has_country_none:
                btul.logging.trace(
                    f"🔍 Neuron {mneuron.hotkey} (uid={mneuron.uid}) unchanged",
                    prefix=self.settings.logging_name,
                )
                continue

            hotkey_changed = False
            ip_changed = False

            # Check if hotkey has changed
            if current_neuron and current_neuron.hotkey != new_neuron.hotkey:
                hotkey_changed = True
                btul.logging.debug(
                    f"🔁 Hotkey change detected for Neuron uid={new_neuron.uid}: {current_neuron.hotkey} -> {new_neuron.hotkey}",
                    prefix=self.settings.logging_name,
                )
                neurons_to_delete.append(current_neuron)

            # Check if ip has changed
            if current_neuron and current_neuron.ip != new_neuron.ip:
                ip_changed = True
                btul.logging.debug(
                    f"🌍 IP change detected for Neuron uid={new_neuron.uid} (hotkey={new_neuron.hotkey}): {current_neuron.ip} -> {new_neuron.ip}",
                    prefix=self.settings.logging_name,
                )

            # Check if country is currently not set
            if has_country_none:
                btul.logging.debug(
                    f"🌐 Missing country for Neuron uid={new_neuron.uid} (hotkey={new_neuron.hotkey}, IP={new_neuron.ip})",
                    prefix=self.settings.logging_name,
                )

            if (
                current_neuron
                and not hotkey_changed
                and not ip_changed
                and not has_country_none
            ):
                btul.logging.debug(
                    f"⚙️ Neuron uid={new_neuron.uid} updated (hotkey={new_neuron.hotkey}) with other changes.",
                    prefix=self.settings.logging_name,
                )

                # Display the details of the changes
                mismatches = self._get_details_changed(
                    current_neuron=current_neuron, new_neuron=new_neuron
                )
                btul.logging.trace(mismatches)

            # Flag missing country if there is at least one neuron with no country but an ip
            has_missing_country = has_missing_country or (
                country is None and new_neuron.ip != "0.0.0.0"
            )

            updated_neurons.append(new_neuron)

        # 🔥 Remove neurons in Redis that are no longer in the metagraph
        stale_neurons = [
            neuron
            for hotkey, neuron in stored_neurons.items()
            if hotkey not in mhotkeys and neuron not in neurons_to_delete
        ]

        if stale_neurons:
            btul.logging.debug(
                f"🗑️ # Stale neurons removed: {len(stale_neurons)}",
                prefix=self.settings.logging_name,
            )
            btul.logging.trace(
                f"🗑️ Stale neurons: {list(stale_neurons)}",
                prefix=self.settings.logging_name,
            )
            not self.settings.dry_run and await self.database.remove_neurons(
                stale_neurons
            )

        if neurons_to_delete:
            btul.logging.debug(
                f"🗑️ # Neurons removed: {len(neurons_to_delete)}",
                prefix=self.settings.logging_name,
            )
            btul.logging.trace(
                f"🗑️ Neurons removed: {[n.hotkey for n in neurons_to_delete]}",
                prefix=self.settings.logging_name,
            )
            not self.settings.dry_run and await self.database.remove_neurons(
                neurons_to_delete
            )

        if updated_neurons:
            btul.logging.debug(
                f"🧠 # Neurons updated: {len(updated_neurons)}",
                prefix=self.settings.logging_name,
            )
            btul.logging.trace(
                f"🧠 Neurons updated: {[n.hotkey for n in updated_neurons]}",
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
        else:
            btul.logging.info(
                "✅ Metagraph is in sync with Redis — no changes detected.",
                prefix=self.settings.logging_name,
            )

        return new_axons, has_missing_country

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

    async def _has_new_neuron_registered(self, registration_count) -> tuple[bool, int]:
        new_count = await scbs.get_number_of_registration(
            subtensor=self.subtensor, netuid=self.settings.netuid
        )

        if new_count == registration_count:
            return False, registration_count

        btul.logging.debug(
            f"🆕 Neuron registration count changed: {registration_count} -> {new_count}",
            prefix=self.settings.logging_name,
        )
        return new_count > 0, new_count

    async def _has_neuron_ip_changed(
        self, axons: dict[str, str]
    ) -> tuple[bool, dict[str, str]]:
        latest_axons = await scbs.get_axons(
            subtensor=self.subtensor,
            netuid=self.settings.netuid,
        )

        changed_axons = {}

        for hotkey, latest_ip in latest_axons.items():
            old_ip = axons.get(hotkey)
            if old_ip != latest_ip:
                changed_axons[hotkey] = latest_ip
                btul.logging.debug(
                    f"📡 IP changed for {hotkey}: {old_ip} -> {latest_ip}",
                    prefix=self.settings.logging_name,
                )

        return len(changed_axons.keys()) > 0, latest_axons

    def _get_details_changed(self, new_neuron, current_neuron):
        mismatches = []

        for key, expected_value in new_neuron.__dict__.items():
            actual_value = getattr(current_neuron, key, None)
            if expected_value != actual_value:
                mismatches.append(
                    f"{key}: expected={expected_value}, actual={actual_value}"
                )

        return mismatches
