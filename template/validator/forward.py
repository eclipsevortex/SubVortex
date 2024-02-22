# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# TODO(developer): Set your name
# Copyright © 2023 <your name>

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

import bittensor as bt
import torch
import typing
import traceback
import asyncio

from template.protocol import Dummy, IsAlive, Key
from template.validator.reward import get_rewards, reward
from template.utils.uids import get_random_uids
from template.utils.key import create_seed, create_private_key, create_public_key
from template.utils.subtensor import Subtensor
from template.utils.miner import Miner

from template.utils.geolocalisation import get_localisation_details_of_ip

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

async def forward(self):
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self (:obj:`bittensor.neuron.Neuron`): The neuron object which contains all the necessary state for the validator.

    """
    # Select a bunch of miners to sent the challenge to
    # Selection is for now random
    available_axon_size = len(self.metagraph.axons) - 1 # Except mine
    miner_selection_size = min(available_axon_size, self.config.neuron.sample_size)
    miner_uids = await get_random_uids(self, k=miner_selection_size)

    subtensors = []
    for uid in miner_uids:
        bt.logging.info(f"Proceeding with uid #{uid}")
        
        # seed = create_seed(1, 1)

        # Create the validator's private key
        private_key, pem_private_key = create_private_key()
        self.private_key = pem_private_key

        # Create the validator's public key
        public_key, pem_public_key = create_public_key(private_key)
        self.public_key = pem_public_key

        # Send the validator's public key to the selected miners
        responses = self.dendrite.query(
            # Send the query to selected miner axons in the network.
            axons=[self.metagraph.axons[uid]],
            # Construct a dummy query. This simply contains a single integer.
            synapse=Key(validator_public_key=self.public_key),
            # All responses have the deserialize function called on them before returning.
            # You are encouraged to define your own deserialization function.
            deserialize=True,
        )

        # Get the miner's public key
        miner_public_key_str = responses[0]

        # Get the miner's pem publick key
        miner_public_key = serialization.load_pem_public_key(
            miner_public_key_str.encode('utf-8'),
            backend=default_backend()
        )

        # Encrypt the message
        message = "Romain Diegoni"
        encrypted_message = miner_public_key.encrypt(
            message.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Send challenge to the selected miners
        responses = self.dendrite.query(
            # Send the query to selected miner axons in the network.
            axons=[self.metagraph.axons[uid]],
            # Construct a dummy query. This simply contains a single integer.
            synapse=Dummy(task=1, dummy_input=encrypted_message.decode('latin-1')),
            # All responses have the deserialize function called on them before returning.
            # You are encouraged to define your own deserialization function.
            deserialize=True,
        )

        message, block, subtensor_ip = responses[0]

        # current_block = self.subtensor.get_current_block()
        # print(f"Current block {current_block}/{block}")

        miner_axon = self.metagraph.axons[uid]

        # if False and uid == 2:
        #     miner_subtensor2 = Subtensor()
        #     miner_subtensor2.ip = '82.0.238.236'
        #     miner_subtensor2.cold_key = miner_axon.coldkey
        #     miner_subtensor2.country = "US"
        #     miner_subtensor2.region = "California"
        #     miner_subtensor2.city = "Mountain View"
        #     miner_subtensor2.timezone = "Europe/London"
        #     subtensors.append(miner_subtensor2)

        # Update subtensors list
        miner_subtensor_index = next((i for i, obj in enumerate(subtensors) if obj.ip == subtensor_ip), None)
        if miner_subtensor_index == None:
            # Get some localisation details of the subtensor ip
            # country, region, city = get_localisation_details_of_ip(subtensor_ip)
            # print(f"Miner's subtensor ip {subtensor_ip} {country}/{region}/{city}")
                
            miner_subtensor = Subtensor()
            miner_subtensor.ip = subtensor_ip
            miner_subtensor.cold_key = miner_axon.coldkey
            miner_subtensor.country = "US"
            miner_subtensor.region = "California"
            miner_subtensor.city = "Mountain View"
            miner_subtensor.timezone = "America/Los_Angeles"
            subtensors.append(miner_subtensor)
        else:
            miner_subtensor = subtensors[miner_subtensor_index]

        # Create a new miner
        miner = Miner()
        miner.uid = uid
        miner.ip = miner_axon.ip
        miner.with_subtensor = miner_axon.ip == subtensor_ip

        # Add the miner
        miner_subtensor.miners.append(miner)

    # Adjust the scores based on responses from miners.
    rewards = get_rewards(self, miner_uids, subtensors)
    bt.logging.info(f"Scored responses: {rewards}")

    # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
    self.update_scores(rewards, miner_uids)
