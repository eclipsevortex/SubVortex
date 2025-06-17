import typing
import random
import asyncio
from itertools import chain

import bittensor.core.async_subtensor as btcas
import bittensor.utils.btlogging as btul

import subvortex.core.identity as cci
import subvortex.core.model.neuron as cmn
import subvortex.core.model.challenge as cmc
import subvortex.validator.core.model.miner as cmm
import subvortex.validator.core.challenger.settings as ccs
import subvortex.validator.core.challenger.challenges as ccc
import subvortex.validator.core.challenger.model as ccm


async def execute_challenge(
    step_id: str,
    settings: ccs.Settings,
    subtensor: btcas.AsyncSubtensor,
    challengees: typing.List[cmn.Neuron],
    challengees_nodes: typing.Dict[str, typing.List[cci.Node]],
) -> typing.Tuple[typing.Dict[str, ccm.ChallengeResult], cmc.Challenge]:
    tasks = []

    # Get the nodes of all the challengees
    nodes = list(
        chain.from_iterable(
            [challengees_nodes.get(x.hotkey, cci.DEFAULT_NODE) for x in challengees]
        )
    )

    # Get all the unique chain of the nodes
    node_chains = list(set([x.get("chain") for x in nodes]))
    btul.logging.debug(f"# of chains: {len(node_chains)}", prefix=settings.logging_name)

    # Select the chain node to challenge
    node_chain_selected = random.choice(node_chains)
    btul.logging.debug(
        f"Chain selected: {node_chain_selected}", prefix=settings.logging_name
    )

    # Get all the node types of the selected chain
    node_types = list(
        set([x.get("type") for x in nodes if x.get("chain") == node_chain_selected])
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
        for hotkey, nodes in challengees_nodes.items()
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
        for challengee in challengees:
            challengee_nodes = list(nodes_selected.get(challengee.hotkey, []))
            for challengee_node in challengee_nodes:
                # Check if the node has less connection than the current iteration
                max_node_connection = max(
                    challengee_node.get("max-connection", 0),
                    settings.default_challenge_max_iteration,
                )

                if i >= max_node_connection:
                    # Reached the max connection for that node
                    continue

                # Create and execute the task
                task = asyncio.create_task(
                    execute_challenge(
                        settings=settings,
                        ip=challengee.ip,
                        port=challengee_node.get("port"),
                        challenge=challenge,
                    ),
                    name=f"{challengee.hotkey}-{challengee_node.id}",
                )

                # Add the task in the list
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
    result = _aggregate_results(nodes, done | pending)

    return result, challenge


def _aggregate_results(
    nodes: typing.List[cci.Node], tasks
) -> typing.Dict[str, typing.List[ccm.ChallengeResult]]:
    challenges_result: typing.Dict[str, typing.List[ccm.ChallengeResult]] = {}

    for task in tasks:
        # Get the task details
        task_details = task.get_name().split("-")

        # Get information
        hotkey = task_details[0]
        node_id = task_details[1]

        # Get the node
        node = next((x for x in nodes if x.id == node_id), None)
        if node is None:
            continue

        # Create a default challenge result for this node
        challenge_result = ccm.ChallengeResult.create_default(
            id=node.id,
            chain=node.chain,
            type=node.type,
            is_reliable=True,
        )

        # Increment the number of attempts
        challenge_result.challenge_attempts += 1

        if task.cancelled() or not task.done():
            continue

        # Get the challenge result
        task_result: ccm.TaskResult = task.result()

        # Will be true if at least one task is available
        challenge_result.is_available = task_result.is_available

        # Will be true if the task is reliable
        challenge_result.is_reliable = (
            task_result.is_available and task_result.is_reliable
        )

        # Increment the number of successes
        challenge_result.challenge_successes += int(challenge_result.is_reliable)

        # Join unique reason
        challenge_result.reason = (
            ",".join(
                set(filter(None, [challenge_result.reason, task_result.reason.strip()]))
            )
        ).strip()

        # Store the average process time (just the task's time for this single task result)
        challenge_result.avg_process_time = task_result.process_time

        # Append result to list for this hotkey
        challenges_result.setdefault(hotkey, []).append(challenge_result)

    # Post-process: fill in reason if it's still empty but some attempts failed
    for result_list in challenges_result.values():
        for result in result_list:
            if (
                result.reason == ""
                and result.challenge_attempts != result.challenge_successes
            ):
                result.reason = (
                    f"{result.challenge_attempts - result.challenge_successes} task(s) "
                    "have been cancelled or not completed"
                )

    return challenges_result
