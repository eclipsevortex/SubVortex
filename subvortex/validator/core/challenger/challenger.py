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
from subvortex.core.model.neuron import Neuron
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

        previous_last_update = 0
        challengees = challengers = []
        while not self.should_exit.is_set():
            try:
                # Ensure the metagraph is ready
                btul.logging.debug(
                    "Ensure metagraph readiness", prefix=self.settings.logging_name
                )
                await self.database.wait_until_ready(
                    name="metagraph", event=self.should_exit
                )

                # Check registration
                btul.logging.debug(
                    "Checking registration...", prefix=self.settings.logging_name
                )
                await wait_until_registered(database=self.database, hotkey=self.hotkey)

                # Get the current block
                current_block = await self.subtensor.get_current_block()
                btul.logging.debug(
                    f"📦 Block #{current_block}", prefix=self.settings.logging_name
                )

                # Get the last time neurons have been updated
                last_updated = await self.database.get_neuron_last_updated()
                btul.logging.debug(
                    f"Metagraph last update: {last_updated}",
                    prefix=self.settings.logging_name,
                )

                # Compute the cutoff
                sync_cutoff = last_updated + self.settings.metagraph_sync_interval + 25
                btul.logging.debug(
                    f"Metagraph sync cutoff: {sync_cutoff}",
                    prefix=self.settings.logging_name,
                )

                # Check is metagraph has been updated within its sync interval
                if current_block > sync_cutoff:
                    btul.logging.warning(
                        f"⚠️ Metagraph may be out of sync! Last update was at block {last_updated}, "
                        f"but current block is {current_block}. Ensure your metagraph is syncing properly.",
                        prefix=self.settings.logging_name,
                    )
                    await asyncio.sleep(1)
                    continue

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

                    # Get min stake to set weight
                    min_stake = await scbs.get_weights_min_stake(
                        subtensor=self.subtensor
                    )
                    btul.logging.debug(f"Minimum stake to set weights: {min_stake}")

                    # Get the list of challengees
                    challengees = self._get_challengees(
                        neurons=neurons, hotkey=self.hotkey, min_stake=min_stake
                    )
                    btul.logging.debug(
                        f"# of challengees: {len(challengees)}",
                        prefix=self.settings.logging_name,
                    )

                    # Get the list of challengers
                    challengers = await self._get_challengers(
                        neurons=neurons, hotkey=self.hotkey, min_stake=min_stake
                    )
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
                ip_counter = Counter(x.ip for x in challengees)

                # Get the current block
                current_block = await self.subtensor.get_current_block()

                # Get next schedule (step and country)
                step, country = planner.get_next_step2(
                    settings=self.settings,
                    block=current_block,
                    challengers=challengers,
                    countries=countries,
                )

                # Waiting until the step starts
                btul.logging.debug(
                    f"Waiting for step {step.step_index} to start at block #{step.start}",
                    prefix=self.settings.logging_name,
                )
                await self.subtensor.wait_for_block(block=step.start)

                # Get challengees for the current step
                step_challengees = [m for m in challengees if m.country == step.country]
                btul.logging.info(
                    f"[{step.step_index}] Starting challenge for country: {step.country} with {len(step_challengees)} challengees",
                    prefix=self.settings.logging_name,
                )

                # Check if there are no challengees, display a warning message
                if not step_challengees:
                    btul.logging.warning(
                        f"[{step.step_index}] No miners to challenge in {step.country}",
                        prefix=self.settings.logging_name,
                    )
                    continue

                # Load the challengees identity
                identities = await sci.get_challengee_identities(
                    subtensor=self.subtensor,
                    netuid=self.settings.netuid,
                )

                # Challenge all the challengees
                results, challenge = await self.executor.run(
                    step_id=step.id,
                    step_index=step.step_index,
                    challengees=step_challengees,
                    identities=identities,
                    ip_counter=ip_counter,
                )
                btul.logging.debug(
                    f"[{step.step_index}] Executed challenge: {len(results)} results returned",
                    prefix=self.settings.logging_name,
                )

                # Score all the challengees
                await self.scorer.run(
                    step_index=step.step_index,
                    challengees=step_challengees,
                    results=results,
                )
                btul.logging.debug(
                    f"[{step.step_index}] Scoring completed for {len(step_challengees)} challengees",
                    prefix=self.settings.logging_name,
                )

                # Save the challengees result

                # Send the challengees result

                # Wait until the step ends
                btul.logging.debug(
                    f"Waiting for step {step.step_index} to finish at block #{step.stop}",
                    prefix=self.settings.logging_name,
                )
                await self.subtensor.wait_for_block(block=step.stop)

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

    async def _get_challengers(
        self,
        settings: Settings,
        neurons: List[Neuron],
        hotkey: str,
        min_stake: int,
    ):

        # Get the maximum allowed validators
        max_validators = await scbs.get_max_allowed_validators(
            subtensor=self.subtensor, netuid=self.settings.netuid
        )
        btul.logging.trace(f"Max allowed validators: {max_validators}")

        # Get the list of challengers sorted by stake
        challengers = sorted(
            {
                x
                for x in neurons
                if x.validator_trust > 0
                or x.hotkey == hotkey
                or (not settings.is_test and x.stake >= min_stake)
            },
            key=lambda x: x.stake,
            reverse=True,
        )
        btul.logging.trace(f"# of potential challengers: {len(challengers)}")

        return challengers[:max_validators]

    def _get_challengees(
        self, settings: Settings, neurons: List[Neuron], hotkey: str, min_stake: int
    ):
        return [
            x
            for x in neurons
            if x.validator_trust == 0
            and x.hotkey != hotkey
            and (settings.is_test or x.stake < min_stake)
        ]
