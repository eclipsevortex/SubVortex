import asyncio
import argparse
import traceback
from dotenv import load_dotenv

import bittensor.utils.btlogging as btul
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas
import bittensor.core.metagraph as btcm

import subvortex.core.core_bittensor.config.config_utils as scccu
import subvortex.core.challenger.challenger as sccc
import subvortex.core.challenger.database as sccd

import subvortex.validator.metagraph.src.settings as svme


# Load the environment variables for the whole process
load_dotenv(override=True)


async def wait_for_database_connection(
    settings: svme.Settings, database: sccd.NeuronDatabase
) -> None:
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

    # Create the configuration
    config = btcc.Config(parser)

    # Create settings
    settings = svme.Settings.create()
    scccu.update_config(settings, config, parser)

    # Initialise logging
    btul.logging(config=config, debug=True)
    btul.logging.set_trace(config.logging.trace)
    btul.logging._stream_formatter.set_trace(config.logging.trace)
    btul.logging.debug(str(config))

    # Display the settings
    btul.logging.info(f"metagraph settings: {settings}")

    database = None
    challenger = None
    subtensor = None
    try:
        # Create the storage
        database = sccd.ChallengerDatabase(settings=settings)
        await wait_for_database_connection(settings=settings, database=database)

        # Initialize the subtensor
        subtensor = btcas.AsyncSubtensor(config=config)
        await subtensor.initialize()
        btul.logging.info(str(subtensor))

        # Initialize the metagraph
        # TODO: Tell OTF if i provide the subtensor the network wil be finney even if the subtensor is in test!
        metagraph = btcm.AsyncMetagraph(
            netuid=settings.netuid, network=subtensor.network, sync=False
        )
        btul.logging.info(str(metagraph))

        # Create and run the metagraph observer
        challenger = sccc.Challenger(
            settings=settings,
            subtensor=subtensor,
            metagraph=metagraph,
            database=database,
        )
        await challenger.start()

    except Exception as err:
        btul.logging.error("Error in training loop", str(err))
        btul.logging.debug(traceback.print_exception(type(err), err, err.__traceback__))

    except KeyboardInterrupt:
        btul.logging.info("Keyboard interrupt detected, exiting.")

    finally:
        if database:
            await database.mark_as_unready()

        if challenger:
            await challenger.stop()

        if subtensor:
            await subtensor.close()


if __name__ == "__main__":
    asyncio.run(main())
