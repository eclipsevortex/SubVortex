import typing
import random
import asyncio
from itertools import chain

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.identity as cci
import subvortex.core.model.challenge as cmc
import subvortex.validator.core.model.miner as cmm
import subvortex.validator.core.challenger.settings as ccs
import subvortex.validator.core.challenger.challenges as ccc
import subvortex.validator.core.challenger.model as ccm


async def execute_challenge(
    step_id: str,
    settings: ccs.Settings,
    subtensor: btcas.AsyncSubtensor,
    challengers: typing.List[cmm.Miner],
    nodes: typing.Dict[str, typing.List],
) -> typing.Tuple[typing.Dict[str, ccm.ChallengeResult], cmc.Challenge]:
    tasks = []

    # Get the nodes of all the challengers
    challengers_nodes = list(
        chain.from_iterable(
            [nodes.get(x.hotkey, cci.DEFAULT_NODE) for x in challengers]
        )
    )

    # Get all the unique chain of the nodes
    node_chains = list(set([x.get("chain") for x in challengers_nodes]))
    btul.logging.debug(f"# of chains: {len(node_chains)}", prefix=settings.logging_name)

    # Select the chain node to challenge
    node_chain_selected = random.choice(node_chains)
    btul.logging.debug(
        f"Chain selected: {node_chain_selected}", prefix=settings.logging_name
    )

    # Get all the unique chain of the nodes
    node_types = list(
        set(
            [
                x.get("type")
                for x in challengers_nodes
                if x.get("chain") == node_chain_selected
            ]
        )
    )
    btul.logging.debug(
        f"# of chain types: {len(node_types)}", prefix=settings.logging_name
    )

    # Select the type node to challenge
    # TODO: once we have added the type the schedule, take it instead of taking randomly!
    node_type_selected = random.choice(node_types)
    btul.logging.debug(
        f"Chain type: {node_type_selected}", prefix=settings.logging_name
    )

    # List of nodes of the selected chains
    nodes_selected = {
        hotkey: [
            node
            for node in nodes
            if node["chain"] == node_chain_selected
            and node["type"] == node_type_selected
        ]
        for hotkey, nodes in nodes.items()
        if any(node["chain"] == node_chain_selected for node in nodes)
    }
    btul.logging.debug(f"Node selected: {nodes_selected}", prefix=settings.logging_name)

    # Get the max connections across all the nodes selected
    max_connection = max(
        [
            node.get("max-connection", 0)
            for node_list in nodes_selected.values()
            for node in node_list
        ]
        + [settings.default_challenge_max_iteration]
    )
    btul.logging.debug(
        f"Max connection: {max_connection}", prefix=settings.logging_name
    )

    # Get the list of available challenges for the chain
    chain_challenges = ccc.CHALLENGES.get(node_chain_selected)

    # Choose a challenge randomly
    create_challenge, execute_challenge = random.choice(chain_challenges)

    # Create the challenge
    btul.logging.info(f"Creating challenge", prefix=settings.logging_name)
    challenge = await create_challenge(
        step_id=step_id,
        settings=settings,
        node_type=node_type_selected,
        subtensor=subtensor,
    )
    btul.logging.debug(f"Challenge created: {challenge}", prefix=settings.logging_name)

    btul.logging.info(f"Executing challenge", prefix=settings.logging_name)
    for i in range(max_connection):
        for challenger in challengers:
            challenger_nodes = list(nodes_selected.get(challenger.hotkey, []))
            for node in challenger_nodes:
                # Check if the node has less connection than the current iteration
                max_node_connection = max(
                    node.get("max-connection", 0),
                    settings.default_challenge_max_iteration,
                )

                if i >= max_node_connection:
                    # Reached the max connection for that node
                    continue

                task = asyncio.create_task(
                    execute_challenge(
                        settings=settings,
                        ip=challenger.ip,
                        port=node.get("port"),
                        challenge=challenge,
                    ),
                    name=f"{node.get('chain')}-{node.get('type')}-{challenger.hotkey}-{i + 1}",
                )
                tasks.append(task)

    # Wait until finished or timedout
    done, pending = (
        await asyncio.wait(tasks, timeout=settings.challenge_timeout)
        if len(tasks) > 0
        else (set(), set())
    )

    # Cancel any remaining tasks that didn't finished on time
    for task in pending:
        task.cancel()

    btul.logging.debug(f"Challente completed", prefix=settings.logging_name)

    # Build the result
    result = _aggregate_results(done | pending)

    return result, challenge


def _aggregate_results(tasks):
    challenges_result: typing.Dict[str, ccm.ChallengeResult] = {}

    for task in tasks:
        # Get the task details
        task_details = task.get_name().split("-")

        # Get the ip of the task
        chain = task_details[0]
        type = task_details[1]
        hotkey = task_details[2]

        # Get the challenge result
        challenge_result = challenges_result.get(hotkey)
        if challenge_result is None:
            challenge_result = challenges_result[hotkey] = (
                # Set is_reliable True because the node will be consider reliable if all its tasks are available/reliable
                ccm.ChallengeResult.create_default(
                    chain=chain,
                    type=type,
                    is_reliable=True,
                )
            )

        # Increment the number of attempts
        challenge_result.challenge_attempts += 1

        if task.cancelled() or not task.done():
            continue

        # Get the challenge result
        task_result: ccm.TaskResult = task.result()

        # Will be true if at least one task is available
        challenge_result.is_available |= task_result.is_available

        # Will be true if all tasks are reliable
        challenge_result.is_reliable &= (
            task_result.is_available and task_result.is_reliable
        )

        # Increment the number of successes
        challenge_result.challenge_successes += int(challenge_result.is_reliable)

        # Join unique reason
        challenge_result.reason = (
            ",".join(
                set(challenge_result.reason.split(",") + [task_result.reason.strip()])
            )
        ).strip()

        # Compute the average process time
        challenge_result.avg_process_time = (
            challenge_result.avg_process_time + task_result.process_time
        ) / 2

    for result in challenges_result.values():
        if (
            result.reason == ""
            and result.challenge_attempts != result.challenge_successes
        ):
            result.reason = f"{result.challenge_attempts - result.challenge_successes} task(s) have been cancelled or not completed"
            continue

    return challenges_result
