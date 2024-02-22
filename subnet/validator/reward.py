import torch
import numpy as np
import bittensor as bt
from typing import Union, List


def get_sorted_response_times(uids, process_times: List[int], timeout: float):
    """
    Sorts a list of axons based on their response times.

    This function pairs each uid with its corresponding axon's response time,
    and then sorts this list in ascending order. Lower response times are considered better.

    Args:
        uids (List[int]): List of unique identifiers for each axon.
        responses (List[Response]): List of Response objects corresponding to each axon.

    Returns:
        List[Tuple[int, float]]: A sorted list of tuples, where each tuple contains an axon's uid and its response time.

    Example:
        >>> get_sorted_response_times([1, 2, 3], [response1, response2, response3])
        [(2, 0.1), (1, 0.2), (3, 0.3)]
    """
    axon_times = [
        (
            uids[idx],
            process_time
            if process_time is not None
            else timeout,
        )
        for idx, process_time in enumerate(process_times)
    ]
    # Sorting in ascending order since lower process time is better
    sorted_axon_times = sorted(axon_times, key=lambda x: x[1])
    bt.logging.debug(f"sorted_axon_times: {sorted_axon_times}")
    return sorted_axon_times


def adjusted_sigmoid_inverse(x, steepness=1, shift=0):
    """
    Inverse of the adjusted sigmoid function.

    This function is a modified version of the sigmoid function that is shifted to
    the right by a certain amount but inverted such that low completion times are
    rewarded and high completions dimes are punished.
    """
    return 1 / (1 + np.exp(steepness * (x - shift)))


def calculate_sigmoid_params(timeout):
    """
    Calculate sigmoid parameters based on the timeout value.

    Args:
    - timeout (float): The current timeout value.

    Returns:
    - tuple: A tuple containing the 'steepness' and 'shift' values for the current timeout.
    """
    base_timeout = 1
    base_steepness = 5
    base_shift = 0.6

    # Calculate the ratio of the current timeout to the base timeout
    ratio = timeout / base_timeout

    # Calculate steepness and shift based on the pattern
    steepness = base_steepness / ratio
    shift = base_shift * ratio

    return steepness, shift


def sigmoid_normalize(process_times, timeout):
    # Center the completion times around 0 for effective sigmoid scaling
    centered_times = process_times - np.mean(process_times)

    # Calculate steepness and shift based on timeout
    steepness, shift = calculate_sigmoid_params(timeout)

    # Apply adjusted sigmoid function to scale the times
    return adjusted_sigmoid_inverse(centered_times, steepness, shift)


def scale_rewards(
    uids, process_times, rewards, timeout: float, device
):
    """
    Scales the rewards for each axon based on their response times using sigmoid normalization.
    Args:
        uids (List[int]): A list of unique identifiers for each axon.
        process_times (List[int]): A list of challenge process time corresponding to each axon.
        rewards (List[float]): A list of initial reward values for each axon.
        timeout (float): The timeout value used for response time calculations.
        data_sizes (List[int]): A list of data sizes corresponding to each axon.

    Returns:
        List[float]: A list of scaled rewards for each axon.
    """
    sorted_axon_times = get_sorted_response_times(uids, process_times, timeout=timeout)

    # Extract only the process times
    process_times = [proc_time for _, proc_time in sorted_axon_times]

    # Normalize the response times
    normalized_times = sigmoid_normalize(process_times, timeout)

    # Create a dictionary mapping UIDs to normalized times
    uid_to_normalized_time = {
        uid: normalized_time
        for (uid, _), normalized_time in zip(sorted_axon_times, normalized_times)
    }

    # Scale the rewards with normalized times
    time_scaled_rewards = torch.tensor(
        [
            rewards.to(device) * uid_to_normalized_time[uid]
            for i, uid in enumerate(uids)
        ]
    )

    # Final normalization if needed
    rescale_factor = torch.sum(rewards) / torch.sum(time_scaled_rewards)
    bt.logging.trace(f"Rescale factor: {rescale_factor}")
    scaled_rewards = [reward * rescale_factor for reward in time_scaled_rewards]

    return scaled_rewards


def apply_reward_scores(
    self,
    uids,
    process_times,
    rewards,
    timeout: float,
):
    """
    Adjusts the moving average scores for a set of UIDs based on their response times and reward values.

    This should reflect the distribution of axon response times

    Parameters:
        uids (List[int]): A list of UIDs for which rewards are being applied.
        process_times (List[float]): A list of challenge process time from the nodes.
        rewards (torch.FloatTensor): A tensor containing the computed reward values.
        data_sizes (List[float]): The size of each data piece used for the forward pass.
        timeout (float): The timeout value used for response time calculations.
    """
    if self.config.neuron.verbose:
        bt.logging.debug(f"Applying rewards: {rewards}")
        bt.logging.debug(f"Reward shape: {rewards.shape}")
        bt.logging.debug(f"UIDs: {uids}")

    # Scale rewards based on response times
    scaled_rewards = scale_rewards(
        uids,
        process_times,
        rewards,
        timeout=timeout,
        device=self.device,
    )
    scaled_rewards = torch.tensor(scaled_rewards).type(
        torch.FloatTensor
    )  # Ensure same type as rewards
    bt.logging.debug(f"Normalized rewards: {scaled_rewards}")

    # Compute forward pass rewards
    # shape: [ metagraph.n ]
    scattered_rewards: torch.FloatTensor = (
        self.moving_averaged_scores.to(self.device)
        .scatter(
            0,
            torch.tensor(uids).to(self.device),
            scaled_rewards.to(self.device),
        )
        .to(self.device)
    )
    bt.logging.trace(f"Scattered rewards: {scattered_rewards}")

    # Update moving_averaged_scores with rewards produced by this step.
    # shape: [ metagraph.n ]
    alpha: float = 0.05
    self.moving_averaged_scores: torch.FloatTensor = alpha * scattered_rewards + (
        1 - alpha
    ) * self.moving_averaged_scores.to(self.device)
    bt.logging.trace(f"Updated moving avg scores: {self.moving_averaged_scores}")