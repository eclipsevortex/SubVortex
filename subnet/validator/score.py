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
import bittensor.utils.btlogging as btul
from typing import List

from subnet.validator.models import Miner
from subnet.validator.bonding import wilson_score_interval
from subnet.validator.localisation import compute_localisation_distance
from subnet.validator.constants import CHALLENGE_NAME
from subnet.constants import (
    AVAILABILITY_FAILURE_REWARD,
    RELIABILLITY_FAILURE_REWARD,
    LATENCY_FAILURE_REWARD,
    DISTRIBUTION_FAILURE_REWARD,
    AVAILABILITY_WEIGHT,
    LATENCY_WEIGHT,
    RELIABILLITY_WEIGHT,
    DISTRIBUTION_WEIGHT,
)

# Longest distance between any two places on Earth is 20,010 kilometers
MAX_DISTANCE = 20010


def check_multiple_miners_on_same_ip(miner: Miner, miners: List[Miner]):
    """
    Check if there is more than one miner per ip
    """
    count = sum(1 for item in miners if item.ip == miner.ip)
    if count > 1:
        btul.logging.warning(
            f"[{miner.uid}][Score][Multiple Ip] {count} miner(s) associated with the ip"
        )

    return count


def can_compute_availability_score(miner: Miner):
    """
    True if we can compute the availaiblity score, false to get the penalty
    """
    return miner.verified and not miner.has_ip_conflicts


def compute_availability_score(miner: Miner):
    """
    Compute the availability score of the uid
    """

    score = (
        1.0 if can_compute_availability_score(miner) else AVAILABILITY_FAILURE_REWARD
    )

    return score


def can_compute_reliability_score(miner: Miner):
    """
    True if we can compute the reliability score, false to get the penalty
    """
    return True


async def compute_reliability_score(miner: Miner):
    """
    Compute the reliaiblity score of the uid based on the the ratio challenge_successes/challenge_attempts
    """
    if not can_compute_reliability_score(miner):
        return RELIABILLITY_FAILURE_REWARD

    # Step 1: Retrieve statistics
    is_successful = miner.verified and not miner.has_ip_conflicts
    miner.challenge_successes = miner.challenge_successes + int(is_successful)
    miner.challenge_attempts = miner.challenge_attempts + 1
    btul.logging.trace(
        f"[{miner.uid}][Score][Reliability] # challenge attempts {miner.challenge_attempts}"
    )
    btul.logging.trace(
        f"[{miner.uid}][Score][Reliability] # challenge succeeded {miner.challenge_successes}"
    )

    # Step 2: Normalization
    score = wilson_score_interval(miner.challenge_successes, miner.challenge_attempts)

    return score


def can_compute_latency_score(miner: Miner):
    """
    True if we can compute the latency score, false to get the penalty
    """
    return miner.verified and not miner.has_ip_conflicts


def compute_latency_score(
    validator_country: str, miner: Miner, miners: List[Miner], locations
):
    """
    Compute the latency score of the uid based on the process time of all uids
    """
    if not can_compute_latency_score(miner):
        return LATENCY_FAILURE_REWARD

    btul.logging.trace(
        f"[{miner.uid}][Score][Latency] Process time {miner.process_time}"
    )

    # Step 1: Get the localisation of the validator
    validator_localisation = locations.get(validator_country)

    # Step 2: Compute the miners process times by adding a tolerance
    miner_index = -1
    process_times = []
    for item in miners:
        if not item.verified or item.has_ip_conflicts:
            # Exclude miners not verifed to not alterate the computation
            continue

        distance = 0
        location = locations.get(item.country)
        if location is not None and validator_localisation is not None:
            distance = compute_localisation_distance(
                validator_localisation["latitude"],
                validator_localisation["longitude"],
                location["latitude"],
                location["longitude"],
            )
        else:
            if validator_localisation is None:
                btul.logging.warning(
                    f"[{miner.uid}][Score][Latency] The validator's country '{validator_country}' could not be found. No tolerance applied."
                )

            if location is None:
                btul.logging.warning(
                    f"[{miner.uid}][Score][Latency] The country '{item.country}' could not be found. No tolerance applied."
                )

        scaled_distance = distance / MAX_DISTANCE
        tolerance = 1 - scaled_distance

        process_time = item.process_time * tolerance
        process_times.append(process_time)

        if miner_index == -1 and item.uid == miner.uid:
            miner_index = len(process_times) - 1
    btul.logging.trace(
        f"[{miner.uid}][Score][Latency] Process times with tolerance {process_times}"
    )

    # Step 3: Baseline Latency Calculation
    baseline_latency = sum(process_times) / len(process_times) 
    btul.logging.trace(f"[{miner.uid}][Score][Latency] Base latency {baseline_latency}")

    # Step 4: Relative Latency Score Calculation
    relative_latency_scores = []
    for process_time in process_times:
        relative_latency_score = 1 - (process_time / baseline_latency)
        relative_latency_scores.append(relative_latency_score)
    btul.logging.trace(
        f"[{miner.uid}][Score][Latency] Relative scores {relative_latency_scores}"
    )

    # Step 5: Normalization
    min_score = min(relative_latency_scores)
    btul.logging.trace(
        f"[{miner.uid}][Score][Latency] Minimum relative score {min_score}"
    )
    max_score = max(relative_latency_scores)
    btul.logging.trace(
        f"[{miner.uid}][Score][Latency] Maximum relative score {max_score}"
    )
    score = relative_latency_scores[miner_index]
    btul.logging.trace(f"[{miner.uid}][Score][Latency] Relative score {score}")

    if min_score == max_score == score:
        # Only one uid with process time
        return 1

    score = (score - min_score) / (max_score - min_score)

    return score


def can_compute_distribution_score(miner: Miner):
    """
    True if we can compute the distribution score, false to get the penalty
    """
    return miner.verified and not miner.has_ip_conflicts


def compute_distribution_score(miner: Miner, miners: List[Miner]):
    """
    Compute the distribution score of the uid based on the country of all uids
    """
    if not can_compute_distribution_score(miner):
        return DISTRIBUTION_FAILURE_REWARD

    # Step 1: Country of the requested response
    country = miner.country

    # Step 2; Exclude miners not verified or with ip conflicts
    conform_miners = [
        miner for miner in miners if miner.verified and not miner.has_ip_conflicts
    ]

    # Step 3: Country the number of miners in the country
    count = 0
    for item in conform_miners:
        if item.country == country:
            count = count + 1
    btul.logging.trace(f"[{miner.uid}][Score][Distribution] {count} uids in {country}")

    # Step 4: Compute the score
    score = 1 / count if count > 0 else 0

    return score


def compute_final_score(miner: Miner):
    """
    Compute the final score based on the different scores (availability, reliability, latency and distribution)
    """
    # Use a smaller weight if the subtensor is available but desync (miner block < validator block - 1)
    availability_weight = (
        3 if miner.verified and not miner.sync else AVAILABILITY_WEIGHT
    )

    numerator = (
        (availability_weight * miner.availability_score)
        + (LATENCY_WEIGHT * miner.latency_score)
        + (RELIABILLITY_WEIGHT * miner.reliability_score)
        + (DISTRIBUTION_WEIGHT * miner.distribution_score)
    )

    denominator = (
        availability_weight + LATENCY_WEIGHT + RELIABILLITY_WEIGHT + DISTRIBUTION_WEIGHT
    )

    score = numerator / denominator if denominator != 0 else 0

    if miner.suspicious:
        penalty_factor = miner.penalty_factor or 0
        btul.logging.debug(
            f"[{CHALLENGE_NAME}][{miner.uid}] Applying penalty factor of {penalty_factor}"
        )
        score = penalty_factor * score

    return score
