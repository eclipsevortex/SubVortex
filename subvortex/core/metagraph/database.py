import typing
import traceback

import bittensor.utils.btlogging as btul

import subvortex.core.model.neuron.neuron as scmm
from subvortex.core.database.database_utils import decode_hash, decode_value
from subvortex.core.database.database import Database as BaseDatabase
from subvortex.core.model.neuron import (
    Neuron,
    NeuronModel210,
    NeuronModel211,
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

    def __init__(self, settings):
        super().__init__(settings=settings)

        # Register neuron models keyed by their version
        self.models["neuron"] = {
            x.version: x for x in [NeuronModel210(), NeuronModel211()]
        }

    async def get_neuron(self, hotkey: str) -> scmm.Neuron:
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "neuron" schema to use during read.
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                # Attempt to read the neuron using the model
                neuron = await model.read(client, hotkey)
                return neuron

            except Exception as ex:
                btul.logging.warning(
                    f"[get_neuron] Failed to read neuron for hotkey='{hotkey}' using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_neuron] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def get_neurons(self) -> typing.Dict[str, scmm.Neuron]:
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "neuron" schema to use during read.
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                # Attempt to read all neurons using the model
                neurons = await model.read_all(client)
                return neurons

            except Exception as ex:
                btul.logging.warning(
                    f"[get_neurons] Failed to read all neurons using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_neurons] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return []

    async def get_neuron_last_updated(self):
        """
        Get the block of the last time the metagraph has been updated
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        try:
            raw = await client.get(self._key("state:neuron:last_updated"))
            return int(decode_value(raw) or 0)

        except Exception as ex:
            btul.logging.error(
                f"[get_last_updated] Failed to read last updated block: {ex}",
                prefix=self.settings.logging_name,
            )
            btul.logging.debug(
                f"[get_last_updated] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                prefix=self.settings.logging_name,
            )

        return 0


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

    async def update_neurons(self, neurons: typing.List[scmm.Neuron]):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "neuron" schema to use during read.
        _, active = await self._get_migration_status("neuron")

        for version in reversed(active):
            model = self.models["neuron"][version]
            if not model:
                continue

            try:
                # Attempt to write all neurons to the database
                await model.write_all(client, neurons)

            except Exception as ex:
                btul.logging.warning(
                    f"[update_neurons] Failed to update neurons using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[update_neurons] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def remove_neurons(self, neurons: list[Neuron]):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        for version, model in self.models["neuron"].items():
            try:
                # Attempt to delete all given neurons
                await model.delete_all(client, neurons)

            except Exception as ex:
                btul.logging.error(
                    f"[remove_neurons] Failed to remove neurons using version={version}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[remove_neurons] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def set_last_updated(self, block: int):
        """
        Set the block of the last time the metagraph has been updated
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        try:
            await client.set(self._key("state:neuron:last_updated"), str(block))

        except Exception as ex:
            btul.logging.error(
                f"[set_last_updated] Failed to write last updated block {block}: {ex}",
                prefix=self.settings.logging_name,
            )
            btul.logging.debug(
                f"[set_last_updated] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                prefix=self.settings.logging_name,
            )

    async def mark_as_ready(self):
        # Mark metagraph state as "ready"
        await self._set_state(state="ready")

    async def mark_as_unready(self):
        # Mark metagraph state as "unready"
        await self._set_state(state="unready")

    async def notify_state(self):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        try:
            # Get the current state of the metagraph
            state = await client.get(self._key("state:metagraph"))

            # Notify downstream via Redis stream
            await client.xadd(self._key("state:metagraph:stream"), {"state": state})

        except Exception as ex:
            btul.logging.error(
                f"[notify_state] Failed to notify metagraph state: {ex}",
                prefix=self.settings.logging_name,
            )
            btul.logging.debug(
                f"[notify_state] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                prefix=self.settings.logging_name,
            )

    async def get_state(self):
        """
        Get the block of the last time the metagraph has been updated
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        try:
            raw = await client.get(self._key("state:metagraph"))
            return raw

        except Exception as ex:
            btul.logging.error(
                f"[get_last_updated] Failed to read last updated block: {ex}",
                prefix=self.settings.logging_name,
            )
            btul.logging.debug(
                f"[get_last_updated] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                prefix=self.settings.logging_name,
            )

        return 0
    
    def _key(self, key: str):
        # Prefixes keys to namespace them under this service
        return f"{self.settings.key_prefix}:{key}"

    async def _set_state(self, state: str):
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        try:
            # Set the current metagraph state
            await client.set(self._key("state:metagraph"), state)

        except Exception as ex:
            btul.logging.error(
                f"[_set_state] Failed to set metagraph state='{state}': {ex}",
                prefix=self.settings.logging_name,
            )
            btul.logging.debug(
                f"[_set_state] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                prefix=self.settings.logging_name,
            )
