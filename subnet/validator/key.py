import sys
import time
import torch
import json
import paramiko
import typing
import asyncio
import bittensor as bt

from subnet import protocol
from subnet.shared.key import generate_key
from subnet.validator.utils import get_available_query_miners
from subnet.validator.ssh import check_connection


async def handle_synapse(self, uid: int) -> typing.Tuple[bool, protocol.Challenge]:
    # Generate the public key
    public_key, private_key = generate_key('validator')
    bt.logging.debug("keys generated")

    # Get the axon
    axon = self.metagraph.axons[uid]

    # Generate SSH key
    response = self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Key(generate=True, validator_public_key=public_key),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
    )

    # Check the ssh connection works
    verified = check_connection(axon.ip, private_key)
    bt.logging.debug("Ssh connection verified")

    # Execute something here

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(axon.ip, username='root', pkey=private_key)

    # Execute a command on the remote server
    command_to_execute = 'speedtest-cli --json'
    stdin, stdout, stderr = ssh.exec_command(command_to_execute)

    # Get the command output
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    # Print the output or error
    if error is None:
        subtensor_details = json.loads(output)

        

    # Clean SSH key
    response = self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Key(generate=False, validator_public_key=public_key),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
    )

    return verified, response


async def generate_key_data(self):
    start_time = time.time()

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"key uids {uids}")

    # Generate SSH key
    tasks = []
    responses = []
    for uid in uids:
        tasks.append(asyncio.create_task(handle_synapse(self, uid)))
    responses = await asyncio.gather(*tasks)

    # # Compute the rewards for the responses given the prompt.
    # rewards: torch.FloatTensor = torch.zeros(len(responses), dtype=torch.float32).to(
    #     self.device
    # )

    # remove_reward_idxs = []
    # for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
    #     # TODO: Check the result from miner equal the one the validator will get by requesting the subtensor itself
    #     success = True

    #     # Get the hotkey
    #     hotkey = self.metagraph.hotkeys[uid]

    #     # Update the challenge statistics
    #     # await update_statistics(
    #     #     ss58_address=hotkey,
    #     #     success=success,
    #     #     task_type="challenge",
    #     #     database=self.database,
    #     # )

    #     # # Apply reward for this challenge
    #     # tier_factor = await get_tier_factor(hotkey, self.database)
    #     # rewards[idx] = 1.0 * tier_factor

    # if len(responses) == 0:
    #     bt.logging.debug("Received zero hashes from miners, returning event early.")
    #     return

    # uids, responses = _filter_verified_responses(uids, responses)
    # bt.logging.debug(
    #     f"challenge_data() full rewards: {rewards} | uids {uids} | uids to remove {remove_reward_idxs}"
    # )

    # # bt.logging.trace("Applying challenge rewards")
    # # apply_reward_scores(
    # #     self,
    # #     uids=uids,
    # #     responses=responses,
    # #     rewards=rewards,
    # #     timeout=30,
    # # )


def _filter_verified_responses(uids, responses):
    not_none_responses = [
        (uid, response[0])
        for (uid, (verified, response)) in zip(uids, responses)
        if verified is not None
    ]

    if len(not_none_responses) == 0:
        return (), ()

    uids, responses = zip(*not_none_responses)
    return uids, responses




