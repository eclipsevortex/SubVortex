import scalecodec
import bittensor as bt
from typing import List, Union, Any, Dict
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from substrateinterface import SubstrateInterface


def get_weights_min_stake(substrate: SubstrateInterface):
    """
    Return the minimum of TAO a validator need to have the set weight
    """
    weight_min_stake = substrate.query(
        module="SubtensorModule", storage_function="WeightsMinStake", params=[]
    )
    bt.logging.debug(f"get_weights_min_stake() {weight_min_stake}")

    # Convert Rao to Tao
    return int(float(weight_min_stake.value) * 10**-9)


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
    rpc_runtime_config.update_type_registry(bt.chain_data.custom_rpc_type_registry)

    obj = rpc_runtime_config.create_scale_object(return_type, as_scale_bytes)
    if obj.data.to_hex() == "0x0400":  # RPC returned None result
        return bt.NeuronInfoLite.get_null_neuron()

    hex_bytes_result = obj.decode()

    if hex_bytes_result.startswith("0x"):
        bytes_result = bytes.fromhex(hex_bytes_result[2:])
    else:
        bytes_result = bytes.fromhex(hex_bytes_result)

    return bt.NeuronInfoLite.from_vec_u8(bytes_result)


def encode_params(
    self,
    call_definition: List["ParamWithTypes"],
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
