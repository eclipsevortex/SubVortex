import time
import typing
import asyncio
import paramiko
import bittensor as bt

from subnet import protocol
from subnet.shared.key import generate_key
from subnet.validator.ssh import check_connection
from subnet.validator.utils import get_available_query_miners


CHALLENGE_NAME = "Key"


async def handle_generation_synapse(
    self, uid: int, public_key: paramiko.RSAKey, private_key: paramiko.RSAKey
) -> typing.Tuple[bool]:
    # Get the axon
    axon = self.metagraph.axons[uid]

    bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Generating Ssh keys")

    # Send the public ssh key to the miner
    self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Key(generate=True, validator_public_key=public_key),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
        timeout=10,
    )

    # Check the ssh connection works
    verified = check_connection(axon.ip, private_key)
    if verified:
        bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Ssh connexion is verified")
    else:
        bt.logging.warning(f"[{CHALLENGE_NAME}][{uid}]  Ssh connexion is not verified")

    return verified


async def handle_cleaning_synapse(self, uid: int, public_key: paramiko.RSAKey):
    # Get the axon
    axon = self.metagraph.axons[uid]

    bt.logging.debug(f"[{CHALLENGE_NAME}][{uid}] Cleaning Ssh keys")

    # Send the public ssh key to the miner
    self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Key(generate=False, validator_public_key=public_key),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
        timeout=10,
    )

    # TODO: check the connection is not possible anymore


async def generate_ssh_keys(self):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Generate the ssh keys
    keys = []
    for uid in uids:
        public_key, private_key = generate_key(f"validator-{uid}")
        keys.append((public_key, private_key))
    bt.logging.debug(f"[{CHALLENGE_NAME}] Ssh keys generated")

    # Request the miners to create the ssh key
    tasks = []
    for idx, (uid) in enumerate(uids):
        (public_key, private_key) = keys[idx]
        tasks.append(
            asyncio.create_task(
                handle_generation_synapse(self, uid, public_key, private_key)
            )
        )
    await asyncio.gather(*tasks)

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    return keys


async def clean_ssh_keys(self, keys: list):
    start_time = time.time()
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[{CHALLENGE_NAME}] Available uids {uids}")

    # Request miners to remove the ssh key
    tasks = []
    for idx, (uid) in enumerate(uids):
        (public_key, private_key) = keys[idx]
        tasks.append(
            asyncio.create_task(handle_cleaning_synapse(self, uid, public_key))
        )
    await asyncio.gather(*tasks)

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[{CHALLENGE_NAME}] Step finished in {forward_time:.2f}s")

    return keys
