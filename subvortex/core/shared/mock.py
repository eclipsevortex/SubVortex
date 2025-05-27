# The MIT License (MIT)
# Copyright © 2024 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import time
import copy
import uuid
import uvicorn
import asyncio
import random
import bittensor.core.config as btcc
import bittensor.core.axon as btca
import bittensor.core.settings as btcse
import bittensor.core.chain_data as btcc
import bittensor.core.threadpool as btct
import bittensor.utils.balance as btub
import bittensor.utils.btlogging as btul
import bittensor.utils.networking as btun
import bittensor.utils.mock as btum
import bittensor_wallet.wallet as btw
from random import randint
from inspect import Signature
from typing import Optional, Callable
from fastapi import FastAPI, APIRouter
from typing import List, Union

from subvortex.core.core_bittensor.metagraph import SubVortexMetagraph
from subvortex.core.core_bittensor.axon import SubVortexAxon
from subvortex.core.core_bittensor.synapse import Synapse


class MockSubtensor(btum.MockSubtensor):
    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

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

    def force_register_neuron(
        self,
        netuid: int,
        hotkey: str,
        coldkey: str,
        stake: Union["btub.Balance", float, int] = btub.Balance(0),
        balance: Union["btub.Balance", float, int] = btub.Balance(0),
    ) -> int:
        """
        Force register a neuron on the mock chain, returning the UID.
        """
        stake = self._convert_to_balance(stake)
        balance = self._convert_to_balance(balance)

        subtensor_state = self.chain_state["SubtensorModule"]
        if netuid not in subtensor_state["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        uid = self._register_neuron(netuid=netuid, hotkey=hotkey, coldkey=coldkey)

        subtensor_state["TotalStake"][self.block_number] = (
            self._get_most_recent_storage(subtensor_state["TotalStake"]) + stake.rao
        )
        subtensor_state["Stake"][hotkey][coldkey][self.block_number] = stake.rao

        if balance.rao > 0:
            self.force_set_balance(coldkey, balance)
        self.force_set_balance(coldkey, balance)

        return uid

    def _register_neuron(self, netuid: int, hotkey: str, coldkey: str) -> int:
        subtensor_state = self.chain_state["SubtensorModule"]
        if netuid not in subtensor_state["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        subnetwork_n = self._get_most_recent_storage(
            subtensor_state["SubnetworkN"][netuid]
        )

        if subnetwork_n > 0 and any(
            self._get_most_recent_storage(subtensor_state["Keys"][netuid][uid])
            == hotkey
            for uid in range(subnetwork_n)
        ):
            # already_registered
            raise Exception("Hotkey already registered")
        else:
            # Not found
            if subnetwork_n >= self._get_most_recent_storage(
                subtensor_state["MaxAllowedUids"][netuid]
            ):
                # Subnet full, replace neuron randomly
                uid = randint(0, subnetwork_n - 1)
            else:
                # Subnet not full, add new neuron
                # Append as next uid and increment subnetwork_n
                uid = subnetwork_n
                subtensor_state["SubnetworkN"][netuid][self.block_number] = (
                    subnetwork_n + 1
                )

            subtensor_state["Stake"][hotkey] = {}
            subtensor_state["Stake"][hotkey][coldkey] = {}
            subtensor_state["Stake"][hotkey][coldkey][self.block_number] = 0

            subtensor_state["Uids"][netuid][hotkey] = {}
            subtensor_state["Uids"][netuid][hotkey][self.block_number] = uid

            subtensor_state["Keys"][netuid][uid] = {}
            subtensor_state["Keys"][netuid][uid][self.block_number] = hotkey

            subtensor_state["Owner"][hotkey] = {}
            subtensor_state["Owner"][hotkey][self.block_number] = coldkey

            subtensor_state["Active"][netuid][uid] = {}
            subtensor_state["Active"][netuid][uid][self.block_number] = True

            subtensor_state["LastUpdate"][netuid][uid] = {}
            subtensor_state["LastUpdate"][netuid][uid][
                self.block_number
            ] = self.block_number

            subtensor_state["Rank"][netuid][uid] = {}
            subtensor_state["Rank"][netuid][uid][self.block_number] = 0.0

            subtensor_state["Emission"][netuid][uid] = {}
            subtensor_state["Emission"][netuid][uid][self.block_number] = 0.0

            subtensor_state["Incentive"][netuid][uid] = {}
            subtensor_state["Incentive"][netuid][uid][self.block_number] = 0.0

            subtensor_state["Consensus"][netuid][uid] = {}
            subtensor_state["Consensus"][netuid][uid][self.block_number] = 0.0

            subtensor_state["Trust"][netuid][uid] = {}
            subtensor_state["Trust"][netuid][uid][self.block_number] = 0.0

            subtensor_state["ValidatorTrust"][netuid][uid] = {}
            subtensor_state["ValidatorTrust"][netuid][uid][self.block_number] = 0.0

            subtensor_state["Dividends"][netuid][uid] = {}
            subtensor_state["Dividends"][netuid][uid][self.block_number] = 0.0

            subtensor_state["PruningScores"][netuid][uid] = {}
            subtensor_state["PruningScores"][netuid][uid][self.block_number] = 0.0

            subtensor_state["ValidatorPermit"][netuid][uid] = {}
            subtensor_state["ValidatorPermit"][netuid][uid][self.block_number] = False

            subtensor_state["Weights"][netuid][uid] = {}
            subtensor_state["Weights"][netuid][uid][self.block_number] = []

            subtensor_state["Bonds"][netuid][uid] = {}
            subtensor_state["Bonds"][netuid][uid][self.block_number] = []

            subtensor_state["Axons"][netuid][hotkey] = {}
            subtensor_state["Axons"][netuid][hotkey][self.block_number] = {}

            subtensor_state["Prometheus"][netuid][hotkey] = {}
            subtensor_state["Prometheus"][netuid][hotkey][self.block_number] = {}

            if hotkey not in subtensor_state["IsNetworkMember"]:
                subtensor_state["IsNetworkMember"][hotkey] = {}
            subtensor_state["IsNetworkMember"][hotkey][netuid] = {}
            subtensor_state["IsNetworkMember"][hotkey][netuid][self.block_number] = True

            return uid

    def neuron_for_uid_lite(
        self, uid: int, netuid: int, block: Optional[int] = None
    ) -> Optional[btcc.NeuronInfoLite]:
        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        if netuid not in self.chain_state["SubtensorModule"]["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        neuron_info = self._neuron_subnet_exists(uid, netuid, block)
        if neuron_info is None:
            return None

        else:
            neuron_info_dict = neuron_info.__dict__
            del neuron_info
            del neuron_info_dict["weights"]
            del neuron_info_dict["bonds"]

            neuron_info_lite = btcc.NeuronInfoLite(**neuron_info_dict)
            return neuron_info_lite


class MockMetagraph(SubVortexMetagraph):
    def __init__(self, netuid=1, network="mock", subtensor=None):
        super().__init__(netuid=netuid, network=network, lite=True, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        btul.logging.info(f"Metagraph: {self}")
        btul.logging.info(f"Axons: {self.axons}")


class MockDendrite(SubVortexMetagraph):
    """
    Replaces a real bittensor network request with a mock request that just returns some static response for all axons that are passed and adds some random delay.
    """

    def __init__(self, wallet):
        super().__init__(wallet)

    async def forward(
        self,
        axons: List[btca.Axon],
        synapse: btca.Synapse = btca.Synapse(),
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
        wallet: Optional["btw.Wallet"] = None,
        config: Optional["btcc.Config"] = None,
        port: Optional[int] = None,
        ip: Optional[str] = None,
        external_ip: Optional[str] = None,
        external_port: Optional[int] = None,
        max_workers: Optional[int] = None,
    ):
        """Creates a new bittensor.Axon object from passed arguments.

        Args:
            config (:obj:`Optional[bittensor.core.config.Config]`): bittensor.Axon.config()
            wallet (:obj:`Optional[bittensor_wallet.Wallet]`): bittensor wallet with hotkey and coldkeypub.
            port (:type:`Optional[int]`): Binding port.
            ip (:type:`Optional[str]`): Binding ip.
            external_ip (:type:`Optional[str]`): The external ip of the server to broadcast to the network.
            external_port (:type:`Optional[int]`): The external port of the server to broadcast to the network.
            max_workers (:type:`Optional[int]`): Used to create the threadpool if not passed, specifies the number of active threads servicing requests.
        """
        # Build and check config.
        if config is None:
            config = btca.Axon.config()
        config = copy.deepcopy(config)
        config.axon.ip = ip or btcse.DEFAULTS.axon.ip
        config.axon.port = port or btcse.DEFAULTS.axon.port
        config.axon.external_ip = external_ip or btcse.DEFAULTS.axon.external_ip
        config.axon.external_port = external_port or btcse.DEFAULTS.axon.external_port
        config.axon.max_workers = max_workers or btcse.DEFAULTS.axon.max_workers
        btca.Axon.check_config(config)
        self.config = config  # type: ignore

        # Get wallet or use default.
        self.wallet = wallet or btw.Wallet()

        # Build axon objects.
        self.uuid = str(uuid.uuid1())
        self.ip = self.config.axon.ip  # type: ignore
        self.port = self.config.axon.port  # type: ignore
        self.external_ip = (
            self.config.axon.external_ip  # type: ignore
            if self.config.axon.external_ip is not None  # type: ignore
            else btun.get_external_ip()
        )
        self.external_port = (
            self.config.axon.external_port  # type: ignore
            if self.config.axon.external_port is not None  # type: ignore
            else self.config.axon.port  # type: ignore
        )
        self.full_address = str(self.config.axon.ip) + ":" + str(self.config.axon.port)  # type: ignore
        self.started = False

        # Build middleware
        self.thread_pool = btct.PriorityThreadPoolExecutor(
            max_workers=self.config.axon.max_workers  # type: ignore
        )
        self.nonces: dict[str, int] = {}

        # Request default functions.
        self.forward_class_types: dict[str, list[Signature]] = {}
        self.blacklist_fns: dict[str, Optional[Callable]] = {}
        self.priority_fns: dict[str, Optional[Callable]] = {}
        self.forward_fns: dict[str, Optional[Callable]] = {}
        self.verify_fns: dict[str, Optional[Callable]] = {}

        # Instantiate FastAPI
        self.app = FastAPI()
        log_level = "trace" if btul.logging.__trace_on__ else "critical"
        self.fast_config = uvicorn.Config(
            self.app, host="0.0.0.0", port=self.config.axon.port, log_level=log_level
        )
        self.fast_server = btca.FastAPIThreadedServer(config=self.fast_config)
        self.router = APIRouter()
        self.app.include_router(self.router)

        # Build ourselves as the middleware.
        self.middleware_cls = btca.AxonMiddleware
        self.app.add_middleware(self.middleware_cls, axon=self)

        # Attach default forward.
        def ping(r: Synapse) -> Synapse:
            return r

        self.attach(
            forward_fn=ping, verify_fn=None, blacklist_fn=None, priority_fn=None
        )
