import traceback
import bittensor.utils.btlogging as btul

from subvortex.miner.neuron.src.models.score import MinerScore211, Score
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
        self.models["score"] = {x.version: x for x in [MinerScore211()]}

    async def save_scores(self, score: Score):
        """
        Bulk update for a list of miners using active model versions.
        """
        await self.ensure_connection()

        _, active = await self._get_migration_status("score")

        for version in reversed(active):
            model = self.models["score"][version]
            if not model:
                continue

            try:
                await model.write(self.database, score)

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
