from typing import Optional
from dataclasses import dataclass, fields


@dataclass
class Schedule:
    index: int
    instance: int
    cycle_start: int
    cycle_end: int
    block_start: int
    block_end: int
    country: str

    def __init__(
        self,
        index: int,
        instance: int,
        cycle_start: int,
        cycle_end: int,
        block_start: int,
        block_end: int,
        country: str,
    ):
        self.index = index
        self.instance = instance
        self.cycle_start = cycle_start
        self.cycle_end = cycle_end
        self.block_start = block_start
        self.block_end = block_end
        self.country = country

    @property
    def id(self):
        return (
            f"{self.cycle_start}-{self.cycle_end}-{self.block_start}-{self.block_end}"
        )

    @property
    def step_index(self):
        return self.index + 1

    @property
    def instance_index(self):
        return self.instance + 1

    @staticmethod
    def create(
        index: int,
        instance: int,
        cycle_start: int,
        cycle_end: int,
        block_start: int,
        block_end: int,
        country: str,
    ):
        return Schedule(
            index=index,
            instance=instance,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            block_start=block_start,
            block_end=block_end,
            country=country,
        )

    @staticmethod
    def from_dict(mapping):
        """Converts a dictionary to a Schedule instance."""
        return Schedule(
            index=int(mapping["index"]),
            instance=int(mapping["instance"] or 1),
            cycle_start=int(mapping["cycle_start"]),
            cycle_end=int(mapping["cycle_end"]),
            block_start=int(mapping["block_start"]),
            block_end=int(mapping["block_end"]),
            country=mapping["country"],
        )

    def to_dict(self):
        """Converts a Schedule instance to a dictionary"""
        return {
            "index": self.index,
            "instance": self.instance,
            "cycle_start": self.cycle_start,
            "cycle_end": self.cycle_end,
            "block_start": self.block_start,
            "block_end": self.block_end,
            "country": self.country,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Schedule):
            return NotImplemented

        for f in fields(self):
            if getattr(self, f.name) != getattr(other, f.name):
                return False
        return True
