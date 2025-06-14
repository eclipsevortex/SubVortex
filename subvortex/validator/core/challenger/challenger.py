# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import asyncio
import traceback
import bittensor.utils.btlogging as btul
from typing import List
from collections import Counter

import bittensor.core.async_subtensor as btcas

import subvortex.core.identity as sci
import subvortex.core.shared.substrate as scss
import subvortex.core.core_bittensor.subtensor as scbs

from subvortex.core.model.schedule import Schedule
from subvortex.core.scheduler import scheduler_planner as planner
from subvortex.core.shared.neuron import wait_until_registered
from subvortex.validator.core.challenger.miner import sync_miners
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.challenger.database import Database
from subvortex.validator.core.challenger.challenge_executor import ChallengeExecutor
from subvortex.validator.core.challenger.challenge_scorer import ChallengeScorer
from subvortex.validator.core.challenger.utils import extract_countries


class Challenger:
    """
    Orchestrates the challenge lifecycle: scheduling, execution, and scoring.
    Continuously monitors for new blocks, then coordinates challenges across countries
    based on a scheduled plan. Helps validate and score miners.
    """

    def __init__(
        self,
        hotkey: str,
        settings: Settings,
        subtensor: btcas.AsyncSubtensor,
        database: Database,
        executor: ChallengeExecutor,
        scorer: ChallengeScorer,
        instance: int = 1,
    ):
        self.hotkey = hotkey
        self.settings = settings
        self.subtensor = subtensor
        self.database = database
        self.executor = executor
        self.scorer = scorer
        self.instance = instance
        self.should_exit = asyncio.Event()
        self.run_complete = asyncio.Event()

    async def start(self):
        btul.logging.info(
            "🚀 Challenger starting...", prefix=self.settings.logging_name
        )

        current_cycle = None
        previous_last_update = 0
        challengees = challengers = []
        while not self.should_exit.is_set():
            try:
                # Ensure the metagraph is ready
                btul.logging.debug("Ensure metagraph readiness")
                await self.database.wait_until_ready(self.should_exit, "metagraph")

                # Check registration
                btul.logging.debug("Checking registration...")
                await wait_until_registered(database=self.database, hotkey=self.hotkey)

                # Get the current block
                current_block = await self.subtensor.get_current_block()
                btul.logging.debug(
                    f"📦 Block #{current_block}", prefix=self.settings.logging_name
                )

                # Get the last time neurons have been updated
                last_updated = await self.database.get_neuron_last_updated()
                if last_updated == 0:
                    btul.logging.warning(
                        f"Could not get the neuron last updated from redis. Pleaase check your metagraph."
                    )

                # Resync data if metagraph has changed
                if previous_last_update != last_updated:
                    btul.logging.debug(
                        f"Neurons changed at block #{last_updated}, rsync miners",
                        prefix=self.settings.logging_name,
                    )

                    # Store the new last updated
                    previous_last_update = last_updated

                    # Get the list of neurons
                    neurons = await self.database.get_neurons()

                    # Refresh the validator neuron
                    neuron = neurons.get(self.hotkey)
                    btul.logging.trace(
                        f"Neuron details — Hotkey: {neuron.hotkey}, UID: {neuron.uid}, IP: {neuron.ip}"
                    )

                    # Get min stake to set weight
                    min_stake = await scss.get_weights_min_stake_async(
                        substrate=self.subtensor.substrate
                    )
                    btul.logging.debug(f"Minimum stake to set weights: {min_stake}")

                    # Sync miners
                    miners = await sync_miners(
                        settings=self.settings,
                        database=self.database,
                        neurons=neurons,
                        miners=challengees,
                        validator=neuron,
                        min_stake=min_stake,
                    )

                    # Get the list of challengees
                    challengees = list(miners)
                    btul.logging.debug(
                        f"# of challengees: {len(challengees)}",
                        prefix=self.settings.logging_name,
                    )

                    # Get the list of challengers
                    hotkeys = [x.hotkey for x in challengees]
                    challengers = [
                        n for n in neurons.values() if n.hotkey not in hotkeys
                    ]
                    btul.logging.debug(
                        f"# of challengers: {len(challengers)}",
                        prefix=self.settings.logging_name,
                    )

                # Extract the list of country from the challengees
                countries = extract_countries(challengees=challengees)
                btul.logging.debug(
                    f"Countries with eligible miners: {sorted(countries)}",
                    prefix=self.settings.logging_name,
                )

                # Create challengee ip counter
                ip_counts = Counter(x.ip for x in challengees)

                # Compute new cycle if none or cycle expired
                if current_cycle is None or current_block >= current_cycle.stop:
                    current_cycle = planner.get_next_cycle(
                        settings=self.settings,
                        netuid=self.settings.netuid,
                        block=current_block,
                        countries=countries,
                    )
                    btul.logging.info(
                        f"Cycle #{current_cycle.start} - #{current_cycle.stop}",
                        prefix=self.settings.logging_name,
                    )

                # Get challenge schedule for this cycle
                schedule: List[Schedule] = await planner.get_schedule(
                    substrate=self.subtensor.substrate,
                    settings=self.settings,
                    cycle=current_cycle,
                    validators=challengers,
                    countries=countries,
                    hotkey=self.hotkey,
                    instance=self.instance,
                )
                btul.logging.info(
                    f"Fetched schedule with {len(schedule)} steps for cycle #{current_cycle.start}-{current_cycle.stop}",
                    prefix=self.settings.logging_name,
                )

                # Save the schedule in database
                await self.database.add_schedule(schedule)
                btul.logging.trace("Schedule stored", prefix=self.settings.logging_name)

                # TODO: Notify neuron schedule created

                # Determine the current step in the schedule
                step_index, next_step_start = planner.get_next_step(
                    settings=self.settings,
                    cycle=current_cycle,
                    block=current_block,
                    counter=countries,
                )

                # Waiting until the next step starts
                btul.logging.debug(
                    f"Waiting for step {step_index} to start at block #{next_step_start}",
                    prefix=self.settings.logging_name,
                )
                await self.subtensor.wait_for_block(next_step_start)

                # # Process each step in the schedule
                for step in schedule:
                    if step.step_index < step_index:
                        btul.logging.debug(
                            f"[{step.step_index}] Skipping step — already past current step_index {step_index}",
                            prefix=self.settings.logging_name,
                        )
                        continue

                    # Get challengees for the current country step
                    current_challengees = [
                        m for m in challengees if m.country == step.country
                    ]
                    btul.logging.info(
                        f"[{step.step_index}] Starting challenge for country: {step.country} with {len(current_challengees)} miners",
                        prefix=self.settings.logging_name,
                    )

                    if not current_challengees:
                        btul.logging.warning(
                            f"[{step.step_index}] No miners to challenge in {step.country}",
                            prefix=self.settings.logging_name,
                        )
                        continue

                    # Wait for next block
                    await self.subtensor.wait_for_block()

                    # Get the challengees identity
                    identities = await sci.get_challengee_identities(
                        subtensor=self.subtensor,
                        netuid=self.settings.netuid,
                    )

                    if not identities:
                        btul.logging.warning(
                            f"[{step.step_index}] No identities retrieved from subtensor for challenge",
                            prefix=self.settings.logging_name,
                        )
                    elif len(identities) != len(current_challengees):
                        btul.logging.warning(
                            f"[{step.step_index}] Mismatch: {len(current_challengees)} challengees, {len(identities)} identities",
                            prefix=self.settings.logging_name,
                        )

                    # Execute challenge and collect result
                    results, challenge = await self.executor.run(
                        step_id=step.id,
                        step_index=step.step_index,
                        challengees=current_challengees,
                        identities=identities,
                        ip_counts=ip_counts,
                    )
                    btul.logging.debug(
                        f"[{step.step_index}] Executed challenge: {len(results)} results returned",
                        prefix=self.settings.logging_name,
                    )

                    # Apply scoring to challenged miners
                    await self.scorer.run(
                        step_index=step.step_index,
                        challengees=current_challengees,
                        results=results,
                    )
                    btul.logging.debug(
                        f"[{step.step_index}] Scoring completed for {len(current_challengees)} challengees",
                        prefix=self.settings.logging_name,
                    )

                    # Save the miners in database
                    await self.database.update_miners(miners=miners)
                    btul.logging.trace(
                        f"[{step.step_index}] Miners saved",
                        prefix=self.settings.logging_name,
                    )

                    # Save the challenge in database
                    await self.database.add_challenge(challenge)
                    btul.logging.info(
                        f"[{step.step_index}] Challenge saved",
                        prefix=self.settings.logging_name,
                    )

                    # TODO: Notify neuron challenge completed

                    # Wait until this step ends
                    btul.logging.debug(
                        f"Waiting for step {step_index} to finish at block #{next_step_start}",
                        prefix=self.settings.logging_name,
                    )
                    await self.subtensor.wait_for_block(block=step.block_end)

            except AssertionError:
                # We already display a log, so need to do more here
                pass

            except Exception as ex:
                btul.logging.error(f"Unhandled exception: {ex}")
                btul.logging.debug(traceback.format_exc())

        # Signal the neuron has finished
        self.run_complete.set()

    async def stop(self):
        """
        Signals the challenger to stop and waits for the loop to exit cleanly.
        """
        btul.logging.info("Challenger finishing its work...")

        # Signal the service to exit
        self.should_exit.set()

        btul.logging.info("Challenger shutting down...")

        # Wait until service has finished
        await self.run_complete.wait()

        btul.logging.info(
            "✅ Challenger stopped successfully.", prefix=self.settings.logging_name
        )
