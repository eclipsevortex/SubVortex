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
import pytest

from subnet.validator.utils import get_available_uids

from tests.unit_tests.utils.utils import generate_random_ip


@pytest.mark.usefixtures("validator")
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


@pytest.mark.usefixtures("validator")
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


@pytest.mark.usefixtures("validator")
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


@pytest.mark.usefixtures("validator")
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
