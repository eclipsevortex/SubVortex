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
