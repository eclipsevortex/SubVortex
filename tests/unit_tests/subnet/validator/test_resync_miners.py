import copy
import pytest
import unittest
from unittest.mock import MagicMock, patch

from tests.unit_tests.mocks import mock_redis, mock_country
from tests.unit_tests.utils.metagraph import (
    sync_metagraph,
    add_new_miner,
    move_miner,
    replace_old_miner,
    remove_miner,
)

from subnet.validator.miner import resync_miners, get_all_miners

default_axons_details = [
    {"ip": "23.244.235.121", "country": "US"},
    {"ip": "55.228.3.149", "country": "US"},
    {"ip": "43.82.230.186", "country": "SG"},
    {"ip": "191.230.100.214", "country": "BR"},
    {"ip": "85.62.110.203", "country": "ES"},
    {"ip": "187.64.109.14", "country": "BR"},
    {"ip": "38.75.105.111", "country": "KR"},
    {"ip": "176.65.235.230", "country": "IR"},
    {"ip": "34.20.248.3", "country": "US"},
    {"ip": "35.131.97.24", "country": "US"},
    {"ip": "38.213.246.7", "country": "US"},
    {"ip": "89.116.159.53", "country": "US"},
    {"ip": "9.91.241.47", "country": "US"},
    {"ip": "70.229.181.61", "country": "US"},
    {"ip": "88.30.74.99", "country": "ES"},
    {"ip": "88.30.24.99", "country": "ES"},
    {"ip": "9.91.241.48", "country": "ES"},
]

locations = {
    "US": {"country": "United States", "latitude": 37.09024, "longitude": -95.712891},
    "SG": {"country": "Singapore", "latitude": 1.352083, "longitude": 103.819836},
    "BR": {"country": "Brazil", "latitude": -14.235004, "longitude": -51.92528},
    "ES": {"country": "Spain", "latitude": 40.463667, "longitude": -3.74922},
    "KR": {"country": "South Korea", "latitude": 35.907757, "longitude": 127.766922},
    "IR": {"country": "Iran", "latitude": 32.427908, "longitude": 53.688046},
}


@pytest.mark.usefixtures("validator")
class TestResyncMiners(unittest.IsolatedAsyncioTestCase):
    @pytest.fixture(autouse=True)
    def prepare_fixture(self, validator):
        self.validator = validator

    def setUp(self):
        self.chain_state = copy.deepcopy(self.validator.subtensor.chain_state)

    def tearDown(self):
        self.validator.subtensor.chain_state = self.chain_state
        sync_metagraph(self.validator, default_axons_details)

    async def test_given_a_metagraph_when_no_change_should_return_the_same_list_of_miners(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details)

        axons = self.validator.metagraph.axons
        for idx, axon in enumerate(axons):
            axon.ip = axons_details[idx]["ip"]

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )

        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        # Act
        await resync_miners(self.validator)

        # Assert
        assert miners == self.validator.miners

    async def test_given_a_partially_full_metagraph_when_a_new_neuron_is_added_should_be_added_to_the_list(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details) + [
            {"ip": "19.91.241.48", "country": "US"}
        ]

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )
        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        uid = add_new_miner(self.validator, axons_details)

        # Act
        await resync_miners(self.validator)

        # Assert
        miner = next(
            (element for element in self.validator.miners if element.uid == uid), None
        )

        assert len(miners) + 1 == len(self.validator.miners)
        assert miners == self.validator.miners[:-1]

        miner = self.validator.miners[len(self.validator.miners) - 1]
        assert 17 == miner.uid
        assert "miner-hotkey-17" == miner.hotkey
        assert "19.91.241.48" == miner.ip
        assert 1 == miner.ip_occurences
        assert "0.0.0" == miner.version
        assert "US" == miner.country
        assert 0 == miner.challenge_successes
        assert 0 == miner.challenge_successes
        assert 0 == miner.availability_score
        assert 0 == miner.distribution_score
        assert 0 == miner.reliability_score
        assert 0 == miner.latency_score
        assert 0 == miner.score
        assert 0 == miner.process_time
        assert False == miner.suspicious
        assert False == miner.sync
        assert False == miner.verified

    async def test_given_a_full_metagraph_when_a_uid_has_a_new_hotkey_with_same_ip_should_replace_the_old_miner_by_the_new_one_in_the_list(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details)

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )
        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        self.validator.country_service.get_locations.return_value = locations

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        new_uid = replace_old_miner(
            self.validator,
            axons_details,
        )

        # Act
        await resync_miners(self.validator)

        # Assert
        assert len(miners) == len(self.validator.miners)

        axon_detail = axons_details[new_uid]
        miner = self.validator.miners[new_uid]
        assert "miner-hotkey-17" == miner.hotkey
        assert axon_detail["ip"] == miner.ip
        assert 1 == miner.ip_occurences
        assert "0.0.0" == miner.version
        assert axon_detail["country"] == miner.country
        assert 0 == miner.challenge_successes
        assert 0 == miner.challenge_successes
        assert 0 == miner.availability_score
        assert 0 == miner.distribution_score
        assert 0 == miner.reliability_score
        assert 0 == miner.latency_score
        assert 0 == miner.score
        assert 0 == miner.process_time
        assert False == miner.suspicious
        assert False == miner.sync
        assert False == miner.verified

    async def test_given_a_full_metagraph_when_a_uid_has_a_same_hotkey_with_different_ip_should_replace_the_old_miner_by_the_new_one_in_the_list(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details)

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )
        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        self.validator.country_service.get_locations.return_value = locations

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        uid = move_miner(
            self.validator,
            axons_details,
            10,
            axon_detail={"ip": "31.129.22.101", "country": "PT"},
        )

        # Act
        await resync_miners(self.validator)

        # Assert
        assert len(miners) == len(self.validator.miners)

        miner = self.validator.miners[uid]
        assert f"miner-hotkey-{uid}" == miner.hotkey
        assert "31.129.22.101" == miner.ip
        assert 1 == miner.ip_occurences
        assert "0.0.0" == miner.version
        assert "PT" == miner.country
        assert 0 == miner.challenge_successes
        assert 0 == miner.challenge_successes
        assert 0 == miner.availability_score
        assert 0 == miner.distribution_score
        assert 0 == miner.reliability_score
        assert 0 == miner.latency_score
        assert 0 == miner.score
        assert 0 == miner.process_time
        assert False == miner.suspicious
        assert False == miner.sync
        assert False == miner.verified

    async def test_given_a_full_metagraph_when_a_uid_has_a_new_hotkey_with_different_ip_should_replace_the_old_miner_by_the_new_one_in_the_list(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details)

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )
        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        self.validator.country_service.get_locations.return_value = locations

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        new_uid = replace_old_miner(
            self.validator,
            axons_details,
            axon_detail={"ip": "19.91.241.48", "country": "US"},
        )

        # Act
        await resync_miners(self.validator)

        # Assert
        assert len(miners) == len(self.validator.miners)

        miner = self.validator.miners[new_uid]
        assert "miner-hotkey-17" == miner.hotkey
        assert "19.91.241.48" == miner.ip
        assert 1 == miner.ip_occurences
        assert "0.0.0" == miner.version
        assert "US" == miner.country
        assert 0 == miner.challenge_successes
        assert 0 == miner.challenge_successes
        assert 0 == miner.availability_score
        assert 0 == miner.distribution_score
        assert 0 == miner.reliability_score
        assert 0 == miner.latency_score
        assert 0 == miner.score
        assert 0 == miner.process_time
        assert False == miner.suspicious
        assert False == miner.sync
        assert False == miner.verified

    async def test_given_a_metagraph_when_a_uid_is_not_running_should_be_removed_from_the_list(
        self,
    ):
        # Arrange
        axons_details = copy.deepcopy(default_axons_details)

        self.validator.country_service = MagicMock()
        mock_country.mock_get_country(
            self.validator.country_service.get_country, axons_details
        )
        self.validator.database = mock_redis.mock_get_statistics(
            self.validator.metagraph.hotkeys
        )

        self.validator.country_service.get_locations.return_value = locations

        sync_metagraph(self.validator, axons_details)
        miners = await get_all_miners(self.validator)
        self.validator.miners = copy.deepcopy(miners)

        uid = remove_miner(self.validator, axons_details, 15)

        # Act
        await resync_miners(self.validator)

        # Assert
        assert len(miners) - 1 == len(self.validator.miners)
        assert False == any(element.uid == uid for element in self.validator.miners)
