from typing import List
from subnet.validator.models import Miner


def is_miner_suspicious(miner: Miner, suspicious_uids: List[int]):
    """
    True if the miner is in in the suspicious list, false otherwise
    the penalise factor will be returned too if there is one
    """
    return next(
        (
            (
                suspicious is not None,
                (suspicious.get("penalise_factor") if suspicious else None) or 0,
            )
            for suspicious in suspicious_uids
            if suspicious.get("uid") == miner.uid
            and suspicious.get("hotkey") == miner.hotkey
        ),
        (False, 0),
    )
