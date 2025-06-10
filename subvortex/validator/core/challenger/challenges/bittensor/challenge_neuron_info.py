import json
import time
import random
import asyncio
import traceback
import websockets
from websockets.exceptions import (
    ConnectionClosed,
    InvalidURI,
    InvalidHandshake,
    WebSocketException,
)

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.model.challenge as cmc
import subvortex.validator.core.challenger.model as ccm
import subvortex.validator.core.challenger.constants as ccc
import subvortex.validator.core.challenger.settings as ccs


async def create_challenge(
    step_id: str, settings: ccs.Settings, node_type: str, **kargs
) -> cmc.Challenge:
    subtensor = kargs.get("subtensor")

    if node_type == "lite":
        return await _create_lite_challenge(
            step_id=step_id, Pforsettings=settings, subtensor=subtensor
        )
    else:
        btul.logging.warning(f"Node type {node_type} is not implemented")


async def execute_challenge(
    settings: ccs.Settings, ip: str, port: int, challenge: tuple
) -> ccm.TaskResult:
    # Unpacking challenge
    try:
        params, block_hash, value = challenge
    except ValueError as e:
        return (False, f"Invalid challenge format: {e}", settings.challenge_timeout)
    btul.logging.debug(f"Challenge {params} / {block_hash} / {value}")

    # Set IP/Port
    ws_url = (
        f"wss://{ip}:{port}"
        if ip == "archive.chain.opentensor.ai"
        else f"ws://{ip}:{port}"
    )
    btul.logging.debug(f"Challenging {ws_url}")

    # Set start time
    start_time = time.time()

    ws = None
    try:
        # Attempt to establish WebSocket connection
        ws = await websockets.connect(ws_url)
    except asyncio.TimeoutError:
        return ccm.TaskResult.create(reason="WebSocket connection timed out")
    except (InvalidURI, OSError):
        return ccm.TaskResult.create(reason=f"Invalid WebSocket URI: {ws_url}")
    except InvalidHandshake as e:
        return ccm.TaskResult.create(reason=f"WebSocket handshake failed: {e}")
    except WebSocketException as e:
        return ccm.TaskResult.create(reason=f"WebSocket error: {e}")

    # Prepare data payload
    data = json.dumps(
        {
            "id": "state_call0",
            "jsonrpc": "2.0",
            "method": "state_call",
            "params": [
                "NeuronInfoRuntimeApi_get_neuron_lite",
                params,
                block_hash,
            ],
        }
    )

    try:
        # Send request
        await ws.send(data)
    except ConnectionClosed as e:
        return ccm.TaskResult.create(
            reason=f"WebSocket closed before sending data: {e}"
        )

    try:
        # Receive response
        response = await ws.recv()
    except asyncio.TimeoutError:
        return ccm.TaskResult.create(reason=f"WebSocket receive timed out")
    except ConnectionClosed as e:
        return ccm.TaskResult.create(
            reason=f"WebSocket closed before receiving response: {e}"
        )

    # Calculate process time
    process_time = time.time() - start_time

    # Load the response
    try:
        response = json.loads(response)
    except json.JSONDecodeError:
        return ccm.TaskResult.create(
            is_available=True, reason=f"Received malformed JSON response"
        )

    # Validate response
    if "error" in response:
        return ccm.TaskResult.create(
            is_available=True,
            reason=f"Error in response: {response['error'].get('message', 'Unknown error')}",
        )

    if "result" not in response:
        return ccm.TaskResult.create(
            is_available=True,
            reason=f"Response does not contain a 'result' field",
        )

    if response["result"] != value:
        return ccm.TaskResult.create(
            is_available=True,
            reason="Received incorrect result",
            process_time=process_time,
        )

    # Ensure WebSocket is closed properly
    if ws:
        await ws.close()

    return ccm.TaskResult.create(
        is_available=True, is_reliable=True, process_time=process_time
    )


async def _create_lite_challenge(
    step_id: str, settings: ccs.Settings, subtensor: btcas.AsyncSubtensor
) -> cmc.Challenge:
    try:
        # Get the current block from the miner subtensor
        current_block = await subtensor.get_current_block()

        # Select a block between [current block - 256, current block - 10]
        block = random.randint(
            current_block - ccc.LITE_NODE_BLOCK_LOWER_LIMIT,
            current_block - ccc.LITE_NODE_BLOCK_UPPER_LIMIT,
        )
        btul.logging.debug(
            f"[Lite] Block chosen: {block}", prefix=settings.logging_name
        )

        # Get the hash of the choosen block
        block_hash = await subtensor.get_block_hash(block)
        btul.logging.debug(
            f"[Lite] Block hash chosen: {block_hash}", prefix=settings.logging_name
        )

        # Get the number of subnets
        subnet_count = await subtensor.get_total_subnets(block=block) - 1
        btul.logging.debug(
            f"[Lite] # of subnet: {subnet_count}", prefix=settings.logging_name
        )

        # Be sure we select a subnet that at least one neuron
        subnet_to_exclude = []
        subnet_uid = None
        neuron_count = 0
        while neuron_count == 0:
            if subnet_uid is not None:
                subnet_to_exclude.append(subnet_uid)

            # Select a subnet
            subnet_uid = random.choice(
                list(set(range(subnet_count + 1)) - set(subnet_to_exclude))
            )

            # Get the total number of neurons
            neuron_count = await subtensor.subnetwork_n(subnet_uid, block)

        # Select a neuron
        neuron_uid = random.randint(0, neuron_count - 1)

        # Get the runtime call definition
        runtime_call_def = _get_runtime_call_definition(
            substrate=subtensor.substrate,
            api="NeuronInfoRuntimeApi",
            method="get_neuron_lite",
        )

        # Encode the parameters
        params = _new_encode(
            substrate=subtensor.substrate,
            runtime_call_def=runtime_call_def,
            params=[subnet_uid, neuron_uid],
        )
        params = params.hex()

        # Send the RPC request
        response = await subtensor.substrate.rpc_request(
            "state_call",
            [f"NeuronInfoRuntimeApi_get_neuron_lite", params, block_hash],
        )

        # Get the value
        value = response.get("result")

        btul.logging.debug(
            f"[Lite] Challenge created - Block: {block}, Netuid: {subnet_uid}, Uid: {neuron_uid}",
            prefix=settings.logging_name,
        )

        return cmc.Challenge(
            step_id=step_id,
            params=params,
            block_hash=block_hash,
            value=value,
        )

    except Exception as err:
        btul.logging.warning(
            f"[Lite] Could not create the challenge: {err}",
            prefix=settings.logging_name,
        )
        btul.logging.warning(traceback.format_exc(), prefix=settings.logging_name)
        return None


def _get_runtime_call_definition(
    substrate: btcas.AsyncSubstrateInterface, api: str, method: str
):
    try:
        metadata_v15_value = substrate.runtime.metadata_v15.value()

        apis = {entry["name"]: entry for entry in metadata_v15_value["apis"]}
        api_entry = apis[api]
        methods = {entry["name"]: entry for entry in api_entry["methods"]}
        return methods[method]
    except KeyError:
        raise ValueError(f"Runtime API Call '{api}.{method}' not found in registry")


def _new_encode(substrate: btcas.AsyncSubstrateInterface, runtime_call_def, params={}):
    param_data = b""

    for idx, param in enumerate(runtime_call_def["inputs"]):
        param_type_string = f"scale_info::{param['ty']}"
        if isinstance(params, list):
            param_data += substrate._encode_scale(param_type_string, params[idx])
        else:
            if param["name"] not in params:
                raise ValueError(f"Runtime Call param '{param['name']}' is missing")

            param_data += substrate._encode_scale(
                param_type_string, params[param["name"]]
            )
    return param_data
