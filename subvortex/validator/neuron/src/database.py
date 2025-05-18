import traceback
from typing import List

import bittensor.utils.btlogging as btul

from subvortex.core.database.database import Database as BaseDatabase
from subvortex.core.model.neuron.neuron import Neuron
from subvortex.core.database.database_utils import decode_value
from subvortex.validator.neuron.src.models.selection import (
    SelectionModel200,
    SelectionModel210,
)
from subvortex.validator.neuron.src.models.miner import (
    Miner,
    MinerModel210,
)
from subvortex.core.model.neuron import (
    Neuron,
    NeuronModel210,
)


class Database(BaseDatabase):
    def __init__(self, settings):
        super().__init__(settings=settings)

        self.models = {
            "selection": {
                x.version: x for x in [SelectionModel200(), SelectionModel210()]
            },
            "neuron": {x.version: x for x in [NeuronModel210()]},
            "miner": {x.version: x for x in [MinerModel210()]},
        }

    async def get_selected_miners(self, ss58_address: str):
        """
        Return selected uids for a hotkey using versioned selection models.
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("selection")

        for version in reversed(active):  # Prefer latest version
            model = self.models["selection"].get(version)
            if not model:
                continue

            try:
                uids = await model.read(self.database, ss58_address)
                return uids

            except Exception as err:
                btul.logging.warning(
                    f"[{version}] Failed to read selected miners for {ss58_address}: {err}",
                    prefix=self.settings.logging_name,
                )

        return []

    async def set_selection_miners(self, ss58_address: str, uids: list[int]):
        """
        Store selected miner UIDs in all active selection model versions.
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("selection")

        for version in active:
            model = self.models["selection"].get(version)
            if not model:
                continue

            try:
                await model.write(self.database, ss58_address, uids)

            except Exception as err:
                btul.logging.error(
                    f"[{version}] Failed to write selection for {ss58_address}: {err}",
                    prefix=self.settings.logging_name,
                )
        return None

    async def get_neuron(self, hotkey: str) -> Neuron:
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

    async def get_neurons(self) -> dict[str, Neuron]:
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

        return None

    async def get_miner(self, hotkey: str) -> Miner:
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                miner = await model.read(self.database, hotkey)
                return miner

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read miner failed for hotkey {hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def get_miners(self) -> dict[str, Miner]:
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                miners = await model.read_all(self.database)
                return miners

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Read miners failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def add_miner(self, miner: Miner):
        """
        Return the stastistics metadata for the hotkey from the database
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in active:
            model = self.models["miner"].get(version)
            if not model:
                continue

            try:
                await model.write(self.database, miner)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Add miner failed for {miner.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def update_miner(self, miner: Miner):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                await model.write(self.database, miner)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update miner failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def update_miners(self, miners: List[Miner]):
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("miner")

        for version in reversed(active):
            model = self.models["miner"][version]
            if not model:
                continue

            try:
                await model.write_all(self.database, miners)

            except Exception as ex:
                btul.logging.warning(
                    f"[{version}] Update miners failed: {ex}",
                    prefix=self.settings.logging_name,
                )
                btul.logging.debug(traceback.format_exc())

        return None

    async def remove_miner(self, miner: Miner):
        """
        Return the stastistics metadata for the hotkey from the database
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        for version, model in self.models["miner"].items():
            try:
                await model.delete(self.database, miner)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Remove miner failed for {miner.hotkey}: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def get_neuron_last_update(self):
        """
        Get the block of the last time the metagraph has been updated
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        try:
            raw = await self.database.get(self._key("state:neuron:last_updated"))
            return int(decode_value(raw) or 0)

        except Exception as ex:
            btul.logging.error(
                f"Read failed for last updated: {ex}",
                prefix=self.settings.logging_name,
            )
