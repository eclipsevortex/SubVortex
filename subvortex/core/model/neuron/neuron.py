from typing import Optional
from dataclasses import dataclass, asdict

import bittensor.core.chain_data as btccd


@dataclass
class Neuron:
    uid: int = -1
    hotkey: str = ""
    coldkey: str = ""
    netuid: int = -1
    active: bool = False
    stake: float = 0.0
    total_stake: float = 0.0
    rank: float = 0.0
    emission: float = 0.0
    incentive: float = 0.0
    consensus: float = 0.0
    trust: float = 0.0
    validator_trust: float = 0.0
    dividends: float = 0.0
    last_update: int = 0
    validator_permit: bool = False
    ip: str = ""
    ip_type: int = 0
    port: int = 0
    version: int = 0
    protocol: int = 4
    placeholder1: int = 0
    placeholder2: int = 0
    is_serving: bool = False
    country: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert Neuron instance to a dict with consistent types."""
        data = asdict(self)
        data.update(
            {
                "active": int(self.active),
                "validator_permit": int(self.validator_permit),
                "is_serving": int(self.is_serving),
                "country": self.country or "",
            }
        )
        return data

    @staticmethod
    def from_dict(data: dict) -> "Neuron":
        """Create a Neuron instance from a dictionary."""
        return Neuron(
            uid=int(data["uid"]),
            hotkey=data["hotkey"],
            coldkey=data["coldkey"],
            netuid=int(data["netuid"]),
            active=bool(int(data["active"])),
            stake=float(data["stake"]),
            total_stake=float(data["total_stake"]),
            rank=float(data["rank"]),
            emission=float(data["emission"]),
            incentive=float(data["incentive"]),
            consensus=float(data["consensus"]),
            trust=float(data["trust"]),
            validator_trust=float(data["validator_trust"]),
            dividends=float(data["dividends"]),
            last_update=int(data["last_update"]),
            validator_permit=bool(int(data["validator_permit"])),
            ip=data["ip"],
            ip_type=int(data["ip_type"]),
            port=int(data["port"]),
            version=int(data["version"]),
            protocol=int(data["protocol"]),
            placeholder1=int(data["placeholder1"]),
            placeholder2=int(data["placeholder2"]),
            is_serving=bool(int(data["is_serving"])),
            country=data.get("country", "") or None,
        )

    @staticmethod
    def from_proto(neuron: btccd.NeuronInfo) -> "Neuron":
        """Create a Neuron instance from a cbc.NeuronInfo object."""
        return Neuron(
            uid=neuron.uid,
            hotkey=neuron.hotkey,
            coldkey=neuron.coldkey,
            netuid=neuron.netuid,
            active=neuron.active,
            stake=neuron.stake.tao,
            total_stake=neuron.total_stake.tao,
            rank=neuron.rank,
            emission=neuron.emission,
            incentive=neuron.incentive,
            consensus=neuron.consensus,
            trust=neuron.trust,
            validator_trust=neuron.validator_trust,
            dividends=neuron.dividends,
            last_update=neuron.last_update,
            validator_permit=neuron.validator_permit,
            ip=neuron.axon_info.ip,
            ip_type=neuron.axon_info.ip_type,
            protocol=neuron.axon_info.protocol,
            port=neuron.axon_info.port,
            version=neuron.axon_info.version,
            placeholder1=neuron.axon_info.placeholder1,
            placeholder2=neuron.axon_info.placeholder2,
            is_serving=neuron.axon_info.is_serving,
        )

    def update_from_proto(self, neuron) -> None:
        """Update this instance using a cbc.NeuronInfo object."""
        self.__dict__.update(Neuron.from_proto(neuron).__dict__)
