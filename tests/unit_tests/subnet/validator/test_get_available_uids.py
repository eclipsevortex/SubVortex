from subnet.validator.utils import get_available_uids

from tests.unit_tests.utils.utils import generate_random_ip


def test_given_a_list_of_uids_without_exclusion_when_all_uids_are_available_should_return_all_the_uids(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    # Act
    result = get_available_uids(validator, [])

    # Assert
    assert len(axons) == len(result)


def test_given_a_list_of_uids_with_exclusion_when_all_uids_are_available_should_return_all_the_uids_without_excluded_ones(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    exclusions = [1]

    # Act
    result = get_available_uids(validator, exclusions)

    # Assert
    assert len(axons) - 1 == len(result)
    assert all(uid not in result for uid in exclusions)


def test_given_a_list_of_uids_without_exclusion_when_a_uid_is_unavailable_should_not_be_returned(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    # Make uid 1 unavaiable
    unaivalable_uid = 1
    validator.metagraph.axons[unaivalable_uid].ip = "0.0.0.0"

    # Act
    result = get_available_uids(validator, [])

    # Assert
    assert len(axons) - 1 == len(result)
    assert unaivalable_uid not in result


def test_given_a_list_of_uids_with_exclusion_when_a_uid_is_unavailable_should_return_all_the_uids_without_the_excluded_and_unavailable_ones(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    # Make uid 1 unavaiable
    unaivalable_uid = 1
    validator.metagraph.axons[unaivalable_uid].ip = "0.0.0.0"

    exclusions = [2]

    # Act
    result = get_available_uids(validator, exclusions)

    # Assert
    assert len(axons) - 2 == len(result)
    assert all(uid not in result for uid in exclusions + [unaivalable_uid])
