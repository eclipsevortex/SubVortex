import typing
import traceback
import bittensor.utils.btlogging as btul

from subvortex.miner.neuron.src.models.score import MinerScore100, Score
from subvortex.core.metagraph.database import NeuronReadOnlyDatabase


class Database(NeuronReadOnlyDatabase):
    """
    Extended database class for validator logic that handles both read and write access
    to neuron and miner data, as well as selected miner UIDs.

    This class supports:
    - Reading and writing selected miners (validator selection state)
    - Reading and updating miner metadata
    - Fallback support for multiple schema/model versions
    - Tracking the last update block for neurons

    It builds upon NeuronReadOnlyDatabase and adds write access and multi-model support
    for 'selection' and 'miner' domains.
    """

    def __init__(self, settings):
        super().__init__(settings=settings)

        self.setup_neuron_models()
        self.models["score"] = {x.version: x for x in [MinerScore100()]}

    async def get_scores(self) -> typing.List[Score]:
        # Ensure the connection is up and running
        await self.ensure_connection()

        # Get a client
        client = await self.get_client()

        # Get the active versions
        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                # Attempt to read all neurons using the model
                neurons = await model.read_all(client)
                return neurons

            except Exception as ex:
                btul.logging.warning(
                    f"[get_scores] Failed to read all scores using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_scores] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return []

    async def save_scores(self, score: Score, max_entries: int = 100):
        """
        Bulk update for a list of miners using active model versions.
        """
        await self.ensure_connection()

        # Get a client
        client = await self.get_client()

        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                await model.write(client, score)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update score failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[update_score] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def prune_scores(self, max_entries: int):
        await self.ensure_connection()

        # Get a client
        client = await self.get_client()

        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                await model.prune(client, max_entries)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update score failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[update_score] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None
