# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

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
import numpy as np
from typing import Dict

import bittensor.utils.btlogging as btul

import subvortex.validator.core.model.miner as cmm
import subvortex.validator.core.challenger.model as ccm
import subvortex.validator.core.challenger.utils as ccu
import subvortex.validator.core.challenger.settings as sccs
import subvortex.validator.core.challenger.constants as sccc

# Longest distance between any two places on Earth is 20,010 kilometers
MAX_DISTANCE = 20010

# Decay rate parameter controlling the distribution score decrease.
BASE_SCORE = 1
DECAY_RATE = 0.5


def refresh_availability_metadata(
    settings: sccs.Settings, result: ccm.ChallengeResult, miner: cmm.Miner
):
    attempts = ccu.apply_sma(settings, miner.availability_attempts, 1, 0)
    btul.logging.trace(
        f"[{miner.uid}][Score][Availability] # of attempts {miner.availability_attempts}",
        prefix=settings.logging_name,
    )

    successes = ccu.apply_sma(
        settings,
        miner.availability_successes,
        int(result.is_available),
        0,
    )
    btul.logging.trace(
        f"[{miner.uid}][Score][Availability] # of successes {miner.availability_successes}",
        prefix=settings.logging_name,
    )

    return attempts, successes


def compute_availability_score(challengee: cmm.Miner):
    """
    Compute the availability score of the uid
    """
    # Compute the attempts/success
    attempts = sum(challengee.availability_attempts)
    successes = sum(challengee.availability_successes)

    # Normalization
    score = successes / attempts if attempts > 0 else 0

    return score


def refresh_reliability_metadata(
    settings: sccs.Settings, result: ccm.ChallengeResult, challengee: cmm.Miner
):
    attempts = ccu.apply_sma(settings, challengee.reliability_attempts, 1, 0)
    btul.logging.trace(
        f"[{challengee.uid}][Score][Reliability] # of attemmpts {challengee.reliability_attempts}",
        prefix=settings.logging_name,
    )

    successes = ccu.apply_sma(
        settings,
        challengee.reliability_successes,
        int(result.is_reliable),
        0,
    )
    btul.logging.trace(
        f"[{challengee.uid}][Score][Reliability] # of successes {challengee.reliability_successes}",
        prefix=settings.logging_name,
    )

    return attempts, successes


def compute_reliability_score(challengee: cmm.Miner):
    """
    Compute the reliability score of the uid
    """
    # Compute the attempts/success
    attempts = sum(challengee.reliability_attempts)
    successes = sum(challengee.reliability_successes)

    # Normalization
    score = successes / attempts if attempts > 0 else 0

    return score


def refresh_latency_metadata(
    settings: sccs.Settings, result: ccm.ChallengeResult, challengee: cmm.Miner
):
    latency_times = ccu.apply_sma(
        settings,
        challengee.latency_times,
        result.avg_process_time,
        settings.challenge_timeout,
    )
    btul.logging.trace(
        f"[{challengee.uid}][Score][Latency] Process times {latency_times}",
        prefix=settings.logging_name,
    )
    return latency_times


# TODO: Put the score at 0 if the minimum attempts is not all successful! or find way to not get 1 when you are alone!
def compute_latency_score(
    settings: sccs.Settings,
    challengees: Dict[str, cmm.Miner],
    challengee: cmm.Miner,
):
    """
    Compute the latency score of the uid
    """
    # Get the challenger score
    score = challengees.get(challengee.hotkey)

    # Compute the average latency for each challenger
    latencies = [
        (x.hotkey, np.mean(x.latency_times).item()) for x in challengees.values()
    ]

    # Sort the challenger SMA in descending way
    latencies_sorted = sorted(latencies, key=lambda x: x[1])

    # Find the rank of the challenger
    challenger_rank = next(
        (i for i, x in enumerate(latencies_sorted) if x[0] == challengee.hotkey), -1
    )
    if challenger_rank == -1:
        return sccc.LATENCY_FAILURE_REWARD

    btul.logging.info(f"Rank: {challenger_rank}", prefix=settings.logging_name)

    # Calculate the adjustment factor
    adjustment_factor = (sccc.TOP_X_MINERS - len(challengees)) / sccc.TOP_X_MINERS

    # Set the sign modifier based on the index
    sign_modifier = -1 if challenger_rank == 0 else 1

    # Override scores if there are less miners than top x miners
    score = (
        compute_score(challenger_rank)
        if len(challengees) >= sccc.TOP_X_MINERS
        else compute_score(challenger_rank)
        + (
            sign_modifier
            * adjustment_factor
            * (compute_score(challenger_rank) - compute_score(challenger_rank + 1))
        )
    )

    return score


def refresh_performance_metadata(
    settings: sccs.Settings, result: ccm.ChallengeResult, challengee: cmm.Miner
):
    attempts = ccu.apply_sma(
        settings, challengee.performance_attempts, result.challenge_attempts, 0
    )
    btul.logging.trace(
        f"[{challengee.uid}][Score][Performance] # of attempts {challengee.performance_attempts}",
        prefix=settings.logging_name,
    )

    successes = ccu.apply_sma(
        settings,
        challengee.performance_successes,
        result.challenge_successes,
        0,
    )
    btul.logging.trace(
        f"[{challengee.uid}][Score][Performance] # of successes {challengee.performance_successes}",
        prefix=settings.logging_name,
    )

    # Compute an boost for challengee request more attempts than teh minimum
    total_attempts = sum(attempts)
    total_successes = sum(successes)
    success_ratio = (total_successes / total_attempts) if total_attempts > 0 else 0

    # Apply a non-linear boost for challengers attempting more than PERFORMANCE_MIN_ATTEMPTS
    attempt_boost = (
        total_attempts / settings.default_challenge_max_iteration
    ) ** settings.performance_reward_exponent

    # Penalize challengers who take more attempts but fail more
    penalty = 1 - (1 - success_ratio) * settings.performance_penalty_factor
    boost = success_ratio * attempt_boost * penalty

    boosts = ccu.apply_sma(settings, challengee.performance_boost, boost, 0)

    return attempts, successes, boosts


# TODO: Put the score at 0 if the minimum attempts is not all successful! or find way to not get 1 when you are alone!
def compute_performance_score(
    challengees: Dict[str, cmm.Miner],
    challengee: cmm.Miner,
):
    """
    Compute the performance score of the uid
    """
    # Get the challenger score
    score = challengees.get(challengee.hotkey)

    # Build the array of hotkey/boots
    boosts = [
        (x.hotkey, np.mean(x.performance_boost).item()) for x in challengees.values()
    ]

    # Sort challengers by performance score in descending order
    performance_scores_sorted = sorted(boosts, key=lambda x: x[1], reverse=True)

    # Find the rank of the challenger
    challenger_rank = next(
        (
            i
            for i, x in enumerate(performance_scores_sorted)
            if x[0] == challengee.hotkey
        ),
        -1,
    )
    if challenger_rank == -1:
        return sccc.PERFORMANCE_FAILURE_REWARD

    # Calculate the adjustment factor
    adjustment_factor = (sccc.TOP_X_MINERS - len(challengees)) / sccc.TOP_X_MINERS

    # Set the sign modifier based on the index
    sign_modifier = -1 if challenger_rank == 0 else 1

    # Override scores if there are less miners than top x miners
    score = (
        compute_score(challenger_rank)
        if len(challengees) >= sccc.TOP_X_MINERS
        else compute_score(challenger_rank)
        + (
            sign_modifier
            * adjustment_factor
            * (compute_score(challenger_rank) - compute_score(challenger_rank + 1))
        )
    )

    return score


def compute_distribution_score(
    settings: sccs.Settings,
    challengees: Dict[str, cmm.Miner],
    challengee: cmm.Miner,
):
    """
    Compute the distribution score of the challenger
    Only the top x miner will receive a score, the rest will receive 0
    """
    # Sort the challengers per score - override distribution score to make it obsolete
    sorted_challengers = sorted(
        challengees.values(),
        key=lambda x: compute_final_score(settings, x, {"distribution": 1}),
        reverse=True,
    )

    # Take the top X miners
    top_challenger = sorted_challengers[: sccc.TOP_X_MINERS]

    # Find the inder of the miner
    challenger_rank = next(
        (i for i, x in enumerate(top_challenger) if x.hotkey == challengee.hotkey), -1
    )
    if challenger_rank == -1:
        return sccc.DISTRIBUTION_FAILURE_REWARD

    # Compute the score using a exponential decay formula
    # which is used in scoring systems to assign diminishing values to items based on their rank
    score = compute_score(challenger_rank)

    return score


def compute_final_score(settings: sccs.Settings, miner: cmm.Miner, overrides={}):
    """
    Compute the final score based on the different scores (availability, reliability, latency and distribution)
    """
    availability_score = overrides.get("availability", miner.availability_score)
    latency_score = overrides.get("latency", miner.latency_score)
    reliability_score = overrides.get("reliability", miner.reliability_score)
    performance_score = overrides.get("performance", miner.performance_score)
    distribution_score = overrides.get("distribution", miner.distribution_score)

    numerator = (
        (settings.availability_weight * availability_score)
        + (settings.latency_weight * latency_score)
        + (settings.reliability_weight * reliability_score)
        + (settings.distribution_weight * distribution_score)
        + (settings.performance_weight * performance_score)
    )

    denominator = (
        settings.availability_weight
        + settings.latency_weight
        + settings.reliability_weight
        + settings.distribution_weight
        + settings.performance_weight
    )

    score = numerator / denominator if denominator != 0 else 0

    return score


def compute_score(index):
    return BASE_SCORE * np.exp(-DECAY_RATE * index).item()
