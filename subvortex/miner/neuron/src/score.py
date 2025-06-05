import os
import json
import bittensor.utils.btlogging as btul

from subvortex.core.protocol import Score as PScore
from subvortex.miner.neuron.src.settings import Settings
from subvortex.miner.neuron.src.database import Database
from subvortex.miner.neuron.src.models.score import Score


async def save_scores(
    settings: Settings, database: Database, synapse: PScore, path: str
):
    if not settings.score_saving_enabled:
        return

    data = {
        "vuid": synapse.validator_uid,
        "block": synapse.block,
        "rank": synapse.rank,
        "availability_score": synapse.availability,
        "latency_score": synapse.latency,
        "reliability_score": synapse.reliability,
        "distribution_score": synapse.distribution,
        "score": synapse.score,
        "moving_score": synapse.moving_score,
        "penalty_factor": synapse.penalty_factor or -1,
    }

    try:
        if settings.score_saving_target == "json":
            scores_path = f"{settings.score_saving_json_path or path}/scores.json"

            # Load existing scores
            if os.path.exists(scores_path):
                try:
                    with open(scores_path, "r") as f:
                        scores = json.load(f)
                        if not isinstance(scores, list):
                            btul.logging.warning(
                                "scores.json is not a list. Resetting."
                            )
                            scores = []
                except json.JSONDecodeError:
                    btul.logging.warning("scores.json is invalid. Resetting.")
                    scores = []
            else:
                scores = []

            # Append new score and trim to 100 most recent by block
            scores.append(data)
            scores = sorted(scores, key=lambda x: x.get("block", 0), reverse=True)[
                : settings.score_max_entries
            ]

            with open(scores_path, "w") as f:
                json.dump(scores, f, indent=2)

        elif settings.score_saving_target == "redis":
            # Create the new score
            scores = Score.from_dict(data)

            # Save the new score
            await database.save_scores(scores)

            # Prune the old scores
            await database.prune_scores(max_entries=settings.score_max_entries)
            
    except Exception as e:
        btul.logging.error(f"Failed to save score: {e}")
