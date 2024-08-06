import json
import time
import argparse
import subprocess
import bittensor as bt
from typing import List


def run_command(command, stdout=subprocess.DEVNULL):
    try:
        return subprocess.run(
            command,
            check=False,
            stdout=stdout,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        bt.logging.error(f"Error running command: {e}")
        return None


def check_pm2_process_status(process_name: str):
    try:
        # Get the details of all PM2 processes in JSON format
        result = run_command(command=["pm2", "jlist"], stdout=subprocess.PIPE)
        processes = json.loads(result.stdout)
        for process in processes:
            if process["name"] == process_name:
                return process["pm2_env"]["status"]
    except subprocess.CalledProcessError as e:
        bt.logging.error(f"Failed to get the process status: {e}")
        return None


def get_pm2_process_args(process_name: str):
    try:
        # Get the details of all PM2 processes in JSON format
        result = run_command(command=["pm2", "jlist"], stdout=subprocess.PIPE)
        processes = json.loads(result.stdout)

        # Find the process by name and extract the script args
        for process in processes:
            if process["name"] == process_name:
                pm2_env = process.get("pm2_env") or {}
                script_args = pm2_env.get("args", [])
                pm_exec_path = pm2_env.get("pm_exec_path", None)
                interpreter = process["pm2_env"].get("exec_interpreter", None)
                return (pm_exec_path, interpreter, script_args)

        return (None, None, None)
    except subprocess.CalledProcessError as e:
        bt.logging.error(f"Failed to get the process args: {e}")
        return (None, None, None)


def update_firewall_args(config, process_args: List[str]):
    updated_args = []
    i = 0

    while i < len(process_args):
        if process_args[i].startswith("--firewall."):
            if i + 1 < len(process_args) and not process_args[i + 1].startswith("--"):
                i += 2
            else:
                i += 1
        else:
            updated_args.append(process_args[i])
            i += 1

    updated_args = updated_args + [
        "--firewall.on",
        "--firewall.interface",
        config.firewall.interface,
        "--firewall.config",
        config.firewall.config,
    ]

    return updated_args


def restart_pm2_process(
    process_name: str,
    process_path: str,
    process_interpreter: str,
    process_args: List[str],
):
    # Remove the existing process
    run_command(["pm2", "delete", process_name])

    # Restart the process with new arguments
    run_command(
        [
            "pm2",
            "start",
            process_path,
            "--name",
            process_name,
            "--interpreter",
            process_interpreter,
            "--",
        ]
        + process_args
    )


def main(config):
    process_name = config.process.name

    bt.logging.debug(f"Updating process arguments")
    process_path, process_interpreter, process_args = get_pm2_process_args(process_name)
    process_args = update_firewall_args(config, process_args)

    bt.logging.debug(f"Restart miner")
    restart_pm2_process(
        process_name=process_name,
        process_path=process_path,
        process_interpreter=process_interpreter,
        process_args=process_args,
    )

    # Wait a few seconds to allow the process to restart
    waited = 0
    status = "unknown"
    while status not in ["online", "errored"]:
        status = check_pm2_process_status(process_name)
        time.sleep(1)
        waited += 1

        if waited > 10:
            break

    if status == "online":
        bt.logging.success("Firewall has been activated")
    else:
        bt.logging.warning("Firewall could not restart correctly")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.logging.add_args(parser)
        parser.add_argument(
            "--process.name", type=str, help="Name of the miner in pm2", default=None
        )
        parser.add_argument(
            "--firewall.interface",
            type=str,
            help="Interface to listen the traffic to (default eth0)",
            default="eth0",
        )
        parser.add_argument(
            "--firewall.config",
            type=str,
            help="List of ports to forward but not to sniff",
            default="firewall.json",
        )
        parser.add_argument(
            "--sse.firewall.ip",
            type=str,
            required=False,
            help="Allowed Ip to subscribe to the firewall stream. It has to be the ip used to display the firewall UI",
            default=None,
        )

        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")
