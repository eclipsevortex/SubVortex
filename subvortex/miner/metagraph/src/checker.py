import asyncio
import argparse
import traceback
from dotenv import load_dotenv

import bittensor.utils.btlogging as btul
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.core.metagraph as btcm

import subvortex.core.core_bittensor.config.config_utils as scccu
import subvortex.core.metagraph.checker as scmc
import subvortex.core.metagraph.database as scmms

import subvortex.miner.metagraph.src.settings as smme

# Load the environment variables for the whole process
load_dotenv(override=True)


async def wait_for_database_connection(
    settings: smme.Settings, database: scmms.NeuronDatabase
) -> None:
    if settings.dry_run:
        return

    btul.logging.warning(
        "⏳ Waiting for Redis to become available...",
        prefix=settings.logging_name,
    )

    # Ensure the connection
    await database.ensure_connection()

    while True:
        if await database.is_connection_alive():
            btul.logging.info("✅ Connected to Redis.", prefix=settings.logging_name)
            return

        await asyncio.sleep(1)


async def main():
    parser = argparse.ArgumentParser()
    btul.logging.add_args(parser)
    btcas.AsyncSubtensor.add_args(parser)

    parser.add_argument(
        "--uid",
        type=int,
        help="Uid of the neuron to check",
        default=None,
    )

    parser.add_argument(
        "--with_country",
        action="store_true",
        help="True if you want to check the country too",
        default=False,
    )

    # Create the configuration
    config = btcc.Config(parser)

    # Create settings
    settings = smme.Settings.create()
    scccu.update_config(settings, config, parser)

    # Initialise logging
    btul.logging(config=config, debug=True)
    btul.logging.set_trace(config.logging.trace)
    btul.logging._stream_formatter.set_trace(config.logging.trace)

    subtensor = None
    try:
        # Create the storage
        database = scmms.NeuronDatabase(settings=settings)
        await wait_for_database_connection(settings=settings, database=database)

        # Initialize the subtensor
        subtensor = btcas.AsyncSubtensor(config=config)
        await subtensor.initialize()
        btul.logging.info(str(subtensor))

        settings.dry_run and btul.logging.info("Dry run mode enabled")

        # Initialize the metagraph
        # TODO: Tell OTF if I provide the subtensor the network will be finney even if the subtensor is in test!
        metagraph = btcm.AsyncMetagraph(
            netuid=settings.netuid, network=subtensor.network, sync=False
        )
        btul.logging.info(str(metagraph))

        # Create and run the metagraph observer
        checker = scmc.MetagraphChecker(
            settings=settings,
            subtensor=subtensor,
            metagraph=metagraph,
            database=database,
            with_country=config.with_country,
            uid=config.uid,
        )

        # Run the check
        await checker.run()

    except Exception as err:
        btul.logging.error("Error in training loop", str(err))
        btul.logging.debug(traceback.print_exception(type(err), err, err.__traceback__))

    except KeyboardInterrupt:
        btul.logging.info("Keyboard interrupt detected, exiting.")

    finally:
        if subtensor:
            await subtensor.close()


if __name__ == "__main__":
    asyncio.run(main())
