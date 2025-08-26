import asyncio
import traceback

import bittensor.utils.btlogging as btul
import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas

import subvortex.core.country.country as sccc
import subvortex.core.country.geolookup as scgl
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

        # Initialize ultra-fast geo lookup service if license key provided
        self.geo_lookup = (
            scgl.UltraFastGeoLookup(
                output_dir=settings.geo_output_dir,
                license_key=settings.geo_license_key,
            )
            if settings.geo_license_key
            else None
        )

    async def start(self):
        """
        Starts the metagraph observer loop.
        Continuously checks for neuron changes and updates local storage accordingly.
        """
        registration_count = 0
        axons = {}
        last_synced_block = 0
        sync_interval = self.settings.sync_interval
        has_missing_country = False

        btul.logging.info(
            "🚀 MetagraphObserver service starting...",
            prefix=self.settings.logging_name,
        )
        btul.logging.debug(
            f"Settings: {self.settings}", prefix=self.settings.logging_name
        )

        # Start the geo lookup service if available
        if self.geo_lookup:
            await self.geo_lookup.start()
            # Wait for geo data to be ready before proceeding
            btul.logging.info(
                "⏳ Waiting for GeoLite2 data to be ready...",
                prefix=self.settings.logging_name,
            )
            await self.geo_lookup.wait_for_ready(timeout=60.0)
            if self.geo_lookup.is_ready():
                btul.logging.info(
                    "✅ GeoLite2 data is ready for ultra-fast lookups",
                    prefix=self.settings.logging_name,
                )
            else:
                btul.logging.warning(
                    "⚠️ GeoLite2 data not ready - will use API fallback for country lookups",
                    prefix=self.settings.logging_name,
                )
        else:
            btul.logging.info(
                "💡 No geo license key provided - using API fallback for country lookups",
                prefix=self.settings.logging_name,
            )

        # Load the neurons
        neurons = await self.database.get_neurons()

        # Build the current axons
        axons = {x.hotkey: x.ip for x in neurons.values()}

        try:
            while not self.should_exit.is_set():
                try:

                    # Wait for either a new block OR a shutdown signal, whichever comes first.
                    done, _ = await asyncio.wait(
                        [
                            asyncio.create_task(self.subtensor.wait_for_block()),
                            asyncio.create_task(self.should_exit.wait()),
                        ],
                        timeout=24,
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Timeout, no tasks completed
                    if not done:
                        btul.logging.warning(
                            "⏲️ No new block retrieved within 24 seconds. Retrying..."
                        )
                        continue

                    # If shutdown signal is received, break the loop immediately
                    if self.should_exit.is_set():
                        break

                    # If no new block was produced (e.g., shutdown happened or something failed), skip this round
                    # This guards against the case where wait_for_block() returned None or False
                    if not any(
                        task.result()
                        for task in done
                        if not task.cancelled() and not task.exception()
                    ):
                        continue

                    block = await self.subtensor.get_current_block()
                    btul.logging.info(
                        f"📦 Block #{block}", prefix=self.settings.logging_name
                    )

                    # Detect any new neuron registration
                    has_new_registration, registration_count = (
                        await self._has_new_neuron_registered(registration_count)
                    )

                    # Detect if any neuron IP has changed
                    has_axons_changed, new_axons = await self._has_neuron_ip_changed(
                        axons
                    )

                    # Get the last udpate
                    last_update = await self.database.get_neuron_last_updated()

                    # Get the current state of the metagraph
                    state = await self.database.get_state()

                    # Determine whether a resync is needed
                    time_to_resync = block - last_synced_block >= sync_interval
                    must_resync = (
                        has_new_registration
                        or has_axons_changed
                        or has_missing_country
                        or time_to_resync
                        or last_update is None
                    )

                    if not must_resync:
                        btul.logging.debug(
                            "No changes detected; skipping sync.",
                            prefix=self.settings.logging_name,
                        )

                        # Notify listener the metagraph is ready with retry logic
                        notification_success = await self._notify_with_retry(state == "ready")
                        
                        # If notification failed after retries, force a resync
                        if not notification_success and state != "ready":
                            btul.logging.warning(
                                "🔄 Forcing resync due to persistent data consistency failure",
                                prefix=self.settings.logging_name,
                            )
                            # Don't continue - let it fall through to resync logic
                        else:
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
                    axons, has_missing_country = await self._resync(
                        last_update=last_update
                    )

                    # Store the sync block
                    last_synced_block = block

                    # Notify listener the metagraph is ready with retry logic
                    await self._notify_with_retry(state == "ready")

                    # Store the new axons
                    axons = new_axons

                except ConnectionRefusedError as e:
                    btul.logging.error(f"Connection refused: {e}")
                    await asyncio.sleep(1)

                except Exception as e:
                    btul.logging.error(
                        f"❌ Unhandled error in loop: {e}",
                        prefix=self.settings.logging_name,
                    )
                    btul.logging.debug(
                        traceback.format_exc(), prefix=self.settings.logging_name
                    )

        finally:
            # Stop the geo lookup service if it was started
            if self.geo_lookup:
                await self.geo_lookup.stop()

            # Ensure the metagraph is state as unready!
            if not self.settings.dry_run:
                btul.logging.debug(
                    f"  Metagraph marked unready", prefix=self.settings.logging_name
                )
                await self.database.mark_as_unready()
                await self.database.notify_state()

            # Signal the run is completed
            self.run_complete.set()

            btul.logging.info(
                "🛑 MetagraphObserver service exiting...",
                prefix=self.settings.logging_name,
            )

    async def stop(self):
        """
        Signals the observer to stop and waits for the loop to exit cleanly.
        """
        btul.logging.info(
            f"MetagraphObserver stopping...", prefix=self.settings.logging_name
        )

        # Signal the service to exit
        self.should_exit.set()

        # Wait until service has finished
        await self.run_complete.wait()

        btul.logging.info(
            f"✅ MetagraphObserver service stopped", prefix=self.settings.logging_name
        )

    async def _resync(self, last_update: bool) -> dict[str, str]:
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

            try:
                # Set the country for the new neuron
                country = (
                    current_neuron.country
                    # The is a country for an ip that has not changed
                    if current_neuron
                    and current_neuron.ip == new_neuron.ip
                    and current_neuron.country is not None
                    else (
                        # Get the country for the ip - try ultra-fast lookup first if available and ready, otherwise use API fallback
                        self._get_country_for_ip(new_neuron.ip)
                        if new_neuron.ip != "0.0.0.0"
                        and scsu.is_valid_ipv4(new_neuron.ip)
                        else None
                    )
                )

            except sccc.CountryApiException as e:
                # Handle API failures - this applies to all API fallback scenarios
                btul.logging.error(f"🚨 Country API failure: {e}")
                btul.logging.warning(
                    "⏸️ Pausing metagraph updates until APIs recover..."
                )

                # Wait for the longest rate limit to expire (ensures all APIs are available)
                if e.rate_limited:
                    max_wait = max(e.rate_limited.values())
                    btul.logging.info(
                        f"⏰ Waiting {max_wait:.0f}s for all APIs to recover..."
                    )
                    await asyncio.sleep(max_wait)
                else:
                    await asyncio.sleep(60)  # Default wait if no rate limit info

                # Keep retrying until APIs recover or user stops the program
                while not self.should_exit.is_set():
                    try:
                        test_country = self._get_country_for_ip(new_neuron.ip)
                        btul.logging.info(
                            "✅ Country APIs recovered, resuming metagraph updates"
                        )
                        country = test_country
                        break

                    except sccc.CountryApiException:
                        btul.logging.warning(
                            "❌ APIs still failing - waiting 30s before retry..."
                        )
                        await asyncio.sleep(30)

            except Exception as e:
                btul.logging.warning(
                    f"⚠️ Country lookup failed for {new_neuron.ip}: {e}"
                )
                # Use None country for this neuron and continue processing
                country = None

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

        if last_update is None or updated_neurons or neurons_to_delete:
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
            return True  # Already ready, no need to notify

        # Verify data consistency before marking as ready
        if not self.settings.dry_run:
            consistency_verified = await self._verify_data_consistency()
            if not consistency_verified:
                btul.logging.warning(
                    "❌ Data consistency check failed - will not mark as ready",
                    prefix=self.settings.logging_name,
                )
                return False

        btul.logging.debug(
            "🔔 Metagraph marked ready", prefix=self.settings.logging_name
        )
        not self.settings.dry_run and await self.database.mark_as_ready()
        btul.logging.debug(
            "📣 Broadcasting metagraph ready state", prefix=self.settings.logging_name
        )
        not self.settings.dry_run and await self.database.notify_state()

        return True

    async def _notify_with_retry(self, ready) -> bool:
        """
        Notify with retry logic using adaptive delays based on actual Redis response times.
        Returns True if successful, False if failed after all retries.
        """
        # If already ready, skip all checks
        if ready:
            return True
            
        max_retries = 3
        base_delay = 0.01  # Start with 10ms base
        
        for attempt in range(max_retries):
            # Measure how long the consistency check takes
            start_time = asyncio.get_event_loop().time()
            success = await self._notify_if_needed(ready)
            check_duration = asyncio.get_event_loop().time() - start_time
            
            if success:
                if attempt > 0:  # Only log if we actually retried
                    btul.logging.info(
                        f"✅ Data consistency verified on retry {attempt + 1} (took {check_duration*1000:.1f}ms)",
                        prefix=self.settings.logging_name,
                    )
                return True
                
            if attempt < max_retries - 1:  # Don't delay on last attempt
                # Adaptive delay: wait 2-5x the time it took for the check
                # This accounts for Redis load, network latency, etc.
                adaptive_delay = max(base_delay, check_duration * (2 + attempt * 1.5))
                
                btul.logging.debug(
                    f"🔄 Retry {attempt + 1}/{max_retries}: check took {check_duration*1000:.1f}ms, "
                    f"waiting {adaptive_delay*1000:.1f}ms...",
                    prefix=self.settings.logging_name,
                )
                await asyncio.sleep(adaptive_delay)
            else:
                btul.logging.error(
                    f"❌ Failed to verify data consistency after {max_retries} attempts "
                    f"(last check took {check_duration*1000:.1f}ms)",
                    prefix=self.settings.logging_name,
                )
        
        return False

    async def _verify_data_consistency(self) -> bool:
        """
        Verify that the number of neurons in Redis matches the metagraph.
        Uses the existing get_neurons() method for simplicity and reliability.
        Returns True if consistent, False otherwise.
        """
        try:
            # Get expected count from metagraph (we already have this in memory)
            expected_count = len(self.metagraph.neurons)
            
            # Get actual neurons from Redis using existing method
            neurons = await self.database.get_neurons()
            actual_count = len(neurons)
            
            # Only log when there's a mismatch to reduce noise
            if actual_count != expected_count:
                btul.logging.warning(
                    f"⚠️ Data inconsistency: expected {expected_count} neurons, found {actual_count} in Redis",
                    prefix=self.settings.logging_name,
                )
                return False
            
            return True
                
        except Exception as e:
            btul.logging.error(
                f"❌ Error during consistency check: {e}",
                prefix=self.settings.logging_name,
            )
            # On error, assume inconsistent to be safe
            return False

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

    def _get_country_for_ip(self, ip: str) -> str:
        """
        Get country for IP address with proper fallback logic.
        Tries ultra-fast geo lookup first if available and ready, otherwise uses API fallback.
        """
        # Try ultra-fast lookup if available and ready
        if self.geo_lookup and self.geo_lookup.is_ready():
            try:
                country = self.geo_lookup.lookup_country(ip)
                if country is not None:
                    return country
                
            except Exception as e:
                btul.logging.warning(
                    f"⚠️ Ultra-fast geo lookup failed for {ip}: {e}",
                    prefix=self.settings.logging_name,
                )
        
        # Fall back to API lookup
        return sccc.get_country(ip)
