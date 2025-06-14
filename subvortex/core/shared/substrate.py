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
import netaddr
import scalecodec
import bittensor.core.axon as btca
import bittensor.core.chain_data as btcc
import bittensor.core.subtensor as btcs
import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul
import bittensor.utils.balance as btub
import bittensor.utils as btu
from typing import List, Union, Any, Dict
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from substrateinterface import SubstrateInterface


def _get_weights_min_stake(substrate: SubstrateInterface, storage_function: str):
    weight_min_stake = None

    try:
        weight_min_stake = substrate.query(
            module="SubtensorModule", storage_function=storage_function, params=[]
        )
    except:
        pass

    return weight_min_stake


async def get_weights_min_stake_async(substrate: btcas.AsyncSubstrateInterface):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = await substrate.query(
        module="SubtensorModule", storage_function="StakeThreshold", params=[]
    )

    weight_min_stake = result.value if result is not None else 0

    # Convert Rao to Tao
    return int(float(weight_min_stake) * 10**-9)


async def get_owner_hotkey(substrate: btcas.AsyncSubstrateInterface, netuid: int):
    """
    Return the hotkey of the subnet owner
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = await substrate.query(
        module="SubtensorModule", storage_function="SubnetOwnerHotkey", params=[netuid]
    )

    return result.value


def get_weights_min_stake(substrate: btcas.AsyncSubstrateInterface):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = _get_weights_min_stake(substrate, "StakeThreshold")
    if result is None:
        result = _get_weights_min_stake(substrate, "WeightsMinStake")

    weight_min_stake = result.value if result is not None else 0
    btul.logging.debug(f"get_weights_min_stake() {weight_min_stake}")

    # Convert Rao to Tao
    return int(float(weight_min_stake) * 10**-9)


def encode_params(
    self,
    call_definition: List["btcs.ParamWithTypes"],
    params: Union[List[Any], Dict[str, Any]],
) -> str:
    """Returns a hex encoded string of the params using their types."""
    param_data = scalecodec.ScaleBytes(b"")

    for i, param in enumerate(call_definition["params"]):  # type: ignore
        scale_obj = self.substrate.create_scale_object(param["type"])
        if type(params) is list:
            param_data += scale_obj.encode(params[i])
        else:
            if param["name"] not in params:
                raise ValueError(f"Missing param {param['name']} in params dict.")

            param_data += scale_obj.encode(params[param["name"]])

    return param_data.to_hex()


# def from_vec_u8(cls, vec_u8: List[int]) -> "NeuronInfoLite":
#         """Returns a NeuronInfoLite object from a ``vec_u8``."""
#         if len(vec_u8) == 0:
#             return btcc.NeuronInfoLite.get_null_neuron()

#         decoded = from_scale_encoding(vec_u8, ChainDataType.NeuronInfoLite)
#         if decoded is None:
#             return btcc.NeuronInfoLite..get_null_neuron()

#         return btcc.NeuronInfoLite.fix_decoded_values(decoded)
