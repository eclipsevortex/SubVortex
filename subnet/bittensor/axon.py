import copy
import uuid
import uvicorn
import bittensor as bt
from inspect import Signature
from bittensor.axon import AxonMiddleware, FastAPIThreadedServer
from fastapi import FastAPI, APIRouter
from typing import Optional, Callable, Tuple, Dict, List

from subnet.bittensor.synapse import Synapse


class SubVortexAxon(bt.axon):
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
        self.app = FastAPI()
        log_level = "trace" if bt.logging.__trace_on__ else "critical"
        self.fast_config = uvicorn.Config(
            self.app, host="0.0.0.0", port=self.config.axon.port, log_level=log_level
        )
        self.fast_server = FastAPIThreadedServer(config=self.fast_config)
        self.router = APIRouter()
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
