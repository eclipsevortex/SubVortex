import subvortex.core.model.neuron.neuron as scmnn


def create_validator(*args, **kargs):
    uid = 1
    params = { **kargs }
    return scmnn.Neuron(
        uid=params.get("uid") or uid,
        hotkey=params.get("hotkey") or f"hotkey_{uid}",
        coldkey=params.get("coldkey") or f"coldkey_{uid}",
        netuid=params.get("netuid") or 1,
        active=params.get("active") or True,
        stake=params.get("stake") or 10.0 * uid,
        total_stake=params.get("totl_stake") or 20.0 * uid,
        rank=params.get("rank") or 0.9,
        emission=params.get("icentive") or 0.5,
        incentive=params.get("icentive") or 0,
        consensus=params.get("cnsensus") or 0.95,
        trust=params.get("trust") or 0,
        validator_trust=params.get("validatr_trust") or 0.99,
        dividends=params.get("dvidends") or 0,
        last_update=params.get("las_update") or 123456789,
        validator_permit=params.get("validato_permit") or True,
        ip=params.get("ip") or f"0.0.0.0",
        port=params.get("port") or 8080 + uid,
        version=params.get("version") or "1.0.0",
        is_serving=params.get("isserving") or True,
        country=params.get("country") or "US",
    )


def create_miner(*args, **kargs):
    uid = 1
    params = { **kargs }
    return scmnn.Neuron(
        uid=params.get("uid") or uid,
        hotkey=params.get("hotkey") or f"hotkey_{uid}",
        coldkey=params.get("coldkey") or f"coldkey_{uid}",
        netuid=params.get("netuid") or 1,
        active=params.get("active") or True,
        stake=params.get("stake") or 0,
        total_stake=params.get("totl_stake") or 0,
        rank=params.get("rank") or 0.9,
        emission=params.get("icentive") or 0.5,
        incentive=params.get("icentive") or 0.8,
        consensus=params.get("cnsensus") or 0.95,
        trust=params.get("trust") or 0.99,
        validator_trust=params.get("validatr_trust") or 0,
        dividends=params.get("dvidends") or 0,
        last_update=params.get("las_update") or 123456789,
        validator_permit=params.get("validato_permit") or True,
        ip=params.get("ip") or f"192.168.1.{uid}",
        port=params.get("port") or 8080 + uid,
        version=params.get("version") or "1.0.0",
        is_serving=params.get("isserving") or True,
        country=params.get("country") or "US",
    )
