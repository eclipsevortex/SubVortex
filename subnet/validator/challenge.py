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
import torch
import time
import random
import asyncio
import traceback
import bittensor.core.subtensor as btcs
import bittensor.core.settings as btcse
import bittensor.utils.btlogging as btul
from substrateinterface.base import SubstrateInterface

from subnet.constants import DEFAULT_PROCESS_TIME
from subnet.protocol import Synapse
from subnet.validator.models import Miner
from subnet.validator.synapse import send_scope
from subnet.validator.security import is_miner_suspicious
from subnet.validator.utils import (
    get_next_uids,
    deregister_suspicious_uid,
)
from subnet.validator.bonding import update_statistics
from subnet.validator.state import log_event
from subnet.validator.score import (
    compute_availability_score,
    compute_reliability_score,
    compute_latency_score,
    compute_distribution_score,
    compute_final_score,
)
from subnet.validator.constants import CHALLENGE_NAME
from subnet.shared.substrate import get_neuron_for_uid_lite

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
    "axon_info",
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
    "axon_info",
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
            self.metagraph.axons[miner.uid],
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
            substrate = SubstrateInterface(
                ss58_format=btcse.SS58_FORMAT,
                use_remote_preset=True,
                type_registry=btcse.TYPE_REGISTRY,
                url=f"ws://{miner.ip}:9944",
            )

        except Exception:
            reason = "Failed to connect to Subtensor node at the given IP."
            return (verified, reason, process_time)

        # Set the socket timeout
        substrate.websocket.settimeout(DEFAULT_PROCESS_TIME)

        # Start the timer
        start_time = time.time()

        # Execute the challenge
        try:
            neuron = get_neuron_for_uid_lite(
                substrate=substrate, netuid=netuid, uid=uid, block=block
            )
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

    return miner_reason if not miner_verified else subtensor_reason


async def challenge_data(self):
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
    val_hotkey = self.metagraph.hotkeys[self.uid]
    uids = await get_next_uids(self, val_hotkey)
    btul.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Get the misbehavior miners
    suspicious_uids = self.monitor.get_suspicious_uids()
    btul.logging.debug(f"[{CHALLENGE_NAME}] Suspicious uids {suspicious_uids}")

    # Get the locations
    locations = self.country_service.get_locations()

    # Execute the challenges
    tasks = []
    reasons = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_challenge(self, uid, challenge)))
        reasons = await asyncio.gather(*tasks)

    # Initialise the rewards object
    rewards: torch.FloatTensor = torch.zeros(len(uids), dtype=torch.float32).to(
        self.device
    )

    btul.logging.info(f"[{CHALLENGE_NAME}] Starting evaluation")

    # Compute the score
    for idx, (uid) in enumerate(uids):
        # Get the miner
        miner: Miner = next((miner for miner in self.miners if miner.uid == uid), None)

        btul.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Computing score...")
        btul.logging.debug(f"[{CHALLENGE_NAME}][{miner.uid}] Country {miner.country}")

        # Check if the miner is suspicious
        miner.suspicious, miner.penalty_factor = is_miner_suspicious(
            miner, suspicious_uids
        )
        if miner.suspicious:
            btul.logging.warning(f"[{CHALLENGE_NAME}][{miner.uid}] Miner is suspicious")

        # Check if the miner/subtensor are verified
        if not miner.verified:  # or not miner.sync:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] Not verified: {reasons[idx]}"
            )

        # Check the miner's ip is not used by multiple miners (1 miner = 1 ip)
        if miner.has_ip_conflicts:
            btul.logging.warning(
                f"[{CHALLENGE_NAME}][{miner.uid}] {miner.ip_occurences} miner(s) associated with the ip"
            )

        # Compute score for availability
        miner.availability_score = compute_availability_score(miner)
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Availability score {miner.availability_score}"
        )

        # Compute score for latency
        miner.latency_score = compute_latency_score(
            self.country_code, miner, self.miners, locations
        )
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Latency score {miner.latency_score}"
        )

        # Compute score for reliability
        miner.reliability_score = await compute_reliability_score(miner)
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Reliability score {miner.reliability_score}"
        )

        # Compute score for distribution
        miner.distribution_score = compute_distribution_score(miner, self.miners)
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Distribution score {miner.distribution_score}"
        )

        # Compute final score
        miner.score = compute_final_score(miner)
        rewards[idx] = miner.score
        btul.logging.info(f"[{CHALLENGE_NAME}][{miner.uid}] Final score {miner.score}")

        # Send the score details to the miner
        miner.version = await send_scope(self, miner)

        # Save miner snapshot in database
        await update_statistics(self, miner)

    btul.logging.trace(f"[{CHALLENGE_NAME}] Rewards: {rewards}")

    # Compute forward pass rewards
    scattered_rewards: torch.FloatTensor = (
        self.moving_averaged_scores.to(self.device)
        .scatter(
            0,
            torch.tensor(uids).to(self.device),
            rewards.to(self.device),
        )
        .to(self.device)
    )
    btul.logging.trace(f"[{CHALLENGE_NAME}] Scattered rewards: {scattered_rewards}")

    # Update moving_averaged_scores with rewards produced by this step.
    # alpha of 0.05 means that each new score replaces 5% of the weight of the previous weights
    alpha: float = 0.1
    self.moving_averaged_scores = alpha * scattered_rewards + (
        1 - alpha
    ) * self.moving_averaged_scores.to(self.device)
    btul.logging.trace(
        f"[{CHALLENGE_NAME}] Updated moving avg scores: {self.moving_averaged_scores}"
    )

    # Suspicious miners - moving weight to 0 for deregistration
    deregister_suspicious_uid(self.miners, self.moving_averaged_scores)
    btul.logging.trace(
        f"[{CHALLENGE_NAME}] Deregistered moving avg scores: {self.moving_averaged_scores}"
    )

    # Display step time
    forward_time = time.time() - start_time
    btul.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    # Log event
    log_event(self, uids, forward_time)
