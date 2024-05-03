def mock_get_country(mock_get_country, axon_details):
    def side_effect(*args):
        country = next((x["country"] for x in axon_details if x["ip"] == args[0]), None)
        return country or "GB"

    mock_get_country.side_effect = side_effect
