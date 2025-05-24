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
import copy
import uuid
import uvicorn
import bittensor.core.config as btcc
import bittensor.core.axon as btca
import bittensor.core.threadpool as btct
import bittensor.utils.networking as btun
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw
from inspect import Signature
from fastapi import FastAPI, APIRouter
from typing import Optional, Callable, Tuple

from subvortex.core.core_bittensor.synapse import Synapse


class SubVortexAxon(btca.Axon):
    def __init__(
        self,
        wallet: Optional["btw.Wallet"] = None,
        config: Optional["btcc.Config"] = None,
        port: Optional[int] = None,
        ip: Optional[str] = None,
        external_ip: Optional[str] = None,
        external_port: Optional[int] = None,
        max_workers: Optional[int] = None,
        blacklist_fn: Callable[[Synapse], Tuple[bool, str]] = None,
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
        config.axon.ip = ip or config.axon.ip
        config.axon.port = port or config.axon.port
        config.axon.external_ip = external_ip or config.axon.external_ip
        config.axon.external_port = external_port or config.axon.external_port
        config.axon.max_workers = max_workers or config.axon.max_workers
        btca.Axon.check_config(config)
        self.config = config  # type: ignore

        # Get wallet or use default.
        self.wallet = wallet or btw.Wallet(config=self.config)

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
            forward_fn=ping, verify_fn=None, blacklist_fn=blacklist_fn, priority_fn=None
        )
