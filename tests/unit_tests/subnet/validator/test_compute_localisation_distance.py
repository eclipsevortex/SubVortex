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
from subnet.validator.localisation import compute_localisation_distance


def test_distance_between_france_and_america_should_return_close_to_7665_km():
    # Arrange
    longitude_america = -95.712891
    latitude_america = 37.09024
    longitude_france = 2.213749
    latitude_france = 46.227638

    # Act
    result = compute_localisation_distance(
        latitude_america, longitude_america, latitude_france, longitude_france
    )

    # Assert
    assert 7665 < result
    assert 7666 > result


def test_distance_between_france_and_japan_should_return_close_to_9850_km():
    # Arrange
    longitude_japan = 138.252924
    latitude_japan = 36.204824
    longitude_france = 2.213749
    latitude_france = 46.227638

    # Act
    result = compute_localisation_distance(
        latitude_japan, longitude_japan, latitude_france, longitude_france
    )

    # Assert
    assert 9850 < result
    assert 9851 > result
