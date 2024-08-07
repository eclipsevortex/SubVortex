import bittensor as bt
from typing import Optional
from pydantic import (
    Field,
    field_validator,
)


class TerminalInfo(bt.TerminalInfo):
    # The bittensor version on the terminal as an int.
    neuron_version: Optional[int] = Field(
        title="neuron_version",
        description="The neuron version",
        examples=[111],
        default=None,
        frozen=False,
    )

    # Extract the bittensor version on the terminal as an int.
    _extract_version = field_validator("neuron_version", mode="before")(
        bt.synapse.cast_int
    )


class Synapse(bt.Synapse):
    dendrite: Optional[TerminalInfo] = Field(
        title="dendrite",
        description="Dendrite Terminal Information",
        examples=["TerminalInfo"],
        default=TerminalInfo(),
        frozen=False,
        repr=False,
    )
