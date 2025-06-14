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
import bittensor_wallet.wallet as btw
import bittensor_wallet.mock as btwm

import subvortex.core.version as scv
import subvortex.core.core_bittensor.config.config_utils as scccu
import subvortex.validator.core.challenger.challenger as svccc
import subvortex.validator.core.challenger.challenge_executor as svccce
import subvortex.validator.core.challenger.challenge_scorer as svcccs
import subvortex.validator.core.challenger.database as svccd
import subvortex.validator.core.challenger.settings as svccs

load_dotenv(override=True)

# An asyncio event to signal when shutdown is complete
shutdown_complete = asyncio.Event()


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
        settings = svccs.Settings.create()
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
            # Initialize the wallet
            wallet = (
                btwm.get_mock_wallet() if config.mock else btw.Wallet(config=config)
            )
            btul.logging.debug(f"wallet: {str(wallet)}")

            # Create the storage
            database = svccd.Database(settings=settings)
            await self.wait_for_database_connection(
                settings=settings, database=database
            )

            # Initialize the subtensor
            self.subtensor = btcas.AsyncSubtensor(config=config, retry_forever=True)
            await self.subtensor.initialize()
            btul.logging.info(str(self.subtensor))

            # Initialize the metagraph
            # TODO: Tell OTF if I provide the subtensor the network will be finney even if the subtensor is in test!
            metagraph = btcm.AsyncMetagraph(
                netuid=settings.netuid, network=self.subtensor.network, sync=False
            )
            btul.logging.info(str(metagraph))

            # Create the executor
            challenge_executor = svccce.ChallengeExecutor(
                settings=settings, subtensor=self.subtensor
            )

            # Create the scorer
            challenge_scorer = svcccs.ChallengeScorer(settings=settings)

            # Create and run the metagraph observer
            self.challenger = svccc.Challenger(
                hotkey=wallet.hotkey.ss58_address,
                settings=settings,
                subtensor=self.subtensor,
                database=database,
                executor=challenge_executor,
                scorer=challenge_scorer,
                instance=settings.instance,
            )
            await self.challenger.start()

        except Exception as e:
            btul.logging.error(f"Unhandled exception: {e}")
            btul.logging.debug(traceback.format_exc())

    async def shutdown(self):
        btul.logging.info("Shutting down...")

        if getattr(self, "challenger", None):
            await self.challenger.stop()

        if getattr(self, "subtensor", None):
            await self.subtensor.close()
            btul.logging.debug("Subtensor stopped")

        btul.logging.info("Shutting down completed")


async def main():
    # Initialize runner
    runner = Runner()

    # Get the current asyncio event loop
    loop = asyncio.get_running_loop()

    # Define a signal handler that schedules the shutdown coroutine
    def _signal_handler():
        # Schedule graceful shutdown without blocking the signal handler
        loop.create_task(_shutdown(runner))

    # Register signal handlers for SIGINT (Ctrl+C) and SIGTERM (kill command)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # Start the main service logic
    await runner.start()

    # Block here until shutdown is signaled and completed
    await shutdown_complete.wait()


async def _shutdown(runner: Runner):
    # Gracefully shut down the service
    await runner.shutdown()

    # Notify the main function that shutdown is complete
    shutdown_complete.set()


if __name__ == "__main__":
    try:
        # Start the main asyncio loop
        asyncio.run(main())

    except Exception as e:
        # Log any unexpected exceptions that bubble up
        btul.logging.error(f"Unhandled exception: {e}")
        btul.logging.debug(traceback.format_exc())
