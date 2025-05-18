import typing
import traceback

import bittensor.utils.btlogging as btul

import subvortex.core.model.neuron.neuron as scmm
from subvortex.core.database.database_utils import decode_hash
from subvortex.core.database.database import Database as BaseDatabase
from subvortex.core.model.neuron import (
    Neuron,
    NeuronModel210,
)


class NeuronReadOnlyDatabase(BaseDatabase):
    """
    A read-only database interface for neuron data.

    This class provides methods to query the neuron database for individual
    neurons or the full list of neurons, based on the current active model
    version(s). It ensures database connectivity before performing any read operations
    and gracefully handles failures by logging detailed error information.

    Use this class when you need safe access to neuron data without the risk
    of modifying it.
    """

    def setup_neuron_models(self):
        self.models["neuron"] = {x.version: x for x in [NeuronModel210()]}

    async def get_neuron(self, hotkey: str) -> typing.List[scmm.Neuron]:
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                neuron = await model.read(self.database, hotkey)
                return neuron

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read neuron failed for hotkey {hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def get_neurons(self) -> typing.List[scmm.Neuron]:
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                neurons = await model.read_all(self.database)
                return neurons

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read neurons failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return []


class NeuronDatabase(NeuronReadOnlyDatabase):
    """
    A full read-write database interface for neuron data, extending NeuronReadOnlyDatabase.

    This class provides methods to:
    - Update or remove neuron records in the database.
    - Track and persist the last block when the metagraph was updated.
    - Mark the current metagraph state as ready/unready.
    - Notify downstream listeners of metagraph state changes via Redis streams.

    Use this class in components responsible for managing or syncing neuron state.
    """

    def __init__(self, settings):
        super().__init__(settings=settings)
        self.setup_neuron_models()

    async def update_neurons(self, neurons: typing.List[scmm.Neuron]):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                await model.write_all(self.database, neurons)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update neurons failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def remove_neurons(self, neurons: list[Neuron]):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        for version, model in self.models["neuron"].items():
            try:
                await model.delete_all(self.database, neurons)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Remove neurons failed: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def get_last_updated(self):
        """
        Get the block of the last time the metagraph has been updated
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        try:
            raw = await self.database.get(self._key("state:neuron:last_updated"))
            return int(decode_hash(raw) or 0)

        except Exception as ex:
            btul.logging.error(
                f"Read failed for last updated: {ex}",
                prefix=self.settings.logging_name,
            )

        return 0

    async def set_last_updated(self, block: int):
        """
        Set the block of the last time the metagraph has been updated
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        try:
            await self.database.set(self._key("state:neuron:last_updated"), str(block))

        except Exception as ex:
            btul.logging.error(
                f"Write failed for last updated at block #{block}: {ex}",
                prefix=self.settings.logging_name,
            )

    async def mark_as_ready(self):
        await self._set_state(state="ready")

    async def mark_as_unready(self):
        await self._set_state(state="unready")

    async def notify_state(self):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        try:
            # Get the state
            state = await self.database.get(self._key("state:metagraph"))

            # Notify the state
            await self.database.xadd(
                self._key("state:metagraph:stream"), {"state": state}
            )
        except Exception as ex:
            btul.logging.error(
                f"Failed to get neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )

    def _key(self, key: str):
        return f"{self.settings.key_prefix}:{key}"

    async def _set_state(self, state: str):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        try:
            await self.database.set(self._key("state:metagraph"), state)
        except Exception as ex:
            btul.logging.error(
                f"Failed to get neurons: {ex}", prefix=self.settings.logging_name
            )
            btul.logging.debug(
                traceback.format_exc(), prefix=self.settings.logging_name
            )
