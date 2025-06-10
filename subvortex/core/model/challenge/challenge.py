from typing import Any
from dataclasses import dataclass, fields


@dataclass
class Challenge:
    step_id: str
    params: Any
    block_hash: str
    value: Any
    process_time: float

    def __init__(
        self,
        step_id: str,
        params: Any,
        block_hash: str,
        value: Any,
        process_time: float = 0.0,
    ):
        self.step_id = step_id
        self.params = params
        self.block_hash = block_hash
        self.value = value
        self.process_time = process_time

    @property
    def id(self):
        return self.step_id

    @staticmethod
    def create(
        step_id: str,
        process_time: float,
        challenge: tuple | None,
    ):
        params, block_hash, value = challenge or (None, None, None)
        return Challenge(
            step_id=step_id,
            params=params,
            block_hash=block_hash,
            value=value,
            process_time=process_time,
        )

    @staticmethod
    def from_dict(mapping):
        """Converts a dictionary to a Challenge instance."""
        return Challenge(
            step_id=mapping["step_id"],
            params=mapping["params"],
            block_hash=mapping["block_hash"],
            value=mapping["value"],
            process_time=float(mapping["process_time"]),
        )

    def to_dict(self):
        """Converts a Challenge instance to a dictionary"""
        return {
            "step_id": self.step_id,
            "params": self.params or "",
            "block_hash": self.block_hash or "",
            "value": self.value or "",
            "process_time": self.process_time,
        }
