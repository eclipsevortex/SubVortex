import json
import bittensor as bt
import socket
from typing import Any
from bittensor.extrinsics.serving import get_metadata
from substrateinterface import SubstrateInterface
from websocket import WebSocket, create_connection


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


def get_node_peer_id(ip: str, request_id: int):
    payload = {
        "jsonrpc": "2.0",
        "method": "system_localPeerId",
        "id": request_id,
    }

    # Send the request
    body = send_request(ip, payload)

    # Get the peer id
    return body.get("result")


def get_listen_addresses(ip: str, request_id: int):
    payload = {
        "jsonrpc": "2.0",
        "method": "system_localListenAddresses",
        "id": request_id,
    }

    # Send the request
    body = send_request(ip, payload)

    # Get the peer id
    return body.get("result")


def get_sync_state(ip: str, request_id: int):
    payload = {
        "jsonrpc": "2.0",
        "method": "system_syncState",
        "id": request_id,
    }

    # Send the request
    body = send_request(ip, payload)

    # Get the peer id
    return body.get("result")


def send_request(ip: str, payload):
    try:
        # Create a websocket connexion
        websocket: WebSocket = create_connection(
            f"ws://{ip}:9944",
            timeout=None,
            class_=WebSocket,
            redirect_limit=0,
            http_no_proxy=True,
        )

        # Send the request
        websocket.send(json.dumps(payload))

        # Receive the response
        response = websocket.recv()

        # Load the body in json format
        body = json.loads(response)

        return body
    except Exception as err:
        raise err
    finally:
        if websocket:
            websocket.close()

    return None




async def get_current_block(request_id: str, ip: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "chain_getHeader",
        "params": [None],
        "id": request_id,
    }

    websocket = None

    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the peer
        client_socket.connect((ip, 30333))
        
        # Send data to the peer
        client_socket.send(json.dumps(payload))
        
        # Receive a response from the peer
        response = client_socket.recv(1024)
        print(f"Received response from peer: {response.decode()}")

        # Close the connection
        client_socket.close()

        # # Create a websocket connexion
        websocket: WebSocket = create_connection(
            f"ws://{ip}:9944",
            timeout=None,
            class_=WebSocket,
            redirect_limit=0,
            http_no_proxy=True,
            header=['X-Route: MyRoute']
        )

        # # Check for any suspicious
        # suspicious = websocket.getheaders().get("server") is not None

        # # Send the request
        status = websocket.send(json.dumps(payload))
        # print(status)
        # print(websocket.handshake_response.headers)
        # print(websocket.headers)

        # # Receive the response
        # response = websocket.recv()

        # # Load the body in json format
        # body = json.loads(response)

        # # Get the block
        # block = int(body["result"]["number"], 16)

        return 10000, False
    except Exception as err:
        raise err
    finally:
        if websocket:
            websocket.close()