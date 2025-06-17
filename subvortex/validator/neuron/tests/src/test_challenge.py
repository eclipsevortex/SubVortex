import pytest
from collections import defaultdict
from subvortex.validator.neuron.src.challenge import (
    enforce_country_miner_limit,
    MAX_MINERS_PER_COUNTRY,
)


class MockMiner:
    def __init__(self, uid, country, score, registered_at):
        self.uid = uid
        self.country = country
        self.score = score
        self.registered_at = registered_at


@pytest.mark.parametrize("num_miners", [0, 5, 10])
def test_enforce_country_limit_under_or_equal(num_miners):
    # Arrange
    miners = [
        MockMiner(uid=i, country="US", score=1.0, registered_at=100 + i)
        for i in range(num_miners)
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert
    for miner in miners:
        assert scores[miner.uid] == 1.0
        assert miner.score == 1.0


def test_enforce_country_limit_exceeds():
    # Arrange
    miners = [
        MockMiner(uid=i, country="US", score=1.0 - i * 0.01, registered_at=100 + i)
        for i in range(15)
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert
    top_miners = sorted(miners, key=lambda m: (-scores[m.uid], m.registered_at))[
        :MAX_MINERS_PER_COUNTRY
    ]
    bottom_miners = [m for m in miners if m not in top_miners]

    for miner in top_miners:
        assert scores[miner.uid] > 0.0
        assert miner.score > 0.0

    for miner in bottom_miners:
        assert scores[miner.uid] == 0.0
        assert miner.score == 0.0


def test_multiple_countries_mixed_limits():
    # Arrange
    miners = []
    miners += [
        MockMiner(uid=i, country="US", score=0.9, registered_at=100 + i)
        for i in range(5)
    ]
    miners += [
        MockMiner(
            uid=100 + i, country="DE", score=1.0 - i * 0.02, registered_at=200 + i
        )
        for i in range(12)
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert
    for miner in miners:
        if miner.country == "US":
            assert scores[miner.uid] == 0.9
            assert miner.score == 0.9

    de_miners = [m for m in miners if m.country == "DE"]
    sorted_de = sorted(de_miners, key=lambda m: (-scores[m.uid], m.registered_at))
    top_de = sorted_de[:MAX_MINERS_PER_COUNTRY]
    bottom_de = sorted_de[MAX_MINERS_PER_COUNTRY:]

    for miner in top_de:
        assert scores[miner.uid] > 0.0
        assert miner.score > 0.0

    for miner in bottom_de:
        assert scores[miner.uid] == 0.0
        assert miner.score == 0.0


def test_tie_scores_resolved_by_registered_at():
    # Arrange: All scores equal; registered_at determines the tie
    miners = [
        MockMiner(uid=i, country="FR", score=1.0, registered_at=100 + i)
        for i in range(12)
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert: The 2 most recently registered miners should be cut
    sorted_miners = sorted(miners, key=lambda m: (m.registered_at))
    top_10_uids = {m.uid for m in sorted_miners[:MAX_MINERS_PER_COUNTRY]}

    for miner in miners:
        if miner.uid in top_10_uids:
            assert scores[miner.uid] == 1.0
            assert miner.score == 1.0
        else:
            assert scores[miner.uid] == 0.0
            assert miner.score == 0.0


def test_scores_already_zero():
    # Arrange
    miners = [
        MockMiner(uid=i, country="IN", score=0.0, registered_at=100 + i)
        for i in range(5)
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert
    for miner in miners:
        assert scores[miner.uid] == 0.0
        assert miner.score == 0.0


def test_stable_sort_with_score_and_registered_at_mix():
    # Arrange: Same score but shuffled registration dates
    miners = [
        MockMiner(uid=0, country="BR", score=1.0, registered_at=105),
        MockMiner(uid=1, country="BR", score=1.0, registered_at=101),
        MockMiner(uid=2, country="BR", score=1.0, registered_at=103),
        MockMiner(uid=3, country="BR", score=1.0, registered_at=104),
        MockMiner(uid=4, country="BR", score=1.0, registered_at=102),
        MockMiner(uid=5, country="BR", score=1.0, registered_at=106),
        MockMiner(uid=6, country="BR", score=1.0, registered_at=100),
        MockMiner(uid=7, country="BR", score=1.0, registered_at=107),
        MockMiner(uid=8, country="BR", score=1.0, registered_at=109),
        MockMiner(uid=9, country="BR", score=1.0, registered_at=108),
        MockMiner(uid=10, country="BR", score=1.0, registered_at=110),
    ]
    scores = {miner.uid: miner.score for miner in miners}

    # Act
    enforce_country_miner_limit(miners, scores)

    # Assert: The oldest 10 (smallest `registered_at`) stay
    sorted_by_reg = sorted(miners, key=lambda m: m.registered_at)
    uids_to_keep = {m.uid for m in sorted_by_reg[:MAX_MINERS_PER_COUNTRY]}

    for miner in miners:
        if miner.uid in uids_to_keep:
            assert scores[miner.uid] == 1.0
            assert miner.score == 1.0
        else:
            assert scores[miner.uid] == 0.0
            assert miner.score == 0.0
