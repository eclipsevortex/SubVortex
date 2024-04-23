from typing import List
from subnet.validator.models import Miner


def is_miner_suspicious(miner: Miner, suspicious_uids: List[int]):
    """
    True if the miner is in in the suspicious list, false otherwise
    """
    return next(
        (
            suspicious is not None
            for suspicious in suspicious_uids
            if suspicious.get("uid") == miner.uid
            and suspicious.get("hotkey") == miner.hotkey
        ),
        False,
    )
