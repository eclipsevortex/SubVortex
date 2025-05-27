import time
import typing
import asyncio
from collections import Counter

import bittensor.utils.btlogging as btul
import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas

import subvortex.core.model.neuron as scmn
import subvortex.core.core_bittensor.subtensor as scbs
import subvortex.validator.core.challenger.database as sccd
import subvortex.validator.core.challenger.scheduler as sccc
import subvortex.validator.core.challenger.settings as sccs


class Challenger:
    def __init__(
        self,
        settings: sccs.Settings,
        database: sccd.ChallengerDatabase,
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
        btul.logging.info(
            "🚀 Challenger service starting...",
            prefix=self.settings.logging_name,
        )
        btul.logging.debug(f"Settings: {self.settings}")

        try:
            current_cycle = None
            current_block = None

            while not self.should_exit.is_set():
                # Wait for next block to proceed
                if not await scbs.wait_for_block(subtensor=self.subtensor):
                    continue

                # Get the current block
                block = await self.subtensor.get_current_block()
                btul.logging.info(
                    f"📦 Block #{block} detected", prefix=self.settings.logging_name
                )

                # Get the list of neurons
                neurons = await self.database.get_neurons()
                btul.logging.info(
                    f"# of neurons: {len(neurons)}", prefix=self.settings.logging_name
                )

                # Get the list of validators and miners
                validators, miners = [], []
                for neuron in neurons:
                    items = validators if self._is_validator(neuron) else miners
                    items.append(neuron)

                btul.logging.info(
                    f"# of validators: {len(validators)}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.info(
                    f"# of miners: {len(miners)}", prefix=self.settings.logging_name
                )

                # Get the list of country
                countries = self._get_countries(miners)
                btul.logging.debug(
                    f"# of country: {len(countries)}",
                    prefix=self.settings.logging_name,
                )

                # Compute the next cycle if needed
                if current_cycle is None or current_block >= current_cycle.stop:
                    current_cycle = sccc.get_next_cycle(
                        settings=self.settings,
                        netuid=self.settings.netuid,
                        block=current_block,
                        countries=countries,
                    )
                    btul.logging.debug(
                        f"Current cycle #{current_cycle.start} - #{current_cycle.stop}",
                        prefix=self.settings.logging_name,
                    )

                # Get the next step and so the next country to challenge
                schedule = await sccc.get_schedule(
                    substrate=self.subtensor.substrate,
                    settings=self.settings,
                    cycle=current_cycle,
                    validators=validators,
                    countries=countries,
                    hotkey=self.wallet.hotkey.ss58_address,
                    instance=1,  # TODO: index of the challenger instance as we can have multiple of them
                )
                btul.logging.debug(
                    f"Schedule: {[(x.country, x.block_start, x.block_end) for x in schedule]}",
                    prefix=self.settings.logging_name,
                )

                # Store the schedule
                await self.database.add_schedule(schedule=schedule)
                btul.logging.trace(
                    f"Schedule stored",
                    prefix=self.settings.logging_name,
                )

                # Compute the next step and the block where to start it
                next_step, next_step_start = sccc.get_next_step(
                    settings=self.settings,
                    cycle=current_cycle,
                    block=current_block,
                    counter=countries,
                )
                btul.logging.debug(
                    f"Waiting for step {next_step} to start at block: #{next_step_start}",
                    prefix=self.settings.logging_name,
                )

                # Wait the beginning of the step
                await scbs.wait_for_block(
                    subtensor=self.subtensor, block=next_step_start
                )

                # Loop through the countries
                for step in schedule:
                    # Get the step number
                    step_index = step.step_index

                    if step_index < next_step:
                        # Skip until next step is reached
                        continue

                    # Set the start time of the step
                    step_start_time = time.time()

                    # Get the scheduled country
                    country = step.country

                    # Display the starting block
                    btul.logging.info(
                        f"[{step_index}] Step starting at block {step.block_start} and finishing at block {step.block_end} for country {country}",
                        prefix=self.settings.logging_name,
                    )

                    # Get the list of challengers for the scheduled country
                    challengers: typing.List[scmn.Neuron] = [
                        m for m in miners if m.country == country
                    ]

                    # Compute the default scores
                    default_scores = {
                        x.hotkey: cm.Score(uid=x.uid, hotkey=x.hotkey)
                        for x in challengers
                    }

                    # Get the current scores for each challenger
                    challenger_hotkeys = [x.hotkey for x in challengers]
                    scores = await self.database.get_scores(challenger_hotkeys)
                    scores = {**default_scores, **scores}
                    btul.logging.debug(
                        f"[{step_index}] Scores loaded from database",
                        prefix=self.settings.logging_name,
                    )

                    # Set the start time of the block we have to wait before challenging
                    wait_block_start = time.time()

                    # Do not challenge if there are no challengers
                    challenge = None
                    if len(challengers) > 0:
                        pass
                    else:
                        wait_block_time = time.time() - wait_block_start

                        btul.logging.warning(
                            f"[{step_index}] No challenge executed as no challengers are available",
                            prefix=self.settings.logging_name,
                        )

                    # Display step time
                    step_time = time.time() - step_start_time
                    btul.logging.debug(
                        f"[{step_index}] Step finished in {step_time:.2f}s",
                        prefix=self.settings.logging_name,
                    )

                    # Store the challenge
                    await self.database.set_challenge(
                        schedule_id=step.id,
                        challenge=challenge,
                        process_time=step_time - wait_block_time,
                    )
                    btul.logging.trace(
                        f"[{step_index}] Challenge {step.id} stored",
                        prefix=self.settings.logging_name,
                    )

                    # Notify analytic
                    await self.database.notify_analytic(
                        "challenge",
                        schedule_id=step.id,
                        hotkeys=",".join(challenger_hotkeys),
                    )
                    btul.logging.trace(
                        f"[{step_index}] Challenge {step.id} sent",
                        prefix=self.settings.logging_name,
                    )

                    btul.logging.debug(
                        f"[{step_index}] Waiting until block: #{step.block_end}",
                        prefix=self.settings.logging_name,
                    )

                    # Wait until the end of the step
                    await scbs.wait_for_block(
                        subtensor=self.subtensor, block=step.block_end
                    )

        finally:
            self.finished.set()
            btul.logging.info(
                "🛑 Challenger service exiting...",
                prefix=self.settings.logging_name,
            )

    async def stop(self):
        """
        Signals the challenger to stop and waits for the loop to exit cleanly.
        """
        self.should_exit.set()
        await self.finished.wait()
        btul.logging.info(
            f"✅ MetagraphObserver service stopped", prefix=self.settings.logging_name
        )

    def _is_validator(neuron: scmn.Neuron):
        return neuron.validator_trust > 0 and neuron.stake >= 1000

    def _get_countries(
        self, neurons: typing.List[scmn.Neuron]
    ) -> typing.Dict[str, int]:
        # Count how many times each value appears in the list
        country_counter = Counter([x.country for x in neurons if x.country != ""])

        # Build the list of countries
        countries = sorted(
            set(
                [
                    (x.country, country_counter[x.country])
                    for x in neurons
                    if x.country in country_counter.keys()
                ]
            )
        )

        return countries
