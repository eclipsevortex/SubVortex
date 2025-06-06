import asyncio
import signal
import argparse
import traceback
from typing import Optional

from dotenv import load_dotenv
import bittensor.utils.btlogging as btul
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.core.metagraph as btcm
import bittensor.core.settings as btcs
import bittensor_wallet.utils as btwu

import subvortex.core.core_bittensor.config.config_utils as scccu
import subvortex.core.core_bittensor.subtensor as sccs
import subvortex.core.metagraph.metagraph as scmm
import subvortex.core.metagraph.database as scmms
import subvortex.core.version as scv
import subvortex.validator.metagraph.src.settings as smme

load_dotenv(override=True)


class Runner:
    def __init__(self):
        self.metagraph_observer: Optional[scmm.MetagraphObserver] = None
        self.subtensor: Optional[btcas.AsyncSubtensor] = None

    async def wait_for_database_connection(self, settings, database):
        if settings.dry_run:
            return

        btul.logging.warning(
            "⏳ Waiting for Redis to become available...", prefix=settings.logging_name
        )
        await database.ensure_connection()

        while not await database.is_connection_alive():
            await asyncio.sleep(1)

        btul.logging.info("✅ Connected to Redis.", prefix=settings.logging_name)

    async def start(self):
        parser = argparse.ArgumentParser()
        btul.logging.add_args(parser)
        btcas.AsyncSubtensor.add_args(parser)

        # Create the configuration
        config = btcc.Config(parser)

        # Create settings
        settings = smme.Settings.create()
        scccu.update_config(settings, config, parser)

        # Initialise logging
        btul.logging(config=config, debug=True)
        btul.logging.set_trace(config.logging.trace)
        btul.logging._stream_formatter.set_trace(config.logging.trace)

        # Display the settings
        btul.logging.info(f"Settings: {settings}")

        # Show validator version
        version = scv.get_version()
        btul.logging.debug(f"Version: {version}")

        try:
            # Create the storage
            database = scmms.NeuronDatabase(settings=settings)
            await self.wait_for_database_connection(
                settings=settings, database=database
            )

            # Initialize the subtensor
            self.subtensor = btcas.AsyncSubtensor(config=config, retry_forever=True)

            # TODO: remove once OTF patched it
            self.subtensor.substrate = sccs.RetryAsyncSubstrate(
                url=self.subtensor.chain_endpoint,
                ss58_format=btwu.SS58_FORMAT,
                type_registry=btcs.TYPE_REGISTRY,
                retry_forever=True,
                use_remote_preset=True,
                chain_name="Bittensor",
                _mock=False,
            )
            await self.subtensor.initialize()
            btul.logging.info(str(self.subtensor))

            settings.dry_run and btul.logging.info("Dry run mode enabled")

            # Initialize the metagraph
            # TODO: Tell OTF if I provide the subtensor the network will be finney even if the subtensor is in test!
            metagraph = btcm.AsyncMetagraph(
                netuid=settings.netuid, network=self.subtensor.network, sync=False
            )
            btul.logging.info(str(metagraph))

            # Create and run the metagraph observer
            self.metagraph_observer = scmm.MetagraphObserver(
                settings=settings,
                subtensor=self.subtensor,
                metagraph=metagraph,
                database=database,
            )
            await self.metagraph_observer.start()

        except Exception as e:
            btul.logging.error(f"Unhandled exception: {e}")
            btul.logging.debug(traceback.format_exc())

    async def shutdown(self):
        btul.logging.info("Shutting down...")

        if getattr(self, "metagraph_observer", None):
            await self.metagraph_observer.stop()

        if getattr(self, "subtensor", None):
            await self.subtensor.close()
            btul.logging.debug("Subtensor stopped")

        btul.logging.info("Shutting down completed")


if __name__ == "__main__":
    runner = Runner()

    def _handle_signal(sig, frame):
        loop.call_soon_threadsafe(lambda: asyncio.create_task(runner.shutdown()))

    # Create and set a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Register signal handlers (in main thread)
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        # Run the metagraph
        loop.run_until_complete(runner.start())

    except Exception as e:
        btul.logging.error(f"Unhandled exception: {e}")
        btul.logging.debug(traceback.format_exc())

    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
