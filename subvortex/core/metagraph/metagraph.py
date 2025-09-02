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
                        notification_success = await self._notify_with_retry(
                            state == "ready"
                        )

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
                    try:
                        axons, has_missing_country = await self._resync(
                            last_update=last_update
                        )

                        # Store the sync block
                        last_synced_block = block

                        # Notify listener the metagraph is ready with retry logic
                        await self._notify_with_retry(state == "ready")
                        
                    except Exception as resync_error:
                        btul.logging.error(
                            f"❌ Resync failed: {resync_error}",
                            prefix=self.settings.logging_name,
                        )
                        # Mark metagraph as unready due to resync failure
                        await self._mark_unready_on_error(f"Resync failed: {resync_error}")
                        # Continue loop to retry

                    # Store the new axons
                    axons = new_axons

                except ConnectionRefusedError as e:
                    btul.logging.error(f"Connection refused: {e}")
                    # Mark metagraph as unready due to connection issues
                    await self._mark_unready_on_error("Connection refused")
                    await asyncio.sleep(1)

                except Exception as e:
                    btul.logging.error(
                        f"❌ Unhandled error in loop: {e}",
                        prefix=self.settings.logging_name,
                    )
                    btul.logging.debug(
                        traceback.format_exc(), prefix=self.settings.logging_name
                    )
                    # Mark metagraph as unready due to unhandled error
                    await self._mark_unready_on_error(f"Unhandled error: {e}")

        finally:
            # Stop the geo lookup service if it was started
            if self.geo_lookup:
                await self.geo_lookup.stop()

            # Clean up country API rate limit data
            sccc.cleanup_all_rate_limits()

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
        old_ips_to_cleanup: list[str] = []
        has_missing_country = False

        try:
            stored_neurons = await self.database.get_neurons()
            btul.logging.debug(
                f"💾 Neurons loaded from Redis: {len(stored_neurons)}",
                prefix=self.settings.logging_name,
            )
        except Exception as e:
            btul.logging.error(
                f"❌ Failed to load neurons from Redis: {e}",
                prefix=self.settings.logging_name,
            )
            raise  # Re-raise to trigger resync failure handling

        mhotkeys = set()

        # Process neurons with retry logic for country API
        for mneuron in self.metagraph.neurons:
            new_axons[mneuron.hotkey] = mneuron.axon_info.ip

            # Get the current neuron
            current_neuron = next(
                (n for n in stored_neurons.values() if n.uid == mneuron.uid), None
            )

            # Create the new neuron from the metagraph
            new_neuron = scmm.Neuron.from_proto(mneuron)

            # Country resolution with infinite retry for API failures
            country = None
            if new_neuron.ip != "0.0.0.0" and scsu.is_valid_ipv4(new_neuron.ip):
                # Check if we can reuse existing country data
                if (
                    current_neuron
                    and current_neuron.ip == new_neuron.ip
                    and current_neuron.country is not None
                ):
                    country = current_neuron.country
                    btul.logging.trace(
                        f"🌍 Reusing country for {new_neuron.hotkey[:8]}... IP {new_neuron.ip}: {country}",
                        prefix=self.settings.logging_name,
                    )
                else:
                    # Need to get country - retry until successful
                    country = await self._get_country_with_infinite_retry(
                        new_neuron.ip, new_neuron.hotkey
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
                # Add old IP to cleanup list if it's not a placeholder IP
                if current_neuron.ip != "0.0.0.0":
                    old_ips_to_cleanup.append(current_neuron.ip)

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

            # Clean up rate limit data for stale neuron IPs
            stale_ips = [
                neuron.ip for neuron in stale_neurons if neuron.ip != "0.0.0.0"
            ]
            if stale_ips:
                sccc.cleanup_rate_limits_for_ips(stale_ips)

            try:
                not self.settings.dry_run and await self.database.remove_neurons(
                    stale_neurons
                )
            except Exception as e:
                btul.logging.error(
                    f"❌ Failed to remove stale neurons from Redis: {e}",
                    prefix=self.settings.logging_name,
                )
                raise  # Re-raise to trigger resync failure handling

        if neurons_to_delete:
            btul.logging.debug(
                f"🗑️ # Neurons removed: {len(neurons_to_delete)}",
                prefix=self.settings.logging_name,
            )
            btul.logging.trace(
                f"🗑️ Neurons removed: {[n.hotkey for n in neurons_to_delete]}",
                prefix=self.settings.logging_name,
            )

            # Remove the neurons
            try:
                not self.settings.dry_run and await self.database.remove_neurons(
                    neurons_to_delete
                )
            except Exception as e:
                btul.logging.error(
                    f"❌ Failed to remove deleted neurons from Redis: {e}",
                    prefix=self.settings.logging_name,
                )
                raise  # Re-raise to trigger resync failure handling

            # Clean up rate limit data for deleted neuron IPs
            deleted_ips = [
                neuron.ip for neuron in neurons_to_delete if neuron.ip != "0.0.0.0"
            ]
            if deleted_ips:
                sccc.cleanup_rate_limits_for_ips(deleted_ips)

        if updated_neurons:
            btul.logging.debug(
                f"🧠 # Neurons updated: {len(updated_neurons)}",
                prefix=self.settings.logging_name,
            )
            btul.logging.trace(
                f"🧠 Neurons updated: {[n.hotkey for n in updated_neurons]}",
                prefix=self.settings.logging_name,
            )
            try:
                not self.settings.dry_run and await self.database.update_neurons(
                    updated_neurons
                )
            except Exception as e:
                btul.logging.error(
                    f"❌ Failed to update neurons in Redis: {e}",
                    prefix=self.settings.logging_name,
                )
                raise  # Re-raise to trigger resync failure handling

        # Clean up rate limit data for old IPs when neurons changed IP
        if old_ips_to_cleanup:
            sccc.cleanup_rate_limits_for_ips(old_ips_to_cleanup)
            btul.logging.debug(
                f"🧹 Cleaned rate limits for {len(old_ips_to_cleanup)} old IPs after IP changes",
                prefix=self.settings.logging_name,
            )

        if last_update is None or updated_neurons or neurons_to_delete:
            block = await self.subtensor.get_current_block()
            try:
                not self.settings.dry_run and await self.database.set_last_updated(block)
                btul.logging.debug(
                    f"📅 Last updated block recorded: #{block}",
                    prefix=self.settings.logging_name,
                )
            except Exception as e:
                btul.logging.error(
                    f"❌ Failed to set last updated block in Redis: {e}",
                    prefix=self.settings.logging_name,
                )
                raise  # Re-raise to trigger resync failure handling

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

                btul.logging.debug(
                    "🔔 Metagraph marked unready", prefix=self.settings.logging_name
                )
                not self.settings.dry_run and await self.database.mark_as_unready()
                btul.logging.debug(
                    "📣 Broadcasting metagraph unready state",
                    prefix=self.settings.logging_name,
                )
                not self.settings.dry_run and await self.database.notify_state()

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
        Marks metagraph as unready if Redis operations fail.
        """
        # If already ready, skip all checks
        if ready:
            return True

        max_retries = 3
        base_delay = 0.01  # Start with 10ms base

        for attempt in range(max_retries):
            try:
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
                    # Mark as unready due to consistency failure
                    await self._mark_unready_on_error("Data consistency verification failed")

            except Exception as e:
                btul.logging.error(
                    f"❌ Redis operation failed during notify retry (attempt {attempt + 1}): {e}",
                    prefix=self.settings.logging_name,
                )
                # Mark as unready due to Redis failure
                await self._mark_unready_on_error(f"Redis operation failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (attempt + 1))

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

    async def _get_country_with_infinite_retry(
        self, ip: str, hotkey: str
    ) -> str | None:
        """
        Get country for IP with infinite retry until API works.
        Uses rate limit timing from API exceptions instead of exponential backoff.
        """
        attempt = 0

        while not self.should_exit.is_set():
            attempt += 1

            try:
                start_time = asyncio.get_event_loop().time()
                country = self._get_country_for_ip(ip)
                duration = (asyncio.get_event_loop().time() - start_time) * 1000

                if country is not None:
                    if attempt > 1:
                        btul.logging.info(
                            f"✅ Country resolved for {hotkey[:8]}... IP {ip}: {country} "
                            f"(attempt {attempt}, took {duration:.0f}ms)",
                            prefix=self.settings.logging_name,
                        )
                    else:
                        btul.logging.debug(
                            f"🌍 Country for {hotkey[:8]}... IP {ip}: {country} ({duration:.0f}ms)",
                            prefix=self.settings.logging_name,
                        )

                    return country
                else:
                    # Country API returned None - this might be a valid "no country found" result
                    if attempt == 1:
                        btul.logging.debug(
                            f"🌍 No country found for {hotkey[:8]}... IP {ip} (valid result)",
                            prefix=self.settings.logging_name,
                        )

                    return None

            except sccc.CountryApiException as e:
                # Handle API failures with proper rate limit timing
                if attempt == 1:
                    btul.logging.warning(
                        f"🌍 Country API failed for {hotkey[:8]}... IP {ip}: {e} - will retry until successful",
                        prefix=self.settings.logging_name,
                    )
                elif attempt % 10 == 0:
                    btul.logging.warning(
                        f"🌍 Country API still failing for {hotkey[:8]}... IP {ip} after {attempt} attempts: {e}",
                        prefix=self.settings.logging_name,
                    )
                else:
                    btul.logging.debug(
                        f"🌍 Country API attempt {attempt} failed for {hotkey[:8]}... IP {ip}: {e}",
                        prefix=self.settings.logging_name,
                    )

                # Check for exit condition before waiting
                if self.should_exit.is_set():
                    btul.logging.info(
                        f"🛑 Stopping country lookup for {hotkey[:8]}... due to shutdown",
                        prefix=self.settings.logging_name,
                    )
                    return None

                # Use rate limit timing from the API exception
                if e.rate_limited:
                    # Wait for the longest rate limit to expire (ensures all APIs are available)
                    max_wait = max(e.rate_limited.values())
                    btul.logging.info(
                        f"⏰ Waiting {max_wait:.0f}s for rate limits to reset for {hotkey[:8]}... IP {ip}",
                        prefix=self.settings.logging_name,
                    )
                    await asyncio.sleep(max_wait)
                else:
                    # Default wait if no rate limit info available
                    btul.logging.debug(
                        f"🔄 Retrying country lookup for {hotkey[:8]}... IP {ip} in 30s (no rate limit info)",
                        prefix=self.settings.logging_name,
                    )
                    await asyncio.sleep(30)

            except Exception as e:
                # Other non-API exceptions
                if attempt == 1:
                    btul.logging.warning(
                        f"🌍 Country lookup error for {hotkey[:8]}... IP {ip}: {e} - will retry until successful",
                        prefix=self.settings.logging_name,
                    )
                elif attempt % 10 == 0:
                    btul.logging.warning(
                        f"🌍 Country lookup still failing for {hotkey[:8]}... IP {ip} after {attempt} attempts: {e}",
                        prefix=self.settings.logging_name,
                    )
                else:
                    btul.logging.debug(
                        f"🌍 Country lookup attempt {attempt} failed for {hotkey[:8]}... IP {ip}: {e}",
                        prefix=self.settings.logging_name,
                    )

                # Check for exit condition before waiting
                if self.should_exit.is_set():
                    btul.logging.info(
                        f"🛑 Stopping country lookup for {hotkey[:8]}... due to shutdown",
                        prefix=self.settings.logging_name,
                    )
                    return None

                # For non-API exceptions, use a shorter default delay
                btul.logging.debug(
                    f"🔄 Retrying country lookup for {hotkey[:8]}... IP {ip} in 5s (non-API error)",
                    prefix=self.settings.logging_name,
                )
                await asyncio.sleep(5)

        # If we exit the loop due to should_exit being set
        return None

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

    async def _mark_unready_on_error(self, error_reason: str):
        """
        Mark metagraph as unready when errors occur and notify listeners.
        This ensures downstream services know the metagraph is in a problematic state.
        """
        try:
            if not self.settings.dry_run:
                await self.database.mark_as_unready()
                await self.database.notify_state()
                btul.logging.warning(
                    f"🚫 Metagraph marked as unready due to: {error_reason}",
                    prefix=self.settings.logging_name,
                )
        except Exception as notify_error:
            # Even if we can't mark as unready (e.g., Redis down), log the attempt
            btul.logging.error(
                f"❌ Failed to mark metagraph as unready (reason: {error_reason}): {notify_error}",
                prefix=self.settings.logging_name,
            )
