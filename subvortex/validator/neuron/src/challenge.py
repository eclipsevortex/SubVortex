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
import random
import asyncio
import traceback
import numpy as np
import bittensor.core.chain_data as btccd
import bittensor.core.subtensor as btcs
import bittensor.core.settings as btcse
import bittensor.utils.btlogging as btul
from typing import Dict
from collections import Counter

from subvortex.core.constants import DEFAULT_PROCESS_TIME
from subvortex.core.protocol import Synapse
from subvortex.validator.neuron.src.miner import Miner
from subvortex.validator.neuron.src.synapse import send_scope
from subvortex.validator.neuron.src.security import (
    is_miner_suspicious,
    deregister_suspicious_uid,
)
from subvortex.validator.neuron.src.selection import get_next_uids
from subvortex.validator.neuron.src.state import log_event
from subvortex.validator.neuron.src.score import (
    compute_availability_score,
    compute_reliability_score,
    compute_latency_score,
    compute_distribution_score,
    compute_final_score,
)

CHALLENGE_NAME = "Challenge"

DEFAULT_CHALLENGE_PROCESS_TIME = 60

# Number of historic blocks a lite node has
LITE_NODE_BLOCK_UPPER_LIMIT = 10
LITE_NODE_BLOCK_LOWER_LIMIT = 256

MINER_PROPERTIES = [
    "hotkey",
    "coldkey",
    "rank",
    "emission",
    "incentive",
    "consensus",
    "trust",
    "last_update",
]

VALIDATOR_PROPERTIES = [
    "hotkey",
    "coldkey",
    "stake",
    "rank",
    "emission",
    "validator_trust",
    "dividends",
    "last_update",
]


def create_subtensor_challenge(subtensor: btcs.Subtensor):
    """
    Create the challenge that the miner subtensor will have to execute
    """
    try:

        # Get the current block from the miner subtensor
        current_block = subtensor.get_current_block()

        # Select a block between [current block - 256, current block - 10]
        block = random.randint(
            current_block - LITE_NODE_BLOCK_LOWER_LIMIT,
            current_block - LITE_NODE_BLOCK_UPPER_LIMIT,
        )
        btul.logging.trace(f"Block chosen: {block}")

        # Be sure we select a subnet that at least one neuron
        subnet_to_exclude = []
        subnet_uid = None
        neurons = []
        while len(neurons) == 0:
            if subnet_uid is not None:
                subnet_to_exclude.append(subnet_uid)

            # Select the subnet
            subnet_count = max(subtensor.get_subnets(block=block))
            subnets = [i for i in range(subnet_count + 1) if i not in subnet_to_exclude]
            subnet_uid = random.choice(subnets)

            # Select the neuron
            neurons = subtensor.neurons_lite(block=block, netuid=subnet_uid)
        btul.logging.trace(f"Subnet chosen: {subnet_uid}")

        neuron_index = random.randint(0, len(neurons) - 1)
        neuron = neurons[neuron_index]
        neuron_uid = neuron.uid
        btul.logging.trace(f"Neuron chosen: {neuron_uid}")

        # Select the property
        properties = (
            MINER_PROPERTIES if neuron.axon_info.is_serving else VALIDATOR_PROPERTIES
        )
        property_index = random.randint(0, len(properties) - 1)
        neuron_property = properties[property_index]
        btul.logging.trace(f"Property chosen: {neuron_property}")

        # Get the property value
        neuron_value = getattr(neuron, neuron_property)

        return (block, subnet_uid, neuron_uid, neuron_property, neuron_value)
    except Exception as err:
        btul.logging.warning(f"Could not create the challenge: {err}")
        btul.logging.warning(traceback.format_exc())
        return None


async def challenge_miner(self, miner: Miner):
    """
    Challenge the miner by pinging it
    """
    verified = False
    reason = None

    try:
        response = await self.dendrite(
            miner.axon,
            Synapse(),
            deserialize=False,
            timeout=5,
        )

        status_code = response.dendrite.status_code
        status_message = response.dendrite.status_message

        verified = status_code == 200
        reason = status_message

        return (verified, reason)
    except Exception as e:
        reason = f"Unexpected error occurred: {e}"

    return (verified, reason)


def challenge_subtensor(miner: Miner, challenge):
    """
    Challenge the subtensor by requesting the value of a property of a specific neuron in a specific subnet at a certain block
    """
    substrate = None
    verified = False
    reason = None
    process_time = None

    try:
        # Get the details of the challenge
        block, netuid, uid, neuron_property, expected_value = challenge

        # Attempt to connect to the subtensor
        try:
            # Create the substrate
            substrate = btcs.SubstrateInterface(
                ss58_format=btcse.SS58_FORMAT,
                use_remote_preset=True,
                type_registry=btcse.TYPE_REGISTRY,
                url=f"ws://{miner.ip}:9944",
            )

        except Exception:
            reason = "Failed to connect to Subtensor node at the given IP."
            return (verified, reason, process_time)

        # Set the socket timeout
        substrate.ws.socket.settimeout(DEFAULT_PROCESS_TIME)

        # Start the timer
        start_time = time.time()

        # Execute the challenge
        try:
            # Get the block hash
            block_hash = substrate.get_block_hash(block)

            # Get the neuron lite details
            result = substrate.runtime_call(
                "NeuronInfoRuntimeApi", "get_neuron_lite", [netuid, uid], block_hash
            )

            # Convert to a neuron entity
            neuron = btccd.NeuronInfoLite.from_dict(result.value)
        except KeyError:
            reason = "Invalid netuid or uid provided."
            return (verified, reason, process_time)
        except ValueError:
            reason = "Invalid or unavailable block number."
            return (verified, reason, process_time)
        except (Exception, BaseException):
            reason = "Failed to retrieve neuron details."
            return (verified, reason, process_time)

        # Access the specified property
        try:
            miner_value = getattr(neuron, neuron_property)
        except AttributeError:
            reason = "Property not found in the neuron."
            return (verified, reason, process_time)

        # Compute the process time
        process_time = time.time() - start_time

        # Verify the challenge
        verified = expected_value == miner_value

    except Exception as err:
        reason = f"An unexpected error occurred: {str(err)}"
    finally:
        if substrate:
            substrate.close()

    return (verified, reason, process_time)


async def handle_challenge(self, uid: int, challenge):
    btul.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Challenging...")

    # Get the miner
    miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

    # Inrement the number of challenge
    miner.challenge_attempts = miner.challenge_attempts + 1

    # Set the process time by default
    process_time: float = DEFAULT_CHALLENGE_PROCESS_TIME

    # Challenge Miner - Ping time
    btul.logging.debug(f"[{CHALLENGE_NAME}][{miner.uid}] Challenging miner")
    miner_verified, miner_reason = await challenge_miner(self, miner)
    if miner_verified:
        btul.logging.success(f"[{CHALLENGE_NAME}][{miner.uid}] Miner verified")
    else:
        btul.logging.warning(
            f"[{CHALLENGE_NAME}][{miner.uid}] Miner not verified - {miner_reason}"
        )

    # Challenge Subtensor if the miner is verified
    subtensor_verified, subtensor_reason = (False, None)
    if miner_verified:
        # Challenge Subtensor - Process time + check the challenge
        btul.logging.debug(f"[{CHALLENGE_NAME}][{miner.uid}] Challenging subtensor")
        subtensor_verified, subtensor_reason, subtensor_time = challenge_subtensor(
            miner, challenge
        )
        if subtensor_verified:
            btul.logging.success(f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor verified")
            process_time = subtensor_time
        else:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] Subtensor not verified - {subtensor_reason}"
            )

    # Flag the miner as verified or not
    miner.verified = miner_verified and subtensor_verified

    # Store the process time to complete the challenge
    miner.process_time = (
        process_time
        if miner.process_time != -1
        else (miner.process_time + process_time) / 2
    )

    # Increment the number of successful challenge
    miner.challenge_successes = miner.challenge_successes + int(miner.verified)

    return miner_reason if not miner_verified else subtensor_reason


async def challenge_data(self, block: int):
    # Get the hotkey of the validator
    val_hotkey = self.neuron.hotkey

    start_time = time.time()
    btul.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Create the challenge
    challenge = create_subtensor_challenge(self.subtensor)
    if not challenge:
        return

    btul.logging.debug(
        f"[{CHALLENGE_NAME}] Challenge created - Block: {challenge[0]}, Netuid: {challenge[1]}, Uid: {challenge[2]}: Property: {challenge[3]}, Value: {challenge[4]}"
    )

    # Select the miners
    uids = await get_next_uids(self, val_hotkey)
    btul.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Get the misbehavior miners
    suspicious_uids = self.monitor.get_suspicious_uids()
    btul.logging.debug(f"[{CHALLENGE_NAME}] Suspicious uids {suspicious_uids}")

    # Get the locations
    locations = self.country_service.get_locations()

    # Define the ip occurences
    ip_occurrences = Counter(miner.ip for miner in self.miners)

    # Execute the challenges
    tasks = []
    reasons = []
    for uid in uids:
        # Send the challenge to the miner
        tasks.append(asyncio.create_task(handle_challenge(self, uid, challenge)))
        reasons = await asyncio.gather(*tasks)

    # Initialise the rewards object
    rewards = np.zeros(len(uids), dtype=np.float32)

    btul.logging.info(f"[{CHALLENGE_NAME}] Starting evaluation")

    # Update moving_averaged_scores with rewards produced by this step.
    # alpha of 0.1 means that each new score replaces 5% of the weight of the previous weights
    alpha: float = 0.1
    btul.logging.debug(f"[{CHALLENGE_NAME}] Moving score alpha: {alpha}")

    # Create mapping uid -> miner
    uid_to_miner: Dict[int, Miner] = {miner.uid: miner for miner in self.miners}

    # Compute the scores
    for idx, (uid) in enumerate(uids):
        # Get the miner
        miner: Miner = uid_to_miner[uid]
        miner_ip_occurences = ip_occurrences.get(miner.ip, 0)

        btul.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Computing score...")
        btul.logging.debug(f"[{CHALLENGE_NAME}][{miner.uid}] Country {miner.country}")

        # Check if the miner is suspicious
        miner.suspicious, miner.penalty_factor = is_miner_suspicious(
            miner, suspicious_uids
        )
        if miner.suspicious:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] Miner is suspicious, apply penalty factor {miner.penalty_factor}"
            )

        # Check if the miner/subtensor are verified
        if not miner.verified:  # or not miner.sync:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] Not verified: {reasons[idx]}"
            )

        # Check the miner's ip is not used by multiple miners (1 miner = 1 ip)
        has_ip_conflicts = miner_ip_occurences > 1
        if has_ip_conflicts:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] {miner_ip_occurences} miner(s) associated with the ip"
            )

        # Compute score for availability
        miner.availability_score = compute_availability_score(miner, has_ip_conflicts)

        # Compute score for latency
        miner.latency_score = compute_latency_score(
            self.neuron.country, miner, self.miners, locations, has_ip_conflicts
        )

        # Compute score for reliability
        miner.reliability_score = await compute_reliability_score(
            miner, has_ip_conflicts
        )

        # Compute score for distribution
        miner.distribution_score = compute_distribution_score(
            miner, self.miners, ip_occurrences
        )

        # Compute final score
        miner.score = compute_final_score(miner)
        rewards[idx] = miner.score

        # Compute moving score
        miner.moving_score = (
            alpha * miner.score + (1 - alpha) * miner.moving_score
            if not miner.suspicious
            else miner.moving_score * miner.penalty_factor
        )

    # Create a sorted list of miner
    sorted_miners = sorted(
        self.miners, key=lambda m: (m.moving_score, -m.uid), reverse=True
    )

    # Compute the rank, display the scores details and save in database
    for idx, (uid) in enumerate(uids):
        # Get the miner
        miner: Miner = uid_to_miner[uid]
        miner_ip_occurences = ip_occurrences.get(miner.ip, 0)

        # Compute the rank of the miner
        miner.rank = next((i for i, x in enumerate(sorted_miners) if x.uid == uid), -1)

        # Display challenge details
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Availability score {miner.availability_score}"
        )
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Latency score {miner.latency_score}"
        )
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Reliability score {miner.reliability_score}"
        )
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Distribution score {miner.distribution_score}"
        )
        btul.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Final score {miner.score}")
        btul.logging.info(
            f"[{CHALLENGE_NAME}][{miner.uid}] Moving score {miner.moving_score:.6f}"
        )
        btul.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Rank {miner.rank}")

        # Save miner snapshot in database
        await self.database.update_miner(miner=miner)

        # Send the score details to the miner
        miner.version = await send_scope(self, miner, miner_ip_occurences, block)

    # Display step time
    forward_time = time.time() - start_time
    btul.logging.debug(f"[{CHALLENGE_NAME}] Challenge finished in {forward_time:.2f}s")

    # Log event
    log_event(self, uids, forward_time)