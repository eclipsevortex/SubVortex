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
import os
import re
import copy
import wandb
import shutil
import numpy as np
import bittensor.utils.btlogging as btul
from wandb.apis import public
from typing import List
from datetime import datetime

from subvortex.core.constants import TESTNET_SUBNET_UID, MAIN_SUBNET_UID

import subvortex.validator.core as validator
from subvortex.core.version import to_spec_version
from subvortex.validator.version import __version__ as THIS_VERSION
from subvortex.validator.core.models import Miner
from subvortex.validator.core.miner import resync_miners

THIS_SPEC_VERSION = to_spec_version(THIS_VERSION)


def should_checkpoint(current_block, prev_step_block, checkpoint_block_length):
    # Check if enough epoch blocks have elapsed since the last checkpoint.
    return current_block - prev_step_block >= checkpoint_block_length


async def resync_metagraph_and_miners(self, force_refresh=False):
    """Checkpoints the training process."""
    btul.logging.info("checkpoint()")
    resynched = resync_metagraph(self)

    if resynched or force_refresh:
        # Resync miners list
        await resync_miners(self)

        # Send refresh data to wandb for global graphs
        log_event(self, [miner.uid for miner in self.miners])

        # Save state
        save_state(self)


def resync_metagraph(self: "validator.neuron.neuron"):
    """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
    btul.logging.info("resync_metagraph()")

    # Copies state of metagraph before syncing.
    previous_metagraph = copy.deepcopy(self.metagraph)

    # Sync the metagraph.
    self.metagraph.sync(subtensor=self.subtensor)

    # Check if the metagraph axon info has changed.
    metagraph_axon_info_updated = previous_metagraph.axons != self.metagraph.axons
    btul.logging.debug(f"metagraph_axon_info_updated: {metagraph_axon_info_updated}")

    if not metagraph_axon_info_updated:
        return False

    btul.logging.info(
        "resync_metagraph() Metagraph updated, re-syncing moving averages"
    )

    # Zero out all hotkeys that have been replaced.
    for uid, hotkey in enumerate(previous_metagraph.hotkeys):
        if hotkey != self.metagraph.hotkeys[uid]:
            btul.logging.debug(
                f"resync_metagraph() old hotkey {hotkey} | uid {uid} has been replaced by {self.metagraph.hotkeys[uid]}"
            )
            self.moving_averaged_scores[uid] = 0  # hotkey has been replaced

    # Check to see if the metagraph has changed size.
    # If so, we need to add new hotkeys and moving averages.
    if len(self.moving_averaged_scores) < len(self.metagraph.hotkeys):
        btul.logging.info(
            "resync_metagraph() Metagraph has grown, adding new hotkeys and moving averages"
        )
        # Update the size of the moving average scores.
        new_moving_average = np.zeros((self.metagraph.n))
        min_len = min(len(self.metagraph.hotkeys), len(self.moving_averaged_scores))
        new_moving_average[:min_len] = self.moving_averaged_scores[:min_len]
        self.moving_averaged_scores = new_moving_average

    return True


def save_state(self):
    r"""Save hotkeys, neuron model and moving average scores to filesystem."""
    btul.logging.info("save_state()")
    try:
        neuron_state_dict = {
            "neuron_weights": self.moving_averaged_scores,
        }

        # Save the state using numpy's .npz format
        np.savez(f"{self.config.neuron.full_path}/model.npz", **neuron_state_dict)
        btul.logging.success(f"Saved model {self.config.neuron.full_path}/model.npz")
    except Exception as e:
        btul.logging.warning(f"Failed to save model with error: {e}")


def load_state(self):
    r"""Load hotkeys and moving average scores from filesystem."""
    btul.logging.info("load_state()")
    try:
        # Load state_dict from a .npz file
        state_file = f"{self.config.neuron.full_path}/model.npz"
        if not os.path.exists(state_file):
            raise FileNotFoundError(f"{state_file} does not exist.")

        state_dict = np.load(state_file)
        neuron_weights = state_dict["neuron_weights"]
 
        # Check to ensure that the size of the neruon weights matches the metagraph size.
        if neuron_weights.shape != (self.metagraph.n,):
            btul.logging.warning(
                f"Neuron weights shape {neuron_weights.shape} does not match metagraph n {self.metagraph.n}."
                " Populating new moving_averaged_scores IDs with zeros."
            )
            self.moving_averaged_scores[: len(neuron_weights)] = neuron_weights
        # Check for NaNs in saved state dict
        elif not np.isnan(neuron_weights).any():
            self.moving_averaged_scores = neuron_weights

        btul.logging.success(f"Reloaded model {self.config.neuron.full_path}/model.npz")
    except Exception as e:
        btul.logging.warning(f"Failed to load model with error: {e}")


def log_miners_table(self, miners: List[Miner], commit=False):
    # Build the dataset
    # We convert any number into string to have a better style in wandb UI
    data = []
    for miner in miners:
        miner_uid = miner.uid
        if miner_uid == -1:
            continue

        data.append(
            [
                miner_uid,
                miner.version,
                miner.country,
                miner.score,
                miner.availability_score,
                miner.latency_score,
                miner.reliability_score,
                miner.distribution_score,
            ]
        )

    # Create the graph
    miners = wandb.Table(
        columns=[
            "UID",
            "Version",
            "Country",
            "Score",
            "Availability",
            "Latency",
            "Reliability",
            "Distribution",
        ],
        data=data,
    )

    wandb.run.log({"02. Miners/miners": miners}, commit=commit)
    btul.logging.trace(f"log_miners_table() {len(data)} miners")


def log_distribution(miners: List[Miner], verified=True, commit=False):
    # Build the data for the metric
    country_counts = {}
    for miner in miners:
        if verified and (not miner.verified or miner.has_ip_conflicts):
            continue

        miner_country = miner.country
        country_counts[miner_country] = country_counts.get(miner_country, 0) + 1

    # Create the graph
    data = [[country, count] for country, count in country_counts.items()]
    table = wandb.Table(data=data, columns=["country", "count"])

    section = (
        "03. Distribution/verified_distribution"
        if verified
        else "03. Distribution/distribution"
    )
    wandb.log(
        {
            section: wandb.plot.bar(
                table,
                "country",
                "count",
                title=(
                    "Verified Miners Distribution"
                    if verified
                    else "Miners Distribution"
                ),
            )
        },
        commit=commit,
    )

    if verified:
        btul.logging.trace(f"log_distribution() {len(data)} verified countries")
    else:
        btul.logging.trace(f"log_distribution() {len(data)} countries")


def log_score(self, name: str, uids: List[int], miners: List[Miner], commit=False):
    property_name = f"{name}_score" if name != "final" else "score"

    # Build the data for the metric
    data = {}
    for miner in miners:
        uid = miner.uid
        if uid not in uids:
            continue

        data[str(uid)] = getattr(miner, property_name)

    # Create the graph
    wandb.run.log({f"04. Scores/{name}_score": data}, commit=commit)
    btul.logging.trace(f"log_score() {name} {len(data)} scores")


def log_moving_averaged_score(
    self, uids: List[int], moving_averaged_scores: List, commit=False
):
    """
    Create a graph showing the moving score for each miner over time
    """
    metagraph_uids = self.metagraph.uids.tolist()

    # Build the data for the metric
    data = {}
    for idx, (score) in enumerate(moving_averaged_scores):
        uid = metagraph_uids[idx]
        if uid not in uids:
            continue

        data[str(uid)] = score

    # Create the graph
    wandb.run.log({"04. Scores/moving_averaged_score": data}, commit=commit)
    btul.logging.trace(
        f"log_moving_averaged_score() {len(data)} moving averaged scores"
    )


def log_completion_times(self, uids: List[int], miners: List[Miner], commit=False):
    """
    Create a graph showing the time to process the challenge over time
    """
    # Build the data for the metric
    data = {}
    for miner in miners:
        uid = miner.uid
        if uid not in uids:
            continue

        data[str(uid)] = miner.process_time or 0

    # Create the graph
    wandb.run.log({"05. Miscellaneous/completion_times": data}, commit=commit)
    btul.logging.trace(f"log_completion_times() {len(data)} completion times")


def log_event(self, uids: List[int], step_length=None):
    if self.config.wandb.off or wandb.run is None:
        return

    btul.logging.info("log_event()")

    try:
        miners: List[Miner] = self.miners
        moving_averaged_scores = self.moving_averaged_scores.tolist()

        # Add overview metrics
        best_miner = max(miners, key=lambda item: item.score)
        wandb.run.log({"01. Overview/best_uid": best_miner.uid}, commit=False)
        if step_length:
            wandb.run.log({"01. Overview/step_process_time": step_length}, commit=False)

        # Add the miner table
        log_miners_table(self, miners)

        # Add miners distribution
        log_distribution(miners)
        log_distribution(miners, False)

        # Add scores
        log_score(self, "final", uids, miners)
        log_score(self, "availability", uids, miners)
        log_score(self, "latency", uids, miners)
        log_score(self, "reliability", uids, miners)
        log_score(self, "distribution", uids, miners)
        log_moving_averaged_score(self, uids, moving_averaged_scores)

        # Add miscellaneous
        log_completion_times(self, uids, miners, True)
    except Exception as err:
        btul.logging.warning(f"log_event() send data to wandb failed: {err}")


def init_wandb(self):
    """Starts a new wandb run."""
    try:
        tags = [
            self.wallet.hotkey.ss58_address,
            THIS_VERSION,
            str(THIS_SPEC_VERSION),
            f"netuid_{self.metagraph.netuid}",
            self.country_code,
        ]

        if self.config.mock:
            tags.append("mock")
        if self.config.neuron.disable_set_weights:
            tags.append("disable_set_weights")

        wandb_config = {
            key: copy.deepcopy(self.config.get(key, None))
            for key in ("neuron", "reward", "netuid", "wandb")
        }
        wandb_config["neuron"].pop("full_path", None)

        # Ensure "subvortex-team" and "test-subvortex-team" are used with the right subnet UID
        # If user provide its own project name we keep it
        project_name = self.config.wandb.project_name
        if self.config.netuid == MAIN_SUBNET_UID and project_name.endswith(
            "subvortex-team"
        ):
            project_name = "subvortex-team"
        elif self.config.netuid == TESTNET_SUBNET_UID and project_name.endswith(
            "subvortex-team"
        ):
            project_name = "test-subvortex-team"
        btul.logging.debug(
            f"Wandb project {project_name} used for Subnet {self.config.netuid}"
        )

        # Get the list of current runs for the validator
        api = wandb.Api()
        runs = api.runs(
            f"{self.config.wandb.entity}/{project_name}",
            order="-created_at",
            filters={"display_name": {"$regex": f"^validator-{self.uid}"}},
        )

        name = f"validator-{self.uid}-1"
        if len(runs) > 0:
            # Take the first run as it will be the most recent one
            last_number = runs[0].name.split("-")[-1]
            next_number = (int(last_number) % 10000) + 1
            name = f"validator-{self.uid}-{next_number}"

        # Create a new run
        wandb.init(
            anonymous="allow",
            reinit=True,
            project=project_name,
            entity=self.config.wandb.entity,
            config=wandb_config,
            mode="offline" if self.config.wandb.offline else "online",
            dir=self.config.neuron.full_path,
            tags=tags,
            name=name,
        )

        btul.logging.debug(f"[Wandb] {len(runs)} run(s) exist")

        # Remove old runs - We keep only the new run
        if len(runs) >= 1:
            btul.logging.debug(f"[Wandb] Removing the {len(runs)} oldest run(s)")
            for i in range(0, len(runs)):
                run: public.Run = runs[i]

                # Remove remote run
                run.delete(True)
                btul.logging.debug(f"[Wandb] Run {run.name} removed remotely")

                # Remove local run
                wandb_base = wandb.run.settings.wandb_dir

                if run.metadata is None:
                    pattern = r"run-\d{8}_\d{6}-" + re.escape(run.id)

                    # matches = re.match(pattern, wandb_base)
                    matches = [
                        subdir
                        for subdir in os.listdir(wandb_base)
                        if re.match(pattern, subdir)
                    ]
                    if len(matches) == 0:
                        continue

                    run_local_path = f"{wandb_base}{matches[0]}"
                    btul.logging.debug("[Wandb] Local path computed")
                else:
                    # Get the run started at time
                    startedAt = run.metadata["startedAt"]

                    # Parse input datetime string into a datetime object
                    input_datetime = datetime.strptime(
                        startedAt, "%Y-%m-%dT%H:%M:%S.%f"
                    )

                    # Format the datetime object into the desired string format
                    output_datetime_str = input_datetime.strftime("%Y%m%d_%H%M%S")

                    # Local path to the run files
                    run_local_path = f"{wandb_base}run-{output_datetime_str}-{run.id}"
                    btul.logging.debug("[Wandb] Local path retrieve from metadata")

                # Remove local run
                if os.path.exists(run_local_path):
                    shutil.rmtree(run_local_path)
                    btul.logging.debug(
                        f"[Wandb] Run {run.name} removed locally {run_local_path}"
                    )
                else:
                    btul.logging.warning(
                        f"[Wandb] Run local directory {run_local_path} does not exist. Please check it has been removed."
                    )

        btul.logging.success(
            prefix="Started a new wandb run",
            suffix=f"<blue> {wandb.run.name} </blue>",
        )
    except Exception as err:
        btul.logging.warning(f"init_wandb() initialising wandb failed: {err}")


def should_reinit_wandb(self):
    """Check if wandb run needs to be rolled over."""
    return (
        not self.config.wandb.off
        and self.step
        and self.step % self.config.wandb.run_step_length == 0
    )


def finish_wandb():
    """
    Finish the current wandb run
    """
    try:
        btul.logging.debug("Finishing wandb run")
        wandb.finish()
        assert wandb.run is None
    except Exception as err:
        btul.logging.warning(f"finish_wandb() finishing wandb failed: {err}")
