import json
import time
import argparse
import subprocess
import bittensor as bt

from subnet.firewall.firewall_factory import create_firewall_tool


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


def restart_pm2_process(process_name: str):
    process_path, process_interpreter, process_args = get_pm2_process_args(process_name)
    if "--firewall.on" not in process_args:
        return

    process_args = [x for x in process_args if x not in ["--firewall.on"]]

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

    # Get the tool for the os
    tool = create_firewall_tool()

    # Change the policy to allow
    bt.logging.debug(f"Change the INPUT policy to allow by default")
    tool.create_allow_policy()

    # Flush the INPUT chain
    bt.logging.debug(f"Flush the INPUT chain")
    tool.flush_input_chain()

    bt.logging.debug(f"Restart miner")
    restart_pm2_process(process_name)

    # Wait a few seconds to allow the process to restart
    status = "unknown"
    while status not in ["online", "errored"]:
        status = check_pm2_process_status(process_name)
        time.sleep(1)

    if status == "online":
        bt.logging.success("Firewall has been deactivated")
    else:
        bt.logging.warning("Firewall could not restart correctly")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        bt.logging.add_args(parser)
        parser.add_argument(
            "--process.name", type=str, help="Name of the miner in pm2", default=None
        )

        config = bt.config(parser)
        bt.logging(config=config, debug=True)

        main(config)
    except KeyboardInterrupt:
        bt.logging.debug("KeyboardInterrupt")
    except ValueError as e:
        bt.logging.error(f"The configuration file is incorrect: {e}")
