import traceback

import bittensor.utils.btlogging as btul

from subvortex.core.database.database_utils import decode_hash, decode_value
from subvortex.core.metagraph.database import NeuronReadOnlyDatabase
from subvortex.validator.core.model.schedule import (
    Schedule,
    ScheduleModel210,
)
from subvortex.validator.core.model.challenge import (
    Challenge,
    ChallengeModel210,
)


class ChallengerDatabase(NeuronReadOnlyDatabase):

    def __init__(self, settings):
        super().__init__(settings=settings)

        # Register neuron models keyed by their version
        self.models["schedule"] = {x.version: x for x in [ScheduleModel210()]}
        self.models["challenge"] = {x.version: x for x in [ChallengeModel210()]}

    async def get_schedule(self, hotkey: str) -> Schedule:
        # Ensure the connection is up and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("schedule")

        for version in reversed(active):
            model = self.models["schedule"][version]
            if not model:
                continue

            try:
                # Attempt to read the neuron using the model
                neuron = await model.read(self.database, hotkey)
                return neuron

            except Exception as ex:
                btul.logging.warning(
                    f"[get_schedule] Failed to read schedule for hotkey='{hotkey}' using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_schedule] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def add_schedule(self, schedule: Schedule):
        # Ensure the connection is up and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in active:
            model = self.models["schedule"].get(version)
            if not model:
                continue

            try:
                await model.write(self.database, schedule)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add schedule failed for {schedule.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[add_schedule] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def add_challenge(self, challenge: Challenge):
        # Ensure the connection is up and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in active:
            model = self.models["challenge"].get(version)
            if not model:
                continue

            try:
                await model.write(self.database, challenge)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add challenge failed for {challenge.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[add_challnge] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    def _key(self, key: str):
        # Prefixes keys to namespace them under this service
        return f"{self.settings.key_prefix}:{key}"
