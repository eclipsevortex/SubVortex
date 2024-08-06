import time
import copy
import uuid
import asyncio
import random
import bittensor as bt
from unittest.mock import MagicMock
from typing import Optional, Callable, Tuple, Dict, List
from bittensor.axon import AxonMiddleware

from subnet.bittensor.metagraph import SubVortexMetagraph
from subnet.bittensor.axon import SubVortexAxon
from subnet.bittensor.synapse import Synapse


class MockSubtensor(bt.MockSubtensor):
    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)

        # Register ourself (the validator) as a neuron at uid=0
        if wallet is not None:
            self.force_register_neuron(
                netuid=netuid,
                hotkey=wallet.hotkey.ss58_address,
                coldkey=wallet.coldkey.ss58_address,
                balance=100000,
                stake=100000,
            )

        # Register n mock neurons who will be miners
        for i in range(1, n + 1):
            self.force_register_neuron(
                netuid=netuid,
                hotkey=f"miner-hotkey-{i}",
                coldkey="mock-coldkey",
                balance=100000,
                stake=100000,
            )


class MockMetagraph(bt.metagraph):
    def __init__(self, netuid=1, network="mock", subtensor=None):
        super().__init__(netuid=netuid, network=network, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        bt.logging.info(f"Metagraph: {self}")
        bt.logging.info(f"Axons: {self.axons}")


class MockDendrite(SubVortexMetagraph):
    """
    Replaces a real bittensor network request with a mock request that just returns some static response for all axons that are passed and adds some random delay.
    """

    def __init__(self, wallet):
        super().__init__(wallet)

    async def forward(
        self,
        axons: List[bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 12,
        deserialize: bool = True,
        run_async: bool = True,
        streaming: bool = False,
    ):
        if streaming:
            raise NotImplementedError("Streaming not implemented yet.")

        async def query_all_axons(streaming: bool):
            """Queries all axons for responses."""

            async def single_axon_response(i, axon):
                """Queries a single axon for a response."""

                start_time = time.time()
                s = synapse.copy()
                # Attach some more required data so it looks real
                s = self.preprocess_synapse_for_request(axon, s, timeout)
                # We just want to mock the response, so we'll just fill in some data
                process_time = random.random()
                if process_time < timeout:
                    s.dendrite.process_time = str(time.time() - start_time)
                    # Update the status code and status message of the dendrite to match the axon
                    # TODO (developer): replace with your own expected synapse data
                    s.dummy_output = s.dummy_input * 2
                    s.dendrite.status_code = 200
                    s.dendrite.status_message = "OK"
                    synapse.dendrite.process_time = str(process_time)
                else:
                    s.dummy_output = 0
                    s.dendrite.status_code = 408
                    s.dendrite.status_message = "Timeout"
                    synapse.dendrite.process_time = str(timeout)

                # Return the updated synapse object after deserializing if requested
                if deserialize:
                    return s.deserialize()
                else:
                    return s

            return await asyncio.gather(
                *(
                    single_axon_response(i, target_axon)
                    for i, target_axon in enumerate(axons)
                )
            )

        return await query_all_axons(streaming)

    def __str__(self) -> str:
        """
        Returns a string representation of the Dendrite object.

        Returns:
            str: The string representation of the Dendrite object in the format "dendrite(<user_wallet_address>)".
        """
        return "MockDendrite({})".format(self.keypair.ss58_address)


class MockAxon(SubVortexAxon):
    def __init__(
        self,
        wallet: Optional["bt.wallet"] = None,
        config: Optional["bt.config"] = None,
        port: Optional[int] = None,
        ip: Optional[str] = None,
        external_ip: Optional[str] = None,
        external_port: Optional[int] = None,
        max_workers: Optional[int] = None,
        blacklist_fn: Callable[[Synapse], Tuple[bool, str]] = None,
    ):
        r"""Creates a new bt.Axon object from passed arguments.
        Args:
            config (:obj:`Optional[bt.config]`, `optional`):
                bt.axon.config()
            wallet (:obj:`Optional[bt.wallet]`, `optional`):
                bittensor wallet with hotkey and coldkeypub.
            port (:type:`Optional[int]`, `optional`):
                Binding port.
            ip (:type:`Optional[str]`, `optional`):
                Binding ip.
            external_ip (:type:`Optional[str]`, `optional`):
                The external ip of the server to broadcast to the network.
            external_port (:type:`Optional[int]`, `optional`):
                The external port of the server to broadcast to the network.
            max_workers (:type:`Optional[int]`, `optional`):
                Used to create the threadpool if not passed, specifies the number of active threads servicing requests.
        """
        # Build and check config.
        if config is None:
            config = bt.axon.config()
        config = copy.deepcopy(config)
        config.axon.ip = ip or config.axon.get("ip", bt.defaults.axon.ip)
        config.axon.port = port or config.axon.get("port", bt.defaults.axon.port)
        config.axon.external_ip = external_ip or config.axon.get(
            "external_ip", bt.defaults.axon.external_ip
        )
        config.axon.external_port = external_port or config.axon.get(
            "external_port", bt.defaults.axon.external_port
        )
        config.axon.max_workers = max_workers or config.axon.get(
            "max_workers", bt.defaults.axon.max_workers
        )
        bt.axon.check_config(config)
        self.config = config  # type: ignore [method-assign]

        # Get wallet or use default.
        self.wallet = wallet or bt.wallet()

        # Build axon objects.
        self.uuid = str(uuid.uuid1())
        self.ip = self.config.axon.ip
        self.port = self.config.axon.port
        self.external_ip = (
            self.config.axon.external_ip
            if self.config.axon.external_ip is not None
            else bt.utils.networking.get_external_ip()
        )
        self.external_port = (
            self.config.axon.external_port
            if self.config.axon.external_port is not None
            else self.config.axon.port
        )
        self.full_address = str(self.config.axon.ip) + ":" + str(self.config.axon.port)
        self.started = False

        # Build middleware
        self.thread_pool = bt.PriorityThreadPoolExecutor(
            max_workers=self.config.axon.max_workers
        )
        self.nonces: Dict[str, int] = {}

        # Request default functions.
        self.forward_class_types: Dict[str, List[Signature]] = {}
        self.blacklist_fns: Dict[str, Optional[Callable]] = {}
        self.priority_fns: Dict[str, Optional[Callable]] = {}
        self.forward_fns: Dict[str, Optional[Callable]] = {}
        self.verify_fns: Dict[str, Optional[Callable]] = {}

        # Instantiate FastAPI
        self.app = MagicMock()
        self.fast_server = MagicMock()
        self.router = MagicMock()
        self.app.include_router(self.router)

        # Build ourselves as the middleware.
        self.middleware_cls = AxonMiddleware
        self.app.add_middleware(self.middleware_cls, axon=self)

        # Attach default forward.
        def ping(r: Synapse) -> Synapse:
            return r

        self.attach(
            forward_fn=ping, verify_fn=None, blacklist_fn=blacklist_fn, priority_fn=None
        )