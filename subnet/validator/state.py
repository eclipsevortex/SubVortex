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

# Utils for checkpointing and saving the model.
import os
import re
import torch
import copy
import wandb
from wandb.apis import public
import shutil
import bittensor as bt
from datetime import datetime
from typing import List

from subnet import __spec_version__ as THIS_SPEC_VERSION
from subnet import __version__ as THIS_VERSION
import subnet.validator as validator



def should_checkpoint(current_block, prev_step_block, checkpoint_block_length):
    # Check if enough epoch blocks have elapsed since the last checkpoint.
    return current_block - prev_step_block >= checkpoint_block_length


def checkpoint(self):
    """Checkpoints the training process."""
    bt.logging.info("checkpoint()")
    resync_metagraph(self)
    save_state(self)


def resync_metagraph(self: "validator.neuron.neuron"):
    """Resyncs the metagraph and updates the hotkeys and moving averages based on the new metagraph."""
    bt.logging.info("resync_metagraph()")

    # Copies state of metagraph before syncing.
    previous_metagraph = copy.deepcopy(self.metagraph)

    # Sync the metagraph.
    self.metagraph.sync(subtensor=self.subtensor)

    # Check if the metagraph axon info has changed.
    metagraph_axon_info_updated = previous_metagraph.axons != self.metagraph.axons
    bt.logging.debug(f"metagraph_axon_info_updated: {metagraph_axon_info_updated}")

    if metagraph_axon_info_updated:
        bt.logging.info(
            "resync_metagraph() Metagraph updated, re-syncing moving averages"
        )

        # Zero out all hotkeys that have been replaced.
        for uid, hotkey in enumerate(previous_metagraph.hotkeys):
            if hotkey != self.metagraph.hotkeys[uid]:
                bt.logging.debug(
                    f"resync_metagraph() old hotkey {hotkey} | uid {uid} has been replaced by {self.metagraph.hotkeys[uid]}"
                )
                self.moving_averaged_scores[uid] = 0  # hotkey has been replaced

        # Check to see if the metagraph has changed size.
        # If so, we need to add new hotkeys and moving averages.
        if len(self.moving_averaged_scores) < len(self.metagraph.hotkeys):
            bt.logging.info(
                "resync_metagraph() Metagraph has grown, adding new hotkeys and moving averages"
            )
            # Update the size of the moving average scores.
            new_moving_average = torch.zeros((self.metagraph.n)).to(self.device)
            min_len = min(len(self.metagraph.hotkeys), len(self.moving_averaged_scores))
            new_moving_average[:min_len] = self.moving_averaged_scores[:min_len]
            self.moving_averaged_scores = new_moving_average


def save_state(self):
    r"""Save hotkeys, neuron model and moving average scores to filesystem."""
    bt.logging.info("save_state()")
    try:
        neuron_state_dict = {
            "neuron_weights": self.moving_averaged_scores.to("cpu").tolist(),
            "last_purged_epoch": self.last_purged_epoch,
        }
        torch.save(neuron_state_dict, f"{self.config.neuron.full_path}/model.torch")
        bt.logging.success(
            prefix="Saved model",
            sufix=f"<blue>{ self.config.neuron.full_path }/model.torch</blue>",
        )
    except Exception as e:
        bt.logging.warning(f"Failed to save model with error: {e}")

    # empty cache
    torch.cuda.empty_cache()


def load_state(self):
    r"""Load hotkeys and moving average scores from filesystem."""
    bt.logging.info("load_state()")
    try:
        state_dict = torch.load(f"{self.config.neuron.full_path}/model.torch")
        neuron_weights = torch.tensor(state_dict["neuron_weights"])
        self.last_purged_epoch = state_dict.get("last_purged_epoch", 0)
        bt.logging.info(f"Loaded last_purged_epoch: {self.last_purged_epoch}")
        # Check to ensure that the size of the neruon weights matches the metagraph size.
        if neuron_weights.shape != (self.metagraph.n,):
            bt.logging.warning(
                f"Neuron weights shape {neuron_weights.shape} does not match metagraph n {self.metagraph.n}"
                "Populating new moving_averaged_scores IDs with zeros"
            )
            self.moving_averaged_scores[: len(neuron_weights)] = neuron_weights.to(
                self.device
            )
        # Check for nans in saved state dict
        elif not torch.isnan(neuron_weights).any():
            self.moving_averaged_scores = neuron_weights.to(self.device)
        bt.logging.success(
            prefix="Reloaded model",
            sufix=f"<blue>{ self.config.neuron.full_path }/model.torch</blue>",
        )
    except Exception as e:
        bt.logging.warning(f"Failed to load model with error: {e}")


def log_miners_table(self, miners: List, commit=False):
    # Build the dataset
    # We convert any number into string to have a better style in wandb UI
    data = []
    for miner in miners:
        miner_uid = miner.get("uid")
        if miner_uid == -1:
            continue

        data.append(
            [
                str(miner_uid),
                str(miner.get("version")),
                str(miner.get("country")),
                str(miner.get("score")),
                str(miner.get("availability_score")),
                str(miner.get("latency_score")),
                str(miner.get("reliability_score")),
                str(miner.get("distribution_score")),
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

    self.wandb.log({"02. Miners/miners": miners}, commit=commit)
    bt.logging.trace(f"log_miners_table() {data} miners")


def log_distribution(self, miners: List, commit=False):
    # Build the data for the metric
    country_counts = {}
    for miner in miners:
        miner_uid = miner.get("uid")
        if miner_uid == "-1":
            continue

        miner_country = miner.get("country")
        country_counts[miner_country] = country_counts.get(miner_country, 0) + 1

    # Create the graph
    data = [[country, count] for country, count in country_counts.items()]
    table = wandb.Table(data=data, columns=["country", "count"])

    wandb.log(
        {
            "03. Distribution/distribution": wandb.plot.bar(
                table, "country", "count", title="Miners Distribution"
            )
        },
        commit=commit,
    )
    bt.logging.trace(f"log_distribution() {data} countries")


def log_score(self, name: str, uids: List[int], miners: List, commit=False):
    property_name = f"{name}_score" if name != "final" else "score"

    # Build the data for the metric
    data = {}
    for miner in miners:
        uid = miner.get("uid")
        if uid not in uids:
            continue

        data[str(uid)] = miner.get(property_name)

    # Create the graph
    self.wandb.log({f"04. Scores/{name}_score": data}, commit=commit)
    bt.logging.trace(f"log_score() {name} {len(data)} scores")


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
    self.wandb.log({"04. Scores/moving_averaged_score": data}, commit=commit)
    bt.logging.trace(f"log_moving_averaged_score() {len(data)} moving averaged scores")


def log_completion_times(self, uids: List[int], miners: List, commit=False):
    """
    Create a graph showing the time to process the challenge over time
    """
    # Build the data for the metric
    data = {}
    for miner in miners:
        uid = miner.get("uid")
        if uid not in uids:
            continue

        data[str(uid)] = miner.get("process_time") or 0

    # Create the graph
    self.wandb.log({"05. Miscellaneous/completion_times": data}, commit=commit)
    bt.logging.trace(f"log_completion_times() {len(data)} completion times")


def log_event(self, uids: List[int], miners: List, step_length, moving_averaged_scores):
    # Log the event to wandb
    if not self.config.wandb.off and self.wandb is not None:
        # Add overview metrics
        best_miner = max(miners, key=lambda item: item["score"])
        self.wandb.log(
            {"01. Overview/best_uid": str(best_miner.get("uid"))}, commit=False
        )
        self.wandb.log({"01. Overview/step_process_time": step_length}, commit=False)

        # Add the miner table
        log_miners_table(self, miners)

        # Add miners distribution
        log_distribution(self, miners)

        # Add scores
        log_score(self, "final", uids, miners)
        log_score(self, "availability", uids, miners)
        log_score(self, "latency", uids, miners)
        log_score(self, "reliability", uids, miners)
        log_score(self, "distribution", uids, miners)
        log_moving_averaged_score(self, uids, moving_averaged_scores)

        # Add miscellaneous
        log_completion_times(self, uids, miners, True)


def init_wandb(self, reinit=False):
    """Starts a new wandb run."""
    tags = [
        self.wallet.hotkey.ss58_address,
        THIS_VERSION,
        str(THIS_SPEC_VERSION),
        f"netuid_{self.metagraph.netuid}",
        self.country,
    ]

    if self.config.mock:
        tags.append("mock")
    if self.config.neuron.disable_set_weights:
        tags.append("disable_set_weights")
    if self.config.neuron.disable_log_rewards:
        tags.append("disable_log_rewards")

    wandb_config = {
        key: copy.deepcopy(self.config.get(key, None))
        for key in ("neuron", "reward", "netuid", "wandb")
    }
    wandb_config["neuron"].pop("full_path", None)

    # Ensure "subvortex-team" and "test-subvortex-team" are used with the right subnet UID
    # If user provide its own project name we keep it
    project_name = self.config.wandb.project_name
    if self.config.netuid == 7 and project_name.endswith("subvortex-team"):
        project_name = "subvortex-team"
    elif self.config.netuid == 92 and project_name.endswith("subvortex-team"):
        project_name = "test-subvortex-team"
    bt.logging.debug(
        f"Wandb project {project_name} used for Subnet {self.config.netuid}"
    )

    # Get the list of current runs for the validator
    # Rate limite for free accounts - 50 requests per minutes
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
    self.wandb = wandb.init(
        anonymous="allow",
        reinit=reinit,
        project=project_name,
        entity=self.config.wandb.entity,
        config=wandb_config,
        mode="offline" if self.config.wandb.offline else "online",
        dir=self.config.neuron.full_path,
        tags=tags,
        notes=self.config.wandb.notes,
        name=name,
    )

    bt.logging.debug(f"[Wandb] {len(runs)} run(s) exist")

    # Remove old runs - We keep only one archive + the new run
    if len(runs) >= 2:
        clean_wandb_old_runs(runs)

    bt.logging.success(
        prefix="Started a new wandb run",
        sufix=f"<blue> {self.wandb.name} </blue>",
    )


def reinit_wandb(self):
    """Reinitializes wandb, rolling over the run."""
    if self.wandb is not None:
        self.wandb.finish()
        assert self.wandb.run is None

    init_wandb(self, reinit=True)


def clean_wandb_old_runs(runs):
    try:
        bt.logging.debug(f"[Wandb] Removing the {len(runs) - 1} oldest run(s)")
        for i in range(1, len(runs)):
            run: public.Run = runs[i]

            # Remove remote run
            run.delete(True)
            bt.logging.debug(f"[Wandb] Run {run.name} removed remotely")

            # Remove local run
            wandb_base = wandb.run.settings.wandb_dir

            if run.metadata is None:
                pattern = r"run-\d{8}_\d{6}-" + re.escape(run.id)

                # re.match(run-\d{8}_\d{6}-6mh2vqw2,"/root/.bittensor/miners/validator/default/netuid92/subvortex_validator/wandb")

                # matches = re.match(pattern, wandb_base)
                matches = [
                    subdir
                    for subdir in os.listdir(wandb_base)
                    if re.match(pattern, subdir)
                ]
                if len(matches) == 0:
                    continue

                run_local_path = f"{wandb_base}{matches[0]}"
                bt.logging.debug("[Wandb] Local path computed")
            else:
                # Get the run started at time
                startedAt = run.metadata["startedAt"]

                # Parse input datetime string into a datetime object
                input_datetime = datetime.strptime(startedAt, "%Y-%m-%dT%H:%M:%S.%f")

                # Format the datetime object into the desired string format
                output_datetime_str = input_datetime.strftime("%Y%m%d_%H%M%S")

                # Local path to the run files
                run_local_path = f"{wandb_base}run-{output_datetime_str}-{run.id}"
                bt.logging.debug("[Wandb] Local path retrieve from metadata")

            # Remove local run
            if os.path.exists(run_local_path):
                shutil.rmtree(run_local_path)
                bt.logging.debug(
                    f"[Wandb] Run {run.name} removed locally {run_local_path}"
                )
            else:
                bt.logging.warning(
                    f"[Wandb] Run local directory {run_local_path} does not exist. Please check it has been removed."
                )

    except Exception as err:
        run_names = [run.name for un in range(1, len(runs))]
        bt.logging.warning(
            f"[Wandb] Could not remove the local runs {run_names}: {err}"
        )


def should_reinit_wandb(self):
    """Check if wandb run needs to be rolled over."""
    return (
        not self.config.wandb.off
        and self.step
        and self.step % self.config.wandb.run_step_length == 0
    )
