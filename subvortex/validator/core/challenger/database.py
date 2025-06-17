import traceback

import bittensor.utils.btlogging as btul

from subvortex.core.metagraph.database import NeuronReadOnlyDatabase
from subvortex.core.model.schedule import (
    Schedule,
    ScheduleModel210,
)
from subvortex.core.model.challenge import (
    Challenge,
    ChallengeModel210,
)
from subvortex.validator.core.database.miner import MinerDatabase
from subvortex.validator.core.challenger.settings import Settings
from subvortex.validator.core.model.score import Score, ScoreModel210


class Database(NeuronReadOnlyDatabase, MinerDatabase):
    def __init__(self, settings: Settings):
        super().__init__(settings=settings)

        # Register neuron models keyed by their version
        self.models["schedule"] = {x.version: x for x in [ScheduleModel210()]}
        self.models["challenge"] = {x.version: x for x in [ChallengeModel210()]}
        self.models["score"] = {x.version: x for x in [ScoreModel210()]}

    async def add_schedule(self, schedule: Schedule):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "schedule" schema to use during read.
        _, active = await self._get_migration_status("schedule")

        for version in active:
            model = self.models["schedule"].get(version)
            if not model:
                continue

            try:
                await model.write(client, schedule)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add schedule failed for {schedule.id}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[add_schedule] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def add_challenge(self, challenge: Challenge):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "challenge" schema to use during read.
        _, active = await self._get_migration_status("challenge")

        for version in active:
            model = self.models["challenge"].get(version)
            if not model:
                continue

            try:
                await model.write(client, challenge)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add challenge failed for {challenge.id}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[add_challenge] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def get_scores(self, hotkey: str) -> dict[str, Score]:
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                miners = await model.read_by_hotkey(client, hotkey)
                return miners

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read scores failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_scores] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def save_score(self, score: Score):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "neuron" schema to use during read.
        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                # Attempt to write all neurons to the database
                await model.write(client, score)

            except Exception as ex:
                btul.logging.warning(
                    f"[save_score] Failed to save score using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[save_score] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None
    
    async def save_scores(self, scores: list[Score]):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "neuron" schema to use during read.
        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                # Attempt to write all neurons to the database
                await model.write_all(client, scores)

            except Exception as ex:
                btul.logging.warning(
                    f"[save_score] Failed to save score using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[save_score] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None
