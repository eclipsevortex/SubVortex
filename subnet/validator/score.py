import numpy as np
import bittensor as bt

from subnet.validator.bonding import wilson_score_interval
from subnet.validator.localisation import (
    compute_localisation_distance,
    get_localisation,
)
from subnet.constants import (
    AVAILABILITY_FAILURE_REWARD,
    LATENCY_FAILURE_REWARD,
    DISTRIBUTION_FAILURE_REWARD,
    RELIABILLITY_FAILURE_REWARD,
)

# Controls how quickly the tolerance decreases with distance.
SIGMA = 20
# Longest distance between any two places on Earth is 20,010 kilometers
MAX_DISTANCE = 20010


def compute_availability_score(verified):
    """
    Compute the availability score of the uid
    """

    score = 1.0 if verified else AVAILABILITY_FAILURE_REWARD
    return score


async def compute_reliability_score(verified, uid, miner):
    """
    Compute the reliaiblity score of the uid based on the the ratio challenge_successes/challenge_attempts
    """
    if verified == False:
        return RELIABILLITY_FAILURE_REWARD

    # Step 1: Retrieve statistics
    challenge_successes = miner.get("challenge_successes") or 0
    challenge_attempts = miner.get("challenge_attempts") or 0
    bt.logging.trace(
        f"[{uid}][Score][Reliability] # challenge attempts {challenge_attempts}"
    )
    bt.logging.trace(
        f"[{uid}][Score][Reliability] # challenge succeeded {challenge_successes}"
    )

    # Step 2: Normalization
    normalized_score = wilson_score_interval(challenge_successes, challenge_attempts)

    return normalized_score


def compute_latency_score(verified, uid, validator_country, responses, miners):
    if verified == False:
        return LATENCY_FAILURE_REWARD

    # Step 1: Get the localisation of the validator
    validator_localisation = get_localisation(validator_country)

    # Step 2: Compute the active miners process times by adding a tolerance
    raw_process_times = []
    process_times = []
    for miner in miners:
        country = miner.get("country")
        process_time = miner.get("process_time")

        if miner.get("verified") == False:
            # Exclude miners not verifed to not alterate the computation
            continue

        matches = [response for response in responses if response[0] == miner.get('uid')]
        new_process_time = matches[0][3] if len(matches) > 0 else process_time or 0

        # Just for log purposes
        raw_process_times.append((miner.get("uid"), new_process_time))

        distance = 0
        location = get_localisation(country)
        if location is not None:
            distance = compute_localisation_distance(
                validator_localisation["latitude"],
                validator_localisation["longitude"],
                location["latitude"],
                location["longitude"],
            )

        scaled_distance = distance / MAX_DISTANCE if distance > 0 else 0
        tolerance = 1 - scaled_distance

        new_process_time = process_time * tolerance if process_time else 5
        process_times.append((miner.get("uid"), new_process_time))
    bt.logging.trace(f"[{uid}][Score][Latency] Process times {raw_process_times}")
    bt.logging.trace(
        f"[{uid}][Score][Latency] Process times with tolerance {process_times}"
    )

    if len(process_times) == 1:
        # There is only one miner active - score is 1
        bt.logging.warning(f"[{uid}][Score][Latency] Only one miner verified ")
        return 1

    # Step 3: Baseline Latency Calculation
    baseline_latency = np.mean([process_time for (_, process_time) in process_times])
    bt.logging.trace(f"[{uid}][Score][Latency] Base latency {baseline_latency}")

    # Step 4: Relative Latency Score Calculation
    relative_latency_scores = []
    for _, process_time in process_times:
        relative_latency_score = 1 - (process_time / baseline_latency)
        relative_latency_scores.append(relative_latency_score)
    bt.logging.trace(
        f"[{uid}][Score][Latency] Relative scores {relative_latency_scores}"
    )

    # Step 5: Normalization
    min_score = min(relative_latency_scores)
    bt.logging.trace(f"[{uid}][Score][Latency] Minimum relative score {min_score}")
    max_score = max(relative_latency_scores)
    bt.logging.trace(f"[{uid}][Score][Latency] Maximum relative score {max_score}")
    index = [idx for idx, (_uid, _) in enumerate(process_times) if _uid == uid][0]
    score = relative_latency_scores[index]
    bt.logging.trace(f"[{uid}][Score][Latency] Relative score {score}")

    normalized_score = (
        (score - min_score) / (max_score - min_score)
        if max_score - min_score > 0
        else 0
    )

    return normalized_score


def compute_distribution_score(verified, uid, countries):
    """
    Compute the distribution score of the uid based on the country of all uids
    """
    if verified == False:
        return DISTRIBUTION_FAILURE_REWARD

    # Step 1: Country of the uid
    country = countries[f"{uid}"]
    bt.logging.trace(f"[{uid}][Score][Distribution] Uid country {country}")

    # Step 2: Get all uids in that country
    others = []
    for key, value in countries.items():
        if value == country:
            others.append(key)
    bt.logging.trace(f"[{uid}][Score][Distribution] Other Uids country {others}")

    # Step 3: Compute the score
    score = 1 / len(others) if country != None else 0

    return score
