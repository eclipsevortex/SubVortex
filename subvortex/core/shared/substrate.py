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
import bittensor.utils.btlogging as btul
import bittensor.utils.balance as btub
import bittensor.utils as btu
from typing import List, Union, Any, Dict
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from substrateinterface import SubstrateInterface
from async_substrate_interface import AsyncSubstrateInterface


def _get_weights_min_stake(substrate: SubstrateInterface, storage_function: str):
    weight_min_stake = None

    try:
        weight_min_stake = substrate.query(
            module="SubtensorModule", storage_function=storage_function, params=[]
        )
    except:
        pass

    return weight_min_stake


async def get_weights_min_stake_async(substrate: AsyncSubstrateInterface):
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


async def get_owner_hotkey(substrate: AsyncSubstrateInterface, netuid: int):
    """
    Return the hotkey of the subnet owner
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = await substrate.query(
        module="SubtensorModule", storage_function="SubnetOwnerHotkey", params=[netuid]
    )

    return result.value


def get_weights_min_stake(substrate: SubstrateInterface):
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


async def get_weights_min_stake_async(substrate: AsyncSubstrateInterface):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    # WeightsMinStake has been renamed StakeThreshold
    result = weight_min_stake = await substrate.query(
        module="SubtensorModule", storage_function="StakeThreshold", params=[]
    )

    weight_min_stake = result.value if result is not None else 0
    btul.logging.debug(f"get_weights_min_stake() {weight_min_stake}")

    # Convert Rao to Tao
    return int(float(weight_min_stake) * 10**-9)


def get_neuron_for_uid_lite(
    substrate: SubstrateInterface, netuid: int, uid: int, block: int = None
):
    data = scalecodec.ScaleBytes(b"")

    scale_obj = substrate.create_scale_object("u16")
    data += scale_obj.encode(netuid)

    scale_obj = substrate.create_scale_object("u16")
    data += scale_obj.encode(uid)

    block_hash = substrate.get_block_hash(block)

    json_result = substrate.rpc_request(
        method="state_call",
        params=["NeuronInfoRuntimeApi_get_neuron_lite", data.to_hex(), block_hash],
    )

    if json_result is None:
        return None

    return_type = "Vec<u8>"

    as_scale_bytes = scalecodec.ScaleBytes(json_result["result"])  # type: ignore

    rpc_runtime_config = RuntimeConfiguration()
    rpc_runtime_config.update_type_registry(load_type_registry_preset("legacy"))
    rpc_runtime_config.update_type_registry(btcc.custom_rpc_type_registry)

    obj = rpc_runtime_config.create_scale_object(return_type, as_scale_bytes)
    if obj.data.to_hex() == "0x0400":  # RPC returned None result
        return btcc.NeuronInfoLite.get_null_neuron()

    # Decode the result
    hex_bytes_result = obj.decode()

    # Convert to bytes
    bytes_result = btu.hex_to_bytes(hex_bytes_result)

    # Get the neuron info lite
    item = btcc.neuron_info.bt_decode.NeuronInfoLite.decode(bytes_result)

    # Set neuron's details
    active = item.active
    axon_info = item.axon_info
    coldkey = btcc.decode_account_id(item.coldkey)
    consensus = item.consensus
    dividends = item.dividends
    emission = item.emission
    hotkey = btcc.decode_account_id(item.hotkey)
    incentive = item.incentive
    last_update = item.last_update
    netuid = item.netuid
    prometheus_info = item.prometheus_info
    pruning_score = item.pruning_score
    rank = item.rank
    stake_dict = btcc.process_stake_data(item.stake)
    stake = sum(stake_dict.values()) if stake_dict else btub.Balance(0)
    trust = item.trust
    uid = item.uid
    validator_permit = item.validator_permit
    validator_trust = item.validator_trust

    return btcc.NeuronInfoLite(
        active=active,
        axon_info=btca.AxonInfo(
            version=axon_info.version,
            ip=str(netaddr.IPAddress(axon_info.ip)),
            port=axon_info.port,
            ip_type=axon_info.ip_type,
            placeholder1=axon_info.placeholder1,
            placeholder2=axon_info.placeholder2,
            protocol=axon_info.protocol,
            hotkey=hotkey,
            coldkey=coldkey,
        ),
        coldkey=coldkey,
        consensus=btu.u16_normalized_float(consensus),
        dividends=btu.u16_normalized_float(dividends),
        emission=emission / 1e9,
        hotkey=hotkey,
        incentive=btu.u16_normalized_float(incentive),
        last_update=last_update,
        netuid=netuid,
        prometheus_info=btcc.PrometheusInfo(
            version=prometheus_info.version,
            ip=str(netaddr.IPAddress(prometheus_info.ip)),
            port=prometheus_info.port,
            ip_type=prometheus_info.ip_type,
            block=prometheus_info.block,
        ),
        pruning_score=pruning_score,
        rank=btu.u16_normalized_float(rank),
        stake_dict=stake_dict,
        stake=stake,
        total_stake=stake,
        trust=btu.u16_normalized_float(trust),
        uid=uid,
        validator_permit=validator_permit,
        validator_trust=btu.u16_normalized_float(validator_trust),
    )


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
