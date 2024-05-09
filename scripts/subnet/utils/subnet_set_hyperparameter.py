import argparse
import bittensor as bt
from substrateinterface import KeypairType, Keypair


# def register_root(wallet: bt.wallet, subtensor: bt.subtensor):
#     with subtensor.substrate as substrate:
#         extrinsic_params = substrate.get_metadata_call_function("SubtensorModule", "root_register")
#         value_argument = extrinsic_params["fields"][len(extrinsic_params["fields"]) - 1]

#         # create extrinsic call
#         call = substrate.compose_call(
#             call_module="SubtensorModule",
#             call_function="root_register",
#             call_params={"netuid": config.netuid, str(value_argument["name"]): wallet.hotkey.ss58_address},
#         )
#         print(wallet)
#         extrinsic = substrate.create_signed_extrinsic(call=call, keypair=wallet.coldkey)
#         response = substrate.submit_extrinsic(
#             extrinsic, wait_for_inclusion=False, wait_for_finalization=True
#         )

#         # process if registration successful
#         response.process_events()
#         if not response.is_success:
#             bt.logging.error("Failed: error: {}".format(response.error_message))
#         else:
#             bt.logging.success(f"Hyper parameter extrinsic changed")
#         # value_argument = extrinsic_params["fields"][len(extrinsic_params["fields"]) - 1]
#         # substrate.query(module="SubtensorModule", storage_function="rootRegister")


# Network ID:        substrate
# Secret seed:       0xe5be9a5092b81bca64be81d212e7f2f9eba183bb7a90954f7b76361f6edb5c0a
# Public key (hex):  0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d
# Account ID:        0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d
# Public key (SS58): 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY
# SS58 Address:      5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY


def set_sudo(wallet: bt.wallet, subtensor: bt.subtensor):
    with subtensor.substrate as substrate:
        extrinsic_params = substrate.get_metadata_call_function("AdminUtils", extrinsic)
        value_argument = extrinsic_params["fields"][len(extrinsic_params["fields"]) - 1]


def get_alice(config, subtensor: bt.subtensor):
    with subtensor.substrate as substrate:
        authorities = substrate.query(module="Aura", storage_function="Authorities")

        seed = "0xe5be9a5092b81bca64be81d212e7f2f9eba183bb7a90954f7b76361f6edb5c0a"
        # seed="0xd217c8d065e5b3d7ec137c755368871cdc7b8d3b7b113fcab0e7082e675d587b"
        # 5GpAyhbCzaoUD1WmtAkceauVDjYS3ivikTAnGFRjLFpYSCRd
        result = bt.Keypair.create_from_seed(
            seed, ss58_format=42, crypto_type=KeypairType.SR25519
        )
        print(result.ss58_address)
        print(substrate.ss58_encode(seed, ss58_format=42))

        # bt.Keypair.create_from_uri

        # authorities = substrate.query(module="Aura", storage_function="Authorities")
        # print(authorities[0])
        # print(authorities[1])

        # wallet = bt.wallet(config=config, name="alice")
        # wallet.regenerate_coldkey(seed="0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d", use_password=False, overwrite=True)

        # return wallet


def set_min_burn(wallet: bt.wallet, subtensor: bt.subtensor, value: int):
    extrinsic = "sudo_set_min_burn"

    with subtensor.substrate as substrate:

        extrinsic_params = substrate.get_metadata_call_function("AdminUtils", extrinsic)
        value_argument = extrinsic_params["fields"][len(extrinsic_params["fields"]) - 1]

        # create extrinsic call
        call = substrate.compose_call(
            call_module="AdminUtils",
            call_function=extrinsic,
            call_params={"netuid": config.netuid, str(value_argument["name"]): value},
        )

        extrinsic = substrate.create_signed_extrinsic(
            call=call,
            keypair=wallet.coldkey,
        )

        response = substrate.submit_extrinsic(
            extrinsic, wait_for_inclusion=False, wait_for_finalization=True
        )

        # process if registration successful
        response.process_events()
        if not response.is_success:
            bt.logging.error("Failed: error: {}".format(response.error_message))
        else:
            bt.logging.success(f"sudo_set_min_burn set to {value}")


# TODO: Have to be a root
# TODO: create a key in keystore and make it sudo?
def set_max_allowed_uids(wallet: bt.wallet, subtensor: bt.subtensor, value: int):
    extrinsic = "sudo_set_max_allowed_uids"

    with subtensor.substrate as substrate:

        extrinsic_params = substrate.get_metadata_call_function("AdminUtils", extrinsic)
        value_argument = extrinsic_params["fields"][len(extrinsic_params["fields"]) - 1]

        # create extrinsic call
        call = substrate.compose_call(
            call_module="AdminUtils",
            call_function=extrinsic,
            call_params={"netuid": config.netuid, str(value_argument["name"]): value},
        )

        extrinsic = substrate.create_signed_extrinsic(
            call=call,
            keypair=wallet.coldkey,
            # signature="0x376184240232b05da7c7dd4a5de12404799d1b6f4b8174147db4fd73552aef40",
        )
        print(extrinsic)

        # Create signature payload
        nonce = subtensor.substrate.get_account_nonce(wallet.coldkey.ss58_address) or 0
        signature_payload = subtensor.substrate.generate_signature_payload(
            call=call, era="00", nonce=nonce, tip=0, tip_asset_id=None
        )
        print("Signature Payload", signature_payload)

        # Set Signature version to crypto type of keypair
        signature_version = wallet.coldkey.crypto_type
        print("Signature Version", signature_version)

        # Sign payload
        signature = wallet.coldkey.sign(signature_payload)
        print("Signature", signature)

        response = substrate.submit_extrinsic(
            extrinsic, wait_for_inclusion=False, wait_for_finalization=True
        )

        # 0xb83a14c340bb9b422e67d6908cee530d15a868240457330b4ed9881e6bfa244c6c631628c1e0c9898c20c60dcd9573bf40e5ab67ceb40ca6be4088530cc1ef88
        # 0xbd018400d43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d014ad8c910b4f08aebe17c8b7cf4ee177cd9865942671ef11c785dc5dcc3e2be5d8244ad8e36075f9c96c4e2b4884265d7cb257db3f10b4a312eee763c49fe1883d50224000c00120f01000500

        # process if registration successful
        response.process_events()
        if not response.is_success:
            bt.logging.error("Failed: error: {}".format(response.error_message))
        else:
            bt.logging.success(f"Hyper parameter extrinsic changed to {value}")


def get_max_allowed_uids(subtensor: bt.subtensor):
    subnet_info = subtensor.get_subnet_info(netuid=1)
    bt.logging.success(f"Max allowed uids {subnet_info.max_n}")


def main(_config):
    bt.logging.check_config(_config)
    bt.logging(config=_config, debug=True, trace=True)

    bt.logging.info("loading wallet")
    wallet = bt.wallet(config=config)
    bt.logging.info(wallet)

    bt.logging.info(f"loading subtensor")
    subtensor = bt.subtensor(config=config)

    wallet.coldkey

    # register_root(wallet, subtensor)

    # alice_wallet = get_alice(config, subtensor)
    # alice_wallet.coldkey
    set_max_allowed_uids(wallet, subtensor, 5)
    # get_max_allowed_uids(subtensor)

    # Old value 1
    # Works with owner wallet
    # set_min_burn(wallet, subtensor, 1)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.wallet.add_args(parser)
        bt.subtensor.add_args(parser)
        bt.logging.add_args(parser)
        parser.add_argument(
            "--netuid", type=int, help="Subvortex network netuid", default=7
        )
        config = bt.config(parser)

        main(config)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ValueError as e:
        print(f"ValueError: {e}")
