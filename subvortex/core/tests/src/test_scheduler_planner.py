import pytest

import subvortex.core.scheduler.settings as svcss
import subvortex.core.scheduler.scheduler_planner as svccs

from subvortex.core.tests.mock.neuron import create_validator


@pytest.mark.asyncio
async def test_get_schedules_when_the_number_of_validators_is_less_than_the_number_of_country_should_compute_the_right_schedule(
    subtensor,
):
    # Arrange
    settings = svcss.Settings()

    countries = [
        ("US", 3),
        ("JP", 26),
        ("FR", 20),
        ("GB", 1),
        ("MX", 10),
        ("CA", 5),
        ("IT", 17),
        ("SP", 2),
        ("HK", 15),
        ("TW", 1),
    ]

    challengers = [
        create_validator(
            uid=i + 1,
            country="US",
            hotkey="5F3sa2TJXJzYqSRyyoPybRhFZ9iSQ8mbHTZ4s5bSjG5z7V" + countries[i][0],
            total_stake=10 * (i + 1),
        )
        for i in range(5)
    ]

    cycle = svccs.get_next_cycle(
        settings=settings, netuid=92, block=4095736, countries=countries
    )

    # Act
    schedules = await svccs.get_schedules(
        substrate=subtensor.substrate,
        settings=settings,
        cycle=cycle,
        challengers=challengers,
        countries=countries,
    )

    # Assert
    # Check all validator have a schedule
    assert len(challengers) == len(schedules)

    for schedule in schedules.values():
        # Check each validator contains a step for each country
        scheduled_countries = [x.country for x in schedule]
        assert len(countries) == len(scheduled_countries)
        assert len(countries) == len(set(scheduled_countries))

        # Check step by step
        for i in range(len(schedule)):
            # # Check no collision in terms of country across all challengers
            # step_countries = [x[i].country for x in schedules.values()]
            # assert len(countries) == len(set(step_countries))

            # Check the cycle
            cycle_start = [x[i].cycle_start for x in schedules.values()]
            assert 1 == len(set(cycle_start))
            assert cycle.start == cycle_start[0]

            cycle_end = [x[i].cycle_end for x in schedules.values()]
            assert 1 == len(set(cycle_end))
            assert cycle.stop == cycle_end[0]

            step_start = cycle.start if i == 0 else schedule[i - 1].block_end
            block_start = [x[i].block_start for x in schedules.values()]
            assert 1 == len(set(block_start))
            assert step_start == block_start[0]

            step_end = (
                cycle.stop if i >= len(schedule) - 1 else schedule[i + 1].block_start
            )
            block_end = [x[i].block_end for x in schedules.values()]
            assert 1 == len(set(block_end))
            assert step_end == block_end[0]

        # Check validator by validator
        for i, (step) in enumerate(schedule):
            # # Check the cycle
            # assert cycle.start == step.cycle_start
            # assert cycle.stop == step.cycle_end

            # Check the step
            step_start = cycle.start if i == 0 else schedule[i - 1].block_end
            assert step_start == step.block_start

            step_end = (
                schedule[i + 1].block_start if i < len(schedule) - 1 else cycle.stop
            )
            assert step_end == step.block_end

    # Check for collision
    for i in range(len(countries)):
        scheduled_country = [x[i].country for x in schedules.values()]
        assert len(challengers) == len(scheduled_country)
        assert len(countries) != len(scheduled_country)


@pytest.mark.asyncio
async def test_get_schedules_when_the_number_of_validators_is_greater_than_the_number_of_country_should_compute_the_right_schedule(
    subtensor,
):
    # Arrange
    settings = svcss.Settings()

    countries = [("US", 3), ("JP", 26), ("FR", 20), ("GB", 1), ("MX", 10)]

    challengers = [
        create_validator(
            uid=i + 1,
            country="US",
            hotkey=f"5F3sa2TJXJzYqSRyyoPybRhFZ9iSQ8mbHTZ4s5bSjG5z7V{i}",
        )
        for i in range(10)
    ]

    cycle = svccs.get_next_cycle(
        settings=settings, netuid=92, block=4095736, countries=countries
    )

    # Act
    schedules = await svccs.get_schedules(
        substrate=subtensor.substrate,
        settings=settings,
        cycle=cycle,
        challengers=challengers,
        countries=countries,
    )

    # Assert
    # Check not all the challengers have a schedule
    assert len(challengers) > len(schedules)

    for schedule in schedules.values():
        # Check each validator contains a step for each country
        scheduled_countries = [x.country for x in schedule]
        assert len(countries) == len(scheduled_countries)
        assert len(countries) == len(set(scheduled_countries))

        # Check step by step
        for i in range(len(schedule)):
            # Check no collision in terms of country across all challengers
            step_countries = [x[i].country for x in schedules.values()]
            assert len(countries) == len(step_countries)

            # Check the cycle
            cycle_start = [x[i].cycle_start for x in schedules.values()]
            assert 1 == len(set(cycle_start))
            assert cycle.start == cycle_start[0]

            cycle_end = [x[i].cycle_end for x in schedules.values()]
            assert 1 == len(set(cycle_end))
            assert cycle.stop == cycle_end[0]

            step_start = cycle.start if i == 0 else schedule[i - 1].block_end
            block_start = [x[i].block_start for x in schedules.values()]
            assert 1 == len(set(block_start))
            assert step_start == block_start[0]

            step_end = (
                cycle.stop if i >= len(schedule) - 1 else schedule[i + 1].block_start
            )
            block_end = [x[i].block_end for x in schedules.values()]
            assert 1 == len(set(block_end))
            assert step_end == block_end[0]

        for i, (step) in enumerate(schedule):
            # Check the cycle
            assert cycle.start == step.cycle_start
            assert cycle.stop == step.cycle_end

            # Check the step
            step_start = cycle.start if i == 0 else schedule[i - 1].block_end
            assert step_start == step.block_start

            step_end = (
                schedule[i + 1].block_start if i < len(schedule) - 1 else cycle.stop
            )
            assert step_end == step.block_end

    # Check for collision
    for i in range(len(countries)):
        scheduled_country = [x[i].country for x in schedules.values()]
        assert len(countries) == len(scheduled_country)
