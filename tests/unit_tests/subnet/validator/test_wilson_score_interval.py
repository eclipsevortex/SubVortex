from subnet.validator.bonding import wilson_score_interval

# The success/attempts for reliability score will be reset every 3 epochs

def test_new_miner_is_starting_by_failing_few_times_before_succeeding_the_remaining_of_3_epochs():
    # Miner started to mine on the subnet
    successes = 0
    attempts = 0

    result = wilson_score_interval(successes, attempts)
    assert 0.5 == result

    # Miner is failing 5 attempts
    successes = 0
    attempts = 5

    result = wilson_score_interval(successes, attempts)
    assert 0.04169951653253214 == result

    # Miner is succeeding 5 attempts
    successes = 5
    attempts = 10

    result = wilson_score_interval(successes, attempts)
    assert 0.5 == result

    # Miner succeeding all the remaining attempts
    successes = 1075
    attempts = 1080

    result = wilson_score_interval(successes, attempts)
    assert 0.9951617896912337 == result


def test_new_miner_is_starting_by_succeeding_few_times_then_failing_few_times_before_succeeding_the_remaining_of_3_epochs():
    # Miner started to mine on the subnet
    successes = 0
    attempts = 0

    result = wilson_score_interval(successes, attempts)
    assert 0.5 == result

    # Miner is succeeded 5 attempts
    successes = 360
    attempts = 360

    result = wilson_score_interval(successes, attempts)
    assert 0.9993689413333688 == result

    # Miner is failing 5 attempts
    successes = 360
    attempts = 365

    result = wilson_score_interval(successes, attempts)
    assert 0.9856959978083112 == result

    # Miner succeeding all the remaining attempts
    successes = 1075
    attempts = 1080

    result = wilson_score_interval(successes, attempts)
    assert 0.9951617896912337 == result


def test_new_miner_is_succeeding_the_3_epochs_except_the_few_last_ones():
    # Miner started to mine on the subnet
    successes = 0
    attempts = 0

    result = wilson_score_interval(successes, attempts)
    assert 0.5 == result

    # Miner is succeeded 5 attempts
    successes = 360
    attempts = 360

    result = wilson_score_interval(successes, attempts)
    assert 0.9993689413333688 == result

    # Miner succeeding all the remaining attempts
    successes = 1075
    attempts = 1080

    result = wilson_score_interval(successes, attempts)
    assert 0.9951617896912337 == result
