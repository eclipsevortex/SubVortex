import bittensor.utils.btlogging as btul

from subvortex.core.database.database import Database as BaseDatabase
from subvortex.validator.core.database import get_field_value
from subvortex.validator.neuron.src.models.statistics import StatisticModel200
from subvortex.validator.neuron.src.models.selection import SelectionModel200


class Database(BaseDatabase):
    def __init__(self, settings):
        super().__init__(settings=settings)

        self.models = {
            "statistic": {x.version: x for x in [StatisticModel200()]},
            "selection": {x.version: x for x in [SelectionModel200()]},
        }

    async def get_hotkey_statistics(self, ss58_address: str):
        """
        Return the stastistics metadata for the hotkey from the database
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("statistic")

        for version in reversed(active):  # Prefer newer
            model = self.models["statistic"][version]
            if not model:
                continue

            try:
                data = await model.read(self.database, ss58_address)
                return data

            except Exception as ex:
                btul.logging.warn(
                    f"[{version}] Read failed for {ss58_address}: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def update_hotkey_statistics(self, ss58_address: str, data):
        """
        Return the stastistics metadata for the hotkey from the database
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        # Get the active versions
        _, active = await self._get_migration_status("statistic")

        for version in active:
            model = self.models["statistic"].get(version)
            if not model:
                continue

            try:
                await model.write(self.database, ss58_address, data)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Write failed for {ss58_address}: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

    async def remove_hotkey_stastitics(self, ss58_address: str):
        """
        Return the stastistics metadata for the hotkey from the database
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        for version, model in self.models["statistic"].items():
            try:
                await model.delete(self.database, ss58_address)

            except Exception as ex:
                btul.logging.error(
                    f"[{version}] Delete failed for {ss58_address}: {ex}",
                    prefix=self.settings.logging_name,
                )

        return None

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
                btul.logging.warn(
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

    async def _get_migration_status(self, model_name: str):
        """
        Returns:
            - latest_version: the 'new' version
            - active_versions: versions marked 'dual' or 'new'
        """
        # Ensure the connection is ip and running
        await self.ensure_connection()

        latest = None
        active = []

        for version in sorted(self.models[model_name].keys()):
            mode = await self.database.get(f"migration_mode:{version}")
            mode = get_field_value(mode)

            if mode == "new":
                latest = version

            if mode in ("dual", "new"):
                active.append(version)

        if len(active) == 0:
            btul.logging.warning(
                f"No models {model_name}", prefix=self.settings.logging_name
            )

        return latest, active
