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
import torch
import copy
import wandb
from wandb.apis import public
import shutil
import bittensor as bt
from datetime import datetime
from dataclasses import asdict

from subnet import __spec_version__ as THIS_SPEC_VERSION
from subnet import __version__ as THIS_VERSION
import subnet.validator as validator
from subnet.validator.event import EventSchema


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


def log_miners_table(self, event: EventSchema, commit=False):
    # Build the dataset
    # We convert any number into string to have a better style in wandb UI
    data = []
    for idx, (uid) in enumerate(event.uids):
        data.append(
            [
                str(uid),
                "0.2.4",
                event.countries[idx],
                str(event.rewards[idx]),
                str(event.availability_scores[idx]),
                str(event.latency_scores[idx]),
                str(event.reliability_scores[idx]),
                str(event.distribution_scores[idx]),
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

    self.wandb.log({"02 Miners/miners": miners}, commit=commit)


def log_distribution(self, event: EventSchema, commit=False):
    # Build the data for the metric
    country_counts = {}
    for code in event.countries:
        country_counts[code] = country_counts.get(code, 0) + 1

    # Create the graph
    data = [[country, count] for country, count in country_counts.items()]
    table = wandb.Table(data=data, columns=["country", "count"])
    wandb.log(
        {
            "03 Distribution/distribution": wandb.plot.bar(
                table, "country", "count", title="Miners Distribution"
            )
        },
        commit=commit,
    )


def log_score(self, name: str, event: EventSchema, commit=False):
    property_name = f"{name}_scores" if name != "final" else "rewards"
    scores = getattr(event, property_name)

    # Build the data for the metric
    data = {}
    for idx, (score) in enumerate(scores):
        data[f"{event.uids[idx]}"] = score

    # Create the graph
    self.wandb.log({f"04 Scores/{name}_score": data}, commit=commit)


def log_moving_averaged_score(self, event: EventSchema, commit=False):
    '''
    Create a graph showing the moving score for each miner over time
    '''
    # Build the data for the metric
    data = {}
    for idx, (score) in enumerate(event.moving_averaged_scores):
        if self.metagraph.uids[idx] not in event.uids:
            continue

        data[f"{self.metagraph.uids[idx]}"] = score

    # Create the graph
    self.wandb.log({"04 Scores/moving_averaged_score": data}, commit=commit)


def log_completion_times(self, event: EventSchema, commit=False):
    '''
    Create a graph showing the time to process the challenge over time
    '''
    # Build the data for the metric
    data = {}
    for idx, (time) in enumerate(event.completion_times):
        data[f"{event.uids[idx]}"] = time

    # Create the graph
    self.wandb.log({"05 Miscellaneous/completion_times": data}, commit=commit)


def log_event(self, event: EventSchema):
    # Log the event to wandb
    if not self.config.wandb.off and self.wandb is not None:
        # Add overview metrics
        self.wandb.log({"01 Overview/best_uid": event.best_uid}, commit=False)
        self.wandb.log(
            {"01 Overview/step_process_time": event.step_length}, commit=False
        )

        # Add the miner table
        log_miners_table(self, event)

        # Add miners distribution
        log_distribution(self, event)

        # Add scores
        log_score(self, "final", event)
        log_score(self, "availability", event)
        log_score(self, "latency", event)
        log_score(self, "reliability", event)
        log_score(self, "distribution", event)
        log_moving_averaged_score(self, event)

        # Add miscellaneous
        log_completion_times(self, event, True)


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

    # Get the list of current runs for the validator
    api = wandb.Api()
    runs = api.runs(
        f"{self.config.wandb.entity}/{self.config.wandb.project_name}",
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
        project=self.config.wandb.project_name,
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
        bt.logging.debug(f"[Wandb] Removing the {len(runs) - 1} oldest run(s)")
        for i in range(1, len(runs)):
            run: public.Run = runs[i]

            wandb_base = wandb.run.settings.wandb_dir

            # Get the run started at time
            startedAt = run.metadata["startedAt"]

            # Parse input datetime string into a datetime object
            input_datetime = datetime.strptime(startedAt, "%Y-%m-%dT%H:%M:%S.%f")

            # Format the datetime object into the desired string format
            output_datetime_str = input_datetime.strftime("%Y%m%d_%H%M%S")

            # Local path to the run files
            run_local_path = f"{wandb_base}/run-{output_datetime_str}-{run.id}"

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

            # Remove remote run
            run.delete(True)
            bt.logging.debug(f"[Wandb] Run {run.name} removed remotely")

    bt.logging.success(
        prefix="Started a new wandb run",
        sufix=f"<blue> {self.wandb.name} </blue>",
    )


def reinit_wandb(self):
    """Reinitializes wandb, rolling over the run."""
    if self.wandb is not None:
        self.wandb.finish()
    init_wandb(self, reinit=True)


def should_reinit_wandb(self):
    """Check if wandb run needs to be rolled over."""
    return (
        not self.config.wandb.off
        and self.step
        and self.step % self.config.wandb.run_step_length == 0
    )
