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
