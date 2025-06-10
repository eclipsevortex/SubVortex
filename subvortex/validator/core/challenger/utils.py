# The MIT License (MIT)
# Copyright © 2055 Eclipse Vortex

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
from collections import Counter
from typing import List, Dict

import subvortex.core.model.neuron as scmn
import subvortex.validator.core.model.miner as scmm
import subvortex.validator.core.challenger.settings as sccs


def apply_sma(
    settings: sccs.Settings,
    scores: list,
    score: int | float,
    default_score: int | float,
):
    if settings.challenge_period <= 1:
        return [score]

    padded = [default_score] * max(
        0, settings.challenge_period - 1 - len(scores)
    ) + scores

    return padded[-settings.challenge_period + 1 :] + [score]


def extract_countries(challengees: List[scmm.Miner]) -> Dict[str, int]:
    """
    Returns a dictionary of countries and their counts from the given list of neurons.

    Args:
        neurons (List[Neuron]): The list of active neurons or miners.

    Returns:
        Dict[str, int]: A dictionary mapping country codes to the number of neurons from that country.
    """
    # Count non-empty country codes
    country_counter = Counter(x.country for x in challengees if x.country)

    # Log each country for debug purposes
    for country, count in country_counter.items():
        print(f"[extract_countries] {country}: {count}")

    return dict(country_counter)
