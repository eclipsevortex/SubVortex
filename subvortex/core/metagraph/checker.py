import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.country.country as sccc
import subvortex.core.model.neuron.neuron as scmm
import subvortex.core.metagraph.database as scmd
import subvortex.core.metagraph.settings as scms


class MetagraphChecker:
    def __init__(
        self,
        settings: scms.Settings,
        database: scmd.NeuronDatabase,
        subtensor: btcas.AsyncSubtensor,
        metagraph: btcm.AsyncMetagraph,
        with_country: bool = False,
        uid: int = None,
    ):
        self.settings = settings
        self.database = database
        self.subtensor = subtensor
        self.metagraph = metagraph
        self.with_country = with_country
        self.uid = uid

    async def run(self):
        btul.logging.info("🔍 Starting metagraph vs Redis consistency check...")

        btul.logging.info(f"🌐 Country detection enabled: {self.with_country}")

        last_updated = await self.database.get_neuron_last_updated()
        btul.logging.info(f"🕒 Last updated block: {last_updated}")

        # Sync the metagraph
        await self.metagraph.sync(
            subtensor=self.subtensor,
            block=last_updated,
            lite=False,
        )
        btul.logging.info(f"✅ Metagraph synced at block {last_updated}.")

        successfull_neurons = 0
        for neuron in self.metagraph.neurons:
            if self.uid is not None and self.uid != neuron.uid:
                continue

            btul.logging.debug(
                f"🔎 Checking neuron: {neuron.hotkey} (uid={neuron.uid})"
            )

            # Get the neuron stored
            stored_neuron = await self.database.get_neuron(neuron.hotkey)

            # Build the neuron from the metagraph
            expected_neuron = scmm.Neuron.from_proto(neuron)

            if self.with_country:
                expected_neuron.country = sccc.get_country(expected_neuron.ip)

            mismatches = []
            for key, expected_value in expected_neuron.__dict__.items():
                if key == "country" and not self.with_country:
                    continue

                stored_value = getattr(stored_neuron, key, None)
                if expected_value != stored_value:
                    mismatches.append(
                        f"{key}: expected={expected_value}, actual={stored_value}"
                    )

            if mismatches:
                btul.logging.error(
                    f"❌ Neuron mismatch for hotkey={neuron.hotkey} (uid={neuron.uid}):"
                )
                for line in mismatches:
                    btul.logging.error(f"  - {line}")
            else:
                successfull_neurons = successfull_neurons + 1
                properties = expected_neuron.__dict__.items()
                btul.logging.debug(
                    f"✅ Neuron {neuron.hotkey} is consistent ({(len(properties))} properties)."
                )

        total = len(self.metagraph.neurons) if not self.uid else 1
        btul.logging.success(
            f"🎉 {successfull_neurons}/{total} neurons are consistent between metagraph and Redis."
        )
