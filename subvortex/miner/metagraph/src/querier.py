import asyncio
import argparse
import traceback
from dotenv import load_dotenv

import bittensor.utils.btlogging as btul
import bittensor.core.config as btcc
import bittensor.core.async_subtensor as btcas

import subvortex.core.core_bittensor.config.config_utils as scccu
import subvortex.core.metagraph.database as scmms
import subvortex.core.metagraph.querier as scmq

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
        "--filter",
        action="append",
        default=[],
        help="Filter neurons by key=value (can use multiple times)",
    )
    parser.add_argument(
        "--fields",
        type=str,
        help="Comma-separated list of fields to display",
        default="",
    )
    parser.add_argument(
        "--sort",
        type=str,
        help="Sort neurons by a field. Use prefix '-' for descending, e.g., --sort=-stake",
        default=None,
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

    try:
        # Create the storage
        database = scmms.NeuronDatabase(settings=settings)
        await wait_for_database_connection(settings=settings, database=database)

        # Create and execute a querier
        querier = scmq.MetagraphQuerier(config=config, database=database)
        await querier.execute()

    except Exception as err:
        btul.logging.error("Error in training loop", str(err))
        btul.logging.debug(traceback.print_exception(type(err), err, err.__traceback__))

    except KeyboardInterrupt:
        btul.logging.info("Keyboard interrupt detected, exiting.")


if __name__ == "__main__":
    asyncio.run(main())
