import numpy as np
import bittensor as bt

from subnet.validator.bonding import wilson_score_interval
from subnet.validator.localisation import (
    compute_localisation_distance,
    get_localisation,
)

# Controls how quickly the tolerance decreases with distance.
SIGMA = 20
# Longest distance between any two places on Earth is 20,010 kilometers
MAX_DISTANCE = 20010


async def compute_reliability_score(database, hotkey: str):
    stats_key = f"stats:{hotkey}"

    # Step 1: Retrieve statistics
    challenge_successes = int(
        await database.hget(stats_key, "challenge_successes") or 0
    )
    challenge_attempts = int(await database.hget(stats_key, "challenge_attempts") or 0)

    # Step 2: Normalization
    normalized_score = wilson_score_interval(challenge_successes, challenge_attempts)

    return normalized_score


def compute_latency_score(idx, validator_country, responses):
    # Step 1: Baseline Latency Calculation
    process_times = list(
        set(
            process_time if process_time else 5
            for verified, country, process_time in responses
        )
    )
    baseline_latency = np.mean(process_times)

    # Step: Get the localisation
    validator_localisation = get_localisation(validator_country)

    # Step 2: Relative Latency Score Calculation
    relative_latency_scores = []
    for response in responses:
        country = response[1]
        process_time = response[2]

        distance = 0
        location = get_localisation(country)
        if location is not None:
            distance = compute_localisation_distance(
                validator_localisation["latitude"],
                validator_localisation["longitude"],
                location["latitude"],
                location["longitude"],
            )

        scaled_distance = distance / MAX_DISTANCE
        tolerance = 1 - scaled_distance
        bt.logging.trace(
            f"[Score][Latency]Tolerance {tolerance} for a distance of {distance} ({validator_localisation['country']}-{location['country'] if location else 'None'})"
        )

        response_process_time = process_time * tolerance if process_time else 5
        relative_latency_score = 1 - (response_process_time / baseline_latency)
        relative_latency_scores.append(relative_latency_score)

    # Step 3: Normalization
    max_score = max(relative_latency_scores)
    min_score = min(relative_latency_scores)
    normalized_scores = (relative_latency_scores[idx] - min_score) / (
        max_score - min_score
    )

    return normalized_scores


def compute_distribution_score(idx, responses):
    # Step 1: Country of the requested response
    country = responses[idx][1]

    # Step 1: Country the number of miners in the country
    count = 0
    for response in responses:
        if response[1] == country:
            count = count + 1

    # Step 2: Compute the score
    score = 1 / count

    return score
