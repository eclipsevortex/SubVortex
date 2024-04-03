from subnet.validator.miner import Miner

miner_not_verified_1 = Miner(
    uid=1,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=False,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_not_verified_2 = Miner(
    uid=2,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=False,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_not_verified_3 = Miner(
    uid=3,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=False,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_with_best_latency = Miner(
    uid=4,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=1.0,
)

miner_with_in_between_latency = Miner(
    uid=5,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=3.0,
)

miner_with_worst_latency = Miner(
    uid=6,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_with_30_percent_to_the_best_in_between_latency = Miner(
    uid=7,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=miner_with_best_latency.process_time
    + (
        (miner_with_worst_latency.process_time - miner_with_best_latency.process_time)
        * 0.3
    ),
)

miner_with_30_percent_to_the_worst_in_between_latency = Miner(
    uid=8,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=miner_with_worst_latency.process_time
    - (
        (miner_with_worst_latency.process_time - miner_with_best_latency.process_time)
        * 0.3
    ),
)

miner_verified = Miner(
    uid=9,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_unique_localisation = Miner(
    uid=10,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="US",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_gb_1 = Miner(
    uid=11,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="GB",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_gb_2 = Miner(
    uid=12,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="GB",
    verified=True,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_with_ip_conflicts_1 = Miner(
    uid=13,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    ip_occurences=2,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_with_ip_conflicts_2 = Miner(
    uid=14,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=True,
    ip_occurences=3,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_not_verified_and_ip_conflicts_1 = Miner(
    uid=15,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=False,
    ip_occurences=2,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)

miner_not_verified_and_ip_conflicts_2 = Miner(
    uid=16,
    hotkey="5GhDs7dTbrGauKnMnUrgWSVmwvX2VdqSnVoqVbEEXrd1Vd81",
    ip="192.168.10.1",
    version="0.0.0",
    country="DE",
    verified=False,
    ip_occurences=2,
    score=0.6851191898108059,
    availability_score=0.0,
    latency_score=0.0,
    reliability_score=0.9996040277537239,
    distribution_score=0.0,
    challenge_attempts=574,
    challenge_successes=574,
    process_time=5.0,
)
