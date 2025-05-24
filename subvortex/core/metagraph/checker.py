import bittensor.core.metagraph as btcm
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

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
    ):
        self.settings = settings
        self.database = database
        self.subtensor = subtensor
        self.metagraph = metagraph

    async def run(self):
        btul.logging.info("🔍 Starting metagraph vs Redis consistency check...")

        last_updated = await self.database.get_neuron_last_updated()
        btul.logging.info(f"🕒 Last updated block: {last_updated}")

        # Sync the metagraph
        await self.metagraph.sync(subtensor=self.subtensor, block=last_updated, lite=False)
        btul.logging.info("✅ Metagraph synced at recorded block.")

        successfull_neurons = 0
        for neuron in self.metagraph.neurons:
            btul.logging.debug(
                f"🔎 Checking neuron: {neuron.hotkey} (uid={neuron.uid})"
            )

            stored_neuron = await self.database.get_neuron(neuron.hotkey)
            expected_neuron = scmm.Neuron.from_proto(neuron)

            mismatches = []
            for key, expected_value in expected_neuron.__dict__.items():
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
                btul.logging.debug(f"✅ Neuron {neuron.hotkey} is consistent.")

        btul.logging.success(
            f"🎉 {successfull_neurons}/{len(self.metagraph.neurons)} neurons are consistent between metagraph and Redis."
        )
