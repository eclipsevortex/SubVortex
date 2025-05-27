import time
import typing
import asyncio
from collections import Counter

import bittensor.utils.btlogging as btul
import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas

import subvortex.core.model.neuron as scmn
import subvortex.core.core_bittensor.subtensor as scbs
import subvortex.validator.core.challenger.model as ccm
import subvortex.validator.core.challenger.database as sccd
import subvortex.validator.core.challenger.scheduler as sccc
import subvortex.validator.core.challenger.settings as sccs
import subvortex.validator.core.challenger.challenges.executor as svccce
import subvortex.validator.core.model.miner as cmm


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

                # Compute the ip occurences
                ip_occurences = Counter([x.ip for x in miners])

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
                    challengees: typing.List[cmm.Miner] = [
                        m for m in miners if m.country == country
                    ]

                    # Set the start time of the block we have to wait before challenging
                    wait_block_start = time.time()

                    # Do not challenge if there are no challengers
                    challenge = None
                    if len(challengees) > 0:
                        # Wait next block to let miners proxy whitelisting the validator
                        btul.logging.debug(
                            "Waiting challengees proxy to be set up",
                            prefix=self.settings.logging_name,
                        )
                        await scbs.wait_for_block(subtensor=self.subtensor)
                        wait_block_time = time.time() - wait_block_start

                        # # Get the list of identities
                        # identities = await get_challengee_identities(
                        #     subtensor=self.subtensor,
                        #     netuid=self.config.netuid,
                        # )
                        # btul.logging.debug(
                        #     f"# of identities: {len(identities)}",
                        #     prefix=self.settings.logging_name,
                        # )

                        # Challenge the challengers
                        challenge_start_time = time.time()
                        challenges_result, challenge = (
                            await self._challenge_challengers(
                                step_index=step_index,
                                settings=self.settings,
                                ip_occurences=ip_occurences,
                                challengees=challengees,
                                identities=identities,
                            )
                        )
                        challenge_time = time.time() - challenge_start_time
                        btul.logging.debug(
                            f"[{step_index}] Challenge completed in {challenge_time} seconds",
                            prefix=self.settings.logging_name,
                        )

                        # Compute the scores
                        score_start_time = time.time()
                        await self._score_challengers(
                            step_index=step_index,
                            settings=self.settings,
                            challengees=challengees,
                            challenges_result=challenges_result,
                        )
                        score_time = time.time() - score_start_time
                        btul.logging.debug(
                            f"[{step_index}] Scoring completed in {score_time} seconds",
                            prefix=self.settings.logging_name,
                        )
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
                    await self.database.add_challenge(
                        schedule_id=step.id,
                        challenge=challenge,
                        process_time=step_time - wait_block_time,
                    )
                    btul.logging.trace(
                        f"[{step_index}] Challenge {step.id} stored",
                        prefix=self.settings.logging_name,
                    )

                    # Notify analytic
                    # hotkeys = [x.hotkey for x in challengers]
                    # await self.database.notify_analytic(
                    #     "challenge",
                    #     schedule_id=step.id,
                    #     hotkeys=",".join(hotkeys),
                    # )
                    # btul.logging.trace(
                    #     f"[{step_index}] Challenge {step.id} sent",
                    #     prefix=self.settings.logging_name,
                    # )

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

    async def _challenge_challengers(
        self,
        step_index: int,
        settings: sccs.Settings,
        ip_occurences: Counter,
        challengees: typing.List[cmm.Miner],
        identities: typing.Dict[str, typing.List],
    ):
        # Define the result
        checks_result = {}

        # Define the available challengers
        available_challengers = list(challengees)

        # Execute some checks
        for challenger in challengees:
            ip = challenger.ip
            hotkey = challenger.hotkey

        # Execute some checks
        for challenger in challengees:
            ip = challenger.ip
            hotkey = challenger.hotkey

            # Check the identity of the miners are set
            identity = identities.get(hotkey)
            if identity is None:
                checks_result[hotkey] = ccm.ChallengeResult.create_failed(
                    reason="Identity is not set",
                    challenge_attempts=settings.default_challenge_max_iteration,
                    avg_process_time=settings.challenge_timeout,
                )
                continue

            # Check if the ip is associated to more than 1 miner
            if ip_occurences[ip] > 1:
                checks_result[hotkey] = ccm.ChallengeResult.create_failed(
                    reason=f"{ip_occurences[ip]} miners associated with the ip {ip}",
                    challenge_attempts=settings.default_challenge_max_iteration,
                    avg_process_time=settings.challenge_timeout,
                )
                continue

            # Check there are some challenges for the different node!

        # Filter out challengers that failed the different checks
        available_challengers = list(
            set(available_challengers)
            - set([x for x in available_challengers if x.hotkey in checks_result])
        )

        challenge = None
        challenges_result = {}
        if len(available_challengers) > 0:
            # Execute challenge
            challenges_result, challenge = await svccce.execute_challenge(
                settings=settings,
                subtensor=self.subtensor,
                challengers=available_challengers,
                nodes=identities,
            )
        else:
            btul.logging.warning(
                f"[{step_index}] Skip the challenge as no challengers have nodes registered",
                prefix=self.settings.logging_name,
            )

        # Build result
        result = {
            **checks_result,
            **challenges_result,
        }

        return result, challenge

    async def _score_challengers(
        self,
        step_index: int,
        settings: sccs.Settings,
        challengees: typing.List[cmm.Miner],
        challenges_result: typing.Dict[str, ccm.ChallengeResult],
    ):
        # Compute the metadata
        for challenger in challengees:
            # Get the miner reason for the challenger
            challenge_result: ccm.ChallengeResult = challenges_result.get(challenger.hotkey)

            # Get the score of the challenger
            score: cm.Score = scores.get(challenger.hotkey)
            score.success = challenge_result.is_successful
            score.reason = challenge_result.reason

            # Display the hotkey
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Hotkey: {challenger.hotkey}"
            )

            if challenge_result.chain:
                btul.logging.debug(
                    f"[{step_index}][{challenger.uid}] Challenge - Chain: {challenge_result.chain}, Type: {challenge_result.type}"
                )

            # Check if the miner/subtensor are verified
            if not score.success:
                btul.logging.warning(
                    f"[{step_index}][{challenger.uid}] Challenge failed - {challenge_result.reason}",
                    prefix=self.settings.logging_name,
                )

            # Availability metadata
            score.availability_attempts, score.availability_successes = (
                refresh_availability_metadata(
                    settings=settings, result=challenge_result, score=score
                )
            )

            # Reliability metadata
            score.reliability_attempts, score.reliability_successes = (
                refresh_reliability_metadata(
                    settings=settings, result=challenge_result, score=score
                )
            )

            # Latency metadata
            score.latency_times = refresh_latency_metadata(
                settings=settings, result=challenge_result, score=score
            )

            # Performance metadata
            (
                score.performance_attempts,
                score.performance_successes,
                score.performance_boost,
            ) = refresh_performance_metadata(
                settings=settings, result=challenge_result, score=score
            )

        # Compute Indivudal and Peers scores
        # Individual score: score that is computed based on the miner itself
        # Peers score: score that is computed based on the challenged miners
        for challenger in challengees:
            # Get the miner reason for the challenger
            challenge_result: ccm.ChallengeResult = challenges_result.get(challenger.hotkey)

            # Get the score of the challenger
            score: cm.Score = scores.get(challenger.hotkey)

            # Compute score for availability
            score.availability_score = compute_availability_score(score=score)
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Availability score {score.availability_score}",
                prefix=self.settings.logging_name,
            )

            # Compute score for reliability
            score.reliability_score = compute_reliability_score(score=score)
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Reliability score {score.reliability_score}",
                prefix=self.settings.logging_name,
            )

            # Compute score for latency
            score.latency_score = compute_latency_score(
                scores=scores,
                challenger=challenger,
            )
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Latency score {score.latency_score}",
                prefix=self.settings.logging_name,
            )

            # Compute score for performence
            score.performance_score = compute_performance_score(
                scores=scores,
                challenger=challenger,
            )
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Performance score {score.performance_score}",
                prefix=self.settings.logging_name,
            )

        # Computes Performance scores
        # Performance score: score that is computed based on the x top miners
        for challenger in challengees:
            # Get the miner reason for the challenger
            challenge_result: ccm.ChallengeResult = challenges_result.get(challenger.hotkey)

            # Get the score of the challenger
            score: cm.Score = scores.get(challenger.hotkey)

            # Compute score for distribution
            score.distribution_score = compute_distribution_score(
                settings=settings,
                challenger=challenger,
                scores=scores,
            )
            btul.logging.debug(
                f"[{step_index}][{challenger.uid}] Distribution score {score.distribution_score}",
                prefix=self.settings.logging_name,
            )

            # Compute final score
            score.final_score = compute_final_score(settings, score)
            btul.logging.info(
                f"[{step_index}][{challenger.uid}] Final score {score.final_score}",
                prefix=self.settings.logging_name,
            )

            # Compute the moving score
            # TODO: Take into account the fact that the miner maybe flag!
            score.moving_score = (
                settings.MOVING_SCORE_ALPHA * score.final_score
                + (1 - settings.MOVING_SCORE_ALPHA) * score.moving_score
            )
            btul.logging.info(
                f"[{step_index}][{challenger.uid}] Moving score {score.moving_score}",
                prefix=self.settings.logging_name,
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
