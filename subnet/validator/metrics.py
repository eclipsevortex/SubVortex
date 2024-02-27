import time
import json
import typing
import asyncio
import paramiko
import bittensor as bt

from subnet import protocol

from subnet.shared.key import generate_key

from subnet.validator.event import EventSchema
from subnet.validator.ssh import check_connection
from subnet.validator.utils import get_available_query_miners


def execute_speed_test(self, uid: int, private_key: paramiko.RSAKey):
    # Get the axon
    axon = self.metagraph.axons[uid]

    # Initialize the SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote server
        ssh.connect(axon.ip, username="root", pkey=private_key)
        bt.logging.debug(f"Ssh connection with {axon.ip}")

        # Execute a command on the remote server
        command_to_execute = "speedtest-cli --json"
        stdin, stdout, stderr = ssh.exec_command(command_to_execute)

        # Get the command output
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        # Check for errors in the stderr output
        if error:
            raise error

        return json.loads(output)
    except paramiko.AuthenticationException:
        bt.logging.error(
            f"[Metrics][{uid}] Authentication failed, please verify your credentials"
        )
    except paramiko.SSHException as e:
        bt.logging.error(f"[Metrics][{uid}] Ssh connection error: {e}")
    except Exception as e:
        bt.logging.error(f"[Metrics][{uid}] An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()


async def handle_generation_synapse(
    self, uid: int, public_key: paramiko.RSAKey, private_key: paramiko.RSAKey
) -> typing.Tuple[bool, protocol.Key]:
    # Get the axon
    axon = self.metagraph.axons[uid]

    # Send the public ssh key to the miner
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
    if verified:
        bt.logging.info(f"[Metrics][{uid}] Ssh connection with {axon.ip} verified")
    else:
        bt.logging.warning(f"[Metrics][{uid}] Ssh connection with {axon.ip} is not verified")

    return verified, response


async def handle_cleaning_synapse(
    self, uid: int, public_key: paramiko.RSAKey
) -> typing.Tuple[bool, protocol.Key]:
    # Get the axon
    axon = self.metagraph.axons[uid]

    # Send the public ssh key to the miner
    response = self.dendrite.query(
        # Send the query to selected miner axons in the network.
        axons=[axon],
        # Construct a dummy query. This simply contains a single integer.
        synapse=protocol.Key(generate=False, validator_public_key=public_key),
        # All responses have the deserialize function called on them before returning.
        # You are encouraged to define your own deserialization function.
        deserialize=True,
    )

    # TODO: check the connection is not possible anymore

    return True, response


async def metrics_data(self, event: EventSchema):
    start_time = time.time()
    bt.logging.debug(f"[Metrics] Starting")

    # Select the miners
    uids = await get_available_query_miners(self, k=10)
    bt.logging.debug(f"[Metrics] Available uids {uids}")

    # Generate the ssh keys
    keys = []
    for uid in uids:
        public_key, private_key = generate_key(f"validator-{uid}")
        keys.append((public_key, private_key))
    bt.logging.debug("[Metrics] Ssh keys generated")

    # Generate and send the ssh keys
    tasks = []
    responses = []
    for idx, (uid) in enumerate(uids):
        (public_key, private_key) = keys[idx]
        tasks.append(
            asyncio.create_task(
                handle_generation_synapse(self, uid, public_key, private_key)
            )
        )
    responses = await asyncio.gather(*tasks)

    # Execute the speedtest-cli to get some metrics
    for idx, (uid, (verified, response)) in enumerate(zip(uids, responses)):
        if not verified:
            event.country.append(None)
            event.region.append(None)
            event.city.append(None)
            event.download.append(0)
            event.upload.append(0)
            event.latency.append(0)
            continue

        # Get the ssh keys
        public_key, private_key = keys[idx]

        result = execute_speed_test(self, uid, private_key)
        if result is None:
            bt.logging.warning(f"[Metrics][{uid}] Speed test failed")
            event.country.append(None)
            event.region.append(None)
            event.city.append(None)
            event.download.append(0)
            event.upload.append(0)
            event.latency.append(0)
            continue

        # Bandwidth - measured in Mbps
        download = float(result.get("download")) / 1000000
        upload = float(result.get("upload")) / 1000000

        # Lantency - measured in milliseconds
        ping = float(result.get("ping"))

        # Geolocalisation
        server = result.get("server")
        name = str(server.get("name")).split(", ")
        country = server.get("country")
        region = name[1] if len(name) == 2 else None
        city = name[0]

        # Get the coldkey
        axon = self.metagraph.axons[idx]
        coldkey = axon.coldkey

        # Get the hotkey
        hotkey = self.metagraph.hotkeys[uid]

        # Get the subs hash
        subs_key = f"subs:{coldkey}:{hotkey}"

        # # Send data to the subvortex api
        # await self.api.send(
        #     {
        #         "type": "metric",
        #         "key": subs_key,
        #         "country": country,
        #         "region": region,
        #         "city": city,
        #         "download": download,
        #         "upload": upload,
        #         "latency": ping,
        #     }
        # )

        # Update event
        event.country.append(country)
        event.region.append(region)
        event.city.append(city)
        event.download.append(download)
        event.upload.append(upload)
        event.latency.append(ping)

        # Update geolocalisation
        await self.database.hset(subs_key, "country", str(country))
        await self.database.hset(subs_key, "region", str(region))
        await self.database.hset(subs_key, "city", str(city))
        await self.database.hset(subs_key, "timezone", f"{country}, {region}, {city}")

        # Update download
        avg_download = download
        legacy_download = await self.database.hget(subs_key, "download")
        if legacy_download is not None:
            avg_download = (float(legacy_download) + download) / 2

        await self.database.hset(subs_key, "download", avg_download)
        bt.logging.info(f"[Metrics][{uid}] Download {avg_download}")

        # Update upload
        avg_upload = upload
        legacy_upload = await self.database.hget(subs_key, "upload")
        if legacy_upload is not None:
            avg_upload = (float(legacy_upload) + avg_upload) / 2

        await self.database.hset(subs_key, "upload", avg_upload)
        bt.logging.info(f"[Metrics][{uid}] Upload {avg_upload}")

        # Update lantency
        avg_latency = ping
        legacy_latency = await self.database.hget(subs_key, "latency")
        if legacy_latency is not None:
            avg_latency = (float(legacy_latency) + ping) / 2

        await self.database.hset(subs_key, "latency", avg_latency)
        bt.logging.info(f"[Metrics][{uid}] Latency {avg_latency}")

    # Clean the ssh keys
    tasks = []
    for uid in uids:
        (public_key, private_key) = keys[idx]
        tasks.append(
            asyncio.create_task(handle_cleaning_synapse(self, uid, public_key))
        )
    await asyncio.gather(*tasks)

    # Display step time
    forward_time = time.time() - start_time
    bt.logging.debug(f"[Metrics] Step time {forward_time:.2f}s")

    return event
