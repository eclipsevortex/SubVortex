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

from subnet.validator.utils import get_available_query_miners

from tests.unit_tests.utils.utils import generate_random_ip


@pytest.mark.usefixtures("validator")
def test_querying_3_miners_without_exclusion_should_return_a_list_of_3_miners(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    # Act
    result = get_available_query_miners(validator, 3, [])

    # Assert
    assert 3 == len(result)


@pytest.mark.usefixtures("validator")
def test_querying_3_miners_without_exclusion_twice_should_return_the_same_list_of_3_miners(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    # Act
    first_result = get_available_query_miners(validator, 3, [])
    second_result = get_available_query_miners(validator, 3, [])

    # Assert
    assert 3 == len(first_result)
    assert 3 == len(second_result)
    assert first_result == second_result


@pytest.mark.usefixtures("validator")
def test_querying_3_miners_with_exclusion_should_return_a_list_of_3_miners(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    selection = get_available_query_miners(validator, 3, [])

    # Act
    result = get_available_query_miners(validator, 3, [selection[1]])

    # Assert
    assert 3 == len(result)
    assert selection[0] == result[0]
    assert selection[1] not in result
    assert selection[2] == result[2]


@pytest.mark.usefixtures("validator")
def test_querying_3_miners_with_exclusion_twice_should_return_the_same_list_of_3_miners(
    validator,
):
    # Arrange
    axons = validator.metagraph.axons
    for axon in axons:
        axon.ip = generate_random_ip()

    selection = get_available_query_miners(validator, 3, [])

    # Act
    first_result = get_available_query_miners(validator, 3, [selection[1]])
    second_result = get_available_query_miners(validator, 3, [selection[1]])

    # Assert
    assert 3 == len(first_result)
    assert 3 == len(second_result)
    assert first_result == second_result
    assert selection[1] not in first_result
