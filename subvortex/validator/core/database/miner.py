import traceback
import bittensor.utils.btlogging as btul
from typing import List

from subvortex.core.database.database import Database as BaseDatabase
from subvortex.validator.core.model.miner import (
    Miner,
    MinerModel211,
)


class MinerDatabase(BaseDatabase):
    def __init__(self, settings):
        super().__init__(settings=settings)

        # Register neuron models keyed by their version
        self.models["miner"] = {x.version: x for x in [MinerModel211()]}

    async def get_miner(self, hotkey: str) -> Miner:
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                miner = await model.read(client, hotkey)
                return miner

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read miner failed for hotkey {hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_miner] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def get_miners(self) -> dict[str, Miner]:
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                miners = await model.read_all(client)
                return miners

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read miners failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[get_miners] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def add_miner(self, miner: Miner):
        """
        Add a new miner record to all active versions of the miner schema.
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("miner")

        for version in active:
            model = self.models["miner"].get(version)
            if not model:
                continue

            try:
                await model.write(client, miner)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add miner failed for {miner.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[add_miner] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def update_miner(self, miner: Miner):
        """
        Update an existing miner record.
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                await model.write(client, miner)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update miner failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[update_miner] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def update_miners(self, miners: List[Miner]):
        """
        Bulk update for a list of miners using active model versions.
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        # Get currently active versions of the "miner" schema to use during read.
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                await model.write_all(client, miners)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update miners failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[update_miners] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def remove_miner(self, miner: Miner):
        """
        Remove a single miner entry from all available versions.
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        for version, model in self.models["miner"].items():
            try:
                await model.delete(client, miner)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Remove miner failed for {miner.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[remove_miner] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def remove_miners(self, miners: List[Miner]):
        """
        Remove a single miner entry from all available versions.
        """
        # Ensure Redis connection is established before any operation.
        await self.ensure_connection()

        # Get a connected Redis client, configured with the correct DB index and prefix.
        client = await self.get_client()

        for version, model in self.models["miner"].items():
            try:
                await model.delete_all(client, miners)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Remove miners failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(
                    f"[remove_miners] Exception type: {type(ex).__name__}, Traceback:\n{traceback.format_exc()}",
                    prefix=self.settings.logging_name,
                )

        return None
