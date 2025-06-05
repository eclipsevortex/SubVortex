import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.country.country as sccc
import subvortex.core.model.neuron.neuron as scmm
import subvortex.core.metagraph.database as scmd
import subvortex.core.metagraph.settings as scms
import subvortex.core.utils as scsu


class MetagraphChecker:
    def __init__(
        self,
        settings: scms.Settings,
        database: scmd.NeuronDatabase,
        subtensor: btcas.AsyncSubtensor,
        metagraph: btcm.AsyncMetagraph = None,
        with_country: bool = False,
        uid: int = None,
        verbose: bool = True,
    ):
        self.settings = settings
        self.database = database
        self.subtensor = subtensor
        self.metagraph = metagraph
        self.with_country = with_country
        self.uid = uid
        self.verbose = verbose

    async def run(self):
        self._log("info", "🔍 Starting metagraph vs Redis consistency check...")
        self._log("info", f"🌐 Country detection enabled: {self.with_country}")

        last_updated = await self.database.get_neuron_last_updated()
        self._log("info", f"🕒 Last updated block: {last_updated}")

        if self.metagraph is None:
            self.metagraph = await self.subtensor.metagraph(netuid=self.settings.netuid)

        await self.metagraph.sync(
            subtensor=self.subtensor,
            block=last_updated,
            lite=False,
        )
        self._log("info", f"✅ Metagraph synced at block {last_updated}.")

        successfull_neurons = 0
        all_mismatches = []
        for neuron in self.metagraph.neurons:
            if self.uid is not None and self.uid != neuron.uid:
                continue

            self._log(
                "debug", f"🔎 Checking neuron: {neuron.hotkey} (uid={neuron.uid})"
            )

            stored_neuron = await self.database.get_neuron(neuron.hotkey)
            expected_neuron = scmm.Neuron.from_proto(neuron)

            if self.with_country:
                expected_neuron.country = (
                    sccc.get_country(expected_neuron.ip)
                    if expected_neuron.ip != "0.0.0.0"
                    and scsu.is_valid_ipv4(expected_neuron.ip)
                    else None
                )

            neuron_mismatches = []
            for key, expected_value in expected_neuron.__dict__.items():
                if key == "country" and not self.with_country:
                    continue

                stored_value = getattr(stored_neuron, key, None)
                if expected_value != stored_value:
                    mismatch = {
                        "hotkey": neuron.hotkey,
                        "uid": neuron.uid,
                        "field": key,
                        "expected": expected_value,
                        "actual": stored_value,
                    }
                    neuron_mismatches.append(mismatch)

            if neuron_mismatches:
                self._log(
                    "error",
                    f"❌ Neuron mismatch for hotkey={neuron.hotkey} (uid={neuron.uid}):",
                )
                for mismatch in neuron_mismatches:
                    self._log(
                        "error",
                        f"  - {mismatch['field']}: expected={mismatch['expected']}, actual={mismatch['actual']}",
                    )

                all_mismatches.extend(neuron_mismatches)
            else:
                successfull_neurons += 1
                self._log(
                    "debug",
                    f"✅ Neuron {neuron.hotkey} is consistent ({len(expected_neuron.__dict__)} properties).",
                )

        total = len(self.metagraph.neurons) if self.uid is None else 1
        self._log(
            "success",
            f"🎉 {successfull_neurons}/{total} neurons are consistent between metagraph and Redis.",
        )

        return (successfull_neurons, total, all_mismatches)

    def _log(self, level: str, message: str):
        if not self.verbose:
            return

        log_func = getattr(btul.logging, level, None)
        if log_func:
            log_func(message)
