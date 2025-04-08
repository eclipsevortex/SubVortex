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

import os
import torch
import argparse
import datetime
import bittensor.utils.btlogging as btul
import bittensor.core.config as btcc
import bittensor.core.axon as btca
import bittensor.core.subtensor as btcs
import bittensor.utils.btlogging as btul
import bittensor_wallet.wallet as btw
from loguru import logger


def check_config(cls, config: "btcc.Config"):
    r"""Checks/validates the config namespace object."""
    btul.logging.check_config(config)

    if config.mock:
        config.wallet._mock = True

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            config.netuid,
            config.miner.name,
        )
    )
    log_path = os.path.join(full_path, "logs", timestamp)

    config.miner.log_path = os.path.expanduser(log_path)
    config.miner.full_path = os.path.expanduser(full_path)
    config.miner.request_log_path = os.path.join(
        full_path, config.miner.request_log_name
    )

    if not os.path.exists(config.miner.full_path):
        os.makedirs(config.miner.full_path, exist_ok=True)
    if not os.path.exists(config.miner.log_path):
        os.makedirs(config.miner.log_path, exist_ok=True)

    if not config.miner.dont_save_events:
        # Add custom event logger for the events.
        logger.level("EVENTS", no=38, icon="📝")
        logger.add(
            config.miner.log_path + "/" + "EVENTS.log",
            rotation=config.miner.events_retention_size,
            serialize=True,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            level="EVENTS",
            format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        )

        logger.add(
            config.miner.log_path + "/" + "INFO.log",
            rotation=config.miner.events_retention_size,
            serialize=True,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            level="INFO",
            format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        )

        if config.logging.debug:
            logger.add(
                config.miner.log_path + "/" + "DEBUG.log",
                rotation=config.miner.events_retention_size,
                serialize=True,
                enqueue=True,
                backtrace=False,
                diagnose=False,
                level="DEBUG",
                format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
            )

        if config.logging.trace:
            logger.add(
                config.miner.log_path + "/" + "TRACE.log",
                rotation=config.miner.events_retention_size,
                serialize=True,
                enqueue=True,
                backtrace=False,
                diagnose=False,
                level="TRACE",
                format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
            )


def add_args(cls, parser):
    parser.add_argument(
        "--netuid", type=int, help="Subvortex network netuid", default=7
    )
    parser.add_argument(
        "--miner.name",
        type=str,
        help="Trials for this miner go in miner.root / (wallet_cold - wallet_hot) / miner.name. ",
        default="subvortex_miner",
    )
    parser.add_argument(
        "--miner.device",
        type=str,
        help="Device to run the validator on.",
        default="cuda" if torch.cuda.is_available() else "cpu",
    )
    parser.add_argument("--miner.verbose", default=False, action="store_true")
    parser.add_argument(
        "--miner.request_log_name",
        type=str,
        help="Name of the request log file",
        default="requests_log.json",
    )

    # Auto update
    parser.add_argument(
        "--auto-update",
        action="store_true",
        help="True if the miner can be auto updated, false otherwise",
        default=False,
    )

    # Mocks.
    parser.add_argument(
        "--miner.mock_subtensor",
        action="store_true",
        help="If True, the miner will allow non-registered hotkeys to mine.",
        default=False,
    )

    # Firewall
    parser.add_argument(
        "--firewall.on",
        action="store_true",
        help="True to enable the firewall feature, False otherwise",
        default=False,
    )
    parser.add_argument(
        "--firewall.interface",
        type=str,
        required=False,
        help="Interface to listen the traffic to (default eth0)",
        default="eth0",
    )
    parser.add_argument(
        "--firewall.config",
        type=str,
        required=False,
        help="List of ports to forward but not to sniff",
        default="firewall.json",
    )

    # Blacklist.
    parser.add_argument(
        "--blacklist.blacklist_hotkeys",
        type=str,
        required=False,
        nargs="*",
        help="Blacklist certain hotkeys",
        default=[],
    )
    parser.add_argument(
        "--blacklist.whitelist_hotkeys",
        type=str,
        required=False,
        nargs="*",
        help="Whitelist certain hotkeys",
        default=[],
    )

    # SSE
    parser.add_argument(
        "--sse.port",
        type=int,
        required=False,
        help="Port used for the SSE server",
        default=5000,
    )
    parser.add_argument(
        "--sse.firewall.ip",
        type=str,
        required=False,
        help="Allowed Ip to subscribe to the firewall stream. It has to be the ip used to display the firewall UI",
        default=None,
    )

    # Mocks
    parser.add_argument(
        "--mock", action="store_true", help="Mock all items.", default=False
    )


def config(cls):
    parser = argparse.ArgumentParser()
    btcs.Subtensor.add_args(parser)
    btul.logging.add_args(parser)
    btw.Wallet.add_args(parser)
    btca.Axon.add_args(parser)
    cls.add_args(parser)
    return btcc.Config(parser)
